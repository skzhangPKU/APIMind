import frida
import json
from datetime import datetime
import argparse
from rich import print
from rich.console import Console
from loguru import logger
import json
from utils.monitoring_utils import *
from argparse import Namespace
import config

console = Console()
default_js_dir = os.path.abspath(os.path.join(os.getcwd(),'.'))


def on_message(message, data):
    if message["type"] == "send":
        if type(message["payload"]) is str:
            if "API Monitor" not in message["payload"]:
                message_dict = json.loads(message["payload"])
                api_name = message_dict['class']+'.'+message_dict['method']
                config.api_trigged_list.add(api_name)
                current_time = datetime.now()
                if config.TIMER is not None:
                    senc = (current_time-config.TIMER).seconds
                    if senc > config.duration:
                        config.thread_life = False
            else:
                return
        else:
            message_dict = message["payload"]
        if "Error" not in str(message_dict):
            try:
                message_dict = json.loads(message["payload"])
                api_name = message_dict['class'] + '.' + message_dict['method']
                config.api_trigged_list.add(api_name)
            except json.decoder.JSONDecodeError as e:
                    pass


def main_v2(
    app_path,
    list_api_to_monitoring=None,
    app_to_install=True,
    store_script=False,
    category=["ALL"],
):
    if not app_to_install:
        package_name = app_path

    pid = None
    device = None
    session = None

    try:
        device = frida.get_usb_device(timeout=10)
        pid = device.spawn([package_name])
        session = device.attach(pid)
    except Exception as e:
        logger.error("Error {}".format(e))
        device = frida.get_usb_device()
        pid = device.spawn([package_name])
        session = device.attach(pid)
    logger.info("Succesfully attacched frida to app")
    try:
        with open(os.path.join(default_js_dir, "api_android_monitor", "default.js")) as f:
            frida_code = f.read()
        script = session.create_script(frida_code)
        script.on("message", on_message)
        script.load()
        device.resume(pid)
        api = script.exports
        time.sleep(3)
        api_monitor = []
        if list_api_to_monitoring is not None:
            json_custom = create_json_custom(list_api_to_monitoring)
            api_monitor.append(json_custom)
            category.append("Custom")
        api.apimonitor(api_monitor)
    except:
        logger.error("Error!!! Papi Frida API Monitoring Failure")
        config.thread_life = False
        pass

    while True:
        if not config.thread_life:
            break

def start_monitoring(package_name):
    logger.info('Thread start')
    arguments = Namespace(api=None, file_apk=None, filter=['NONE'], list_api=['permissions_api.txt'],
                          package_name=package_name, store_script=False, version='2')
    logger.info("Start Frida API Monitoring without App Installation")
    package_name = arguments.package_name
    list_file_api_to_monitoring = arguments.list_api
    list_api_to_monitoring = create_list_api_from_file(
        list_file_api_to_monitoring
    )
    main_v2(
        package_name,
        list_api_to_monitoring,
        app_to_install=False,
        store_script=arguments.store_script,
        category=arguments.filter,
    )

def start_monitoring_with_install(file_apk):
    print('Thread start')
    arguments = Namespace(api=None, file_apk=file_apk, filter=['NONE'], list_api=['permissions_api.txt'],
                          store_script=False, version='2')
    if arguments.file_apk is not None:
        app_path = arguments.file_apk
        if os.path.exists(app_path):
            logger.info("Start Frida API Monitoring with App Installation")
            if arguments.list_api is not None:
                list_file_api_to_monitoring = arguments.list_api
                list_api_to_monitoring = create_list_api_from_file(
                    list_file_api_to_monitoring
                )
                main_v2(
                    app_path,
                    list_api_to_monitoring,
                    app_to_install=True,
                    store_script=arguments.store_script,
                    category=arguments.filter,
                )

if __name__ == "__main__":
    start_monitoring('org.wikipedia.alpha')
