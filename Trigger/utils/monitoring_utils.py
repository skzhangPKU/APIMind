from loguru import logger
from monitoring.adb import ADB
from androguard.core.bytecodes.apk import APK
import time
import os
from utils.adbHelper import start_activity,clear,checkPackageInstall,call_adb
from utils.suppress_stdout import suppress_stdout_stderr

def push_and_start_frida_server(adb: ADB):
    frida_server = os.path.join(
        os.path.abspath(os.path.join(os.getcwd(), '.')), "resources", "frida-server", "frida-server"
    )
    # frida_server = os.path.join(
    #     os.path.abspath(os.path.join(os.getcwd(),'.')), "resources", "frida-server-emulator", "frida-server"
    # )
    try:
        adb.execute(["root"])
    except Exception as e:
        adb.kill_server()
        logger.error("Error on adb {}".format(e))

    logger.info("Push frida server")
    try:
        adb.push_file(frida_server, "/data/local/tmp")
    except Exception as e:
        pass
    logger.info("Add execution permission to frida-server")
    chmod_frida = ["chmod 755 /data/local/tmp/frida-server"]
    adb.shell(chmod_frida)
    logger.info("Start frida server")
    start_frida = ["su -c /data/local/tmp/frida-server &"]
    check_close_frida(adb)
    adb.shell(start_frida, is_async=True)
    time.sleep(4)

def check_close_frida(adb):
    check_frida = ["ps | grep frida | head -1 | awk '{print($2)}'"]
    res = adb.shell(check_frida)
    if res and 'Broken' not in str(res):
        # kill_frida = ["kill -9 " + str(res)]
        kill_frida = ["su -c kill -9 " + str(res)]
        adb.shell(kill_frida)

def install_app_and_install_frida(app_path,pkName,activityName):
    app = APK(app_path)
    package_name = app.get_package()
    logger.info("Start ADB")
    adb = ADB()
    logger.info("Install APP")
    try:
        if not checkPackageInstall(pkName):
            with suppress_stdout_stderr():
                os.system('adb install -r ' + app_path)
    except:
        pass
    logger.info(app_path)
    logger.info("Frida Initialize")
    check_close_frida(adb)
    push_and_start_frida_server(adb)
    return package_name


def create_script_frida(list_api_to_monitoring: list, path_frida_script_template: str):
    with open(path_frida_script_template) as frida_script_file:
        script_frida_template = frida_script_file.read()

    script_frida = ""
    for tuple_class_method in list_api_to_monitoring:
        script_frida += (
            script_frida_template.replace(
                "class_name", '"' + tuple_class_method[0] + '"'
            ).replace("method_name", '"' + tuple_class_method[1] + '"')
            + "\n\n"
        )
    return script_frida


def create_list_api_from_file(list_file_api_to_monitoring):
    list_api_to_monitoring_complete = list()
    for file_api_to_monitoring in list_file_api_to_monitoring:
        list_api_to_monitoring = read_api_to_monitoring(file_api_to_monitoring)
        list_api_to_monitoring_complete.extend(list_api_to_monitoring)
    return list_api_to_monitoring_complete


def create_adb_and_start_frida(package_name):
    logger.info(f"App Already Installed, start to monitoring ${package_name}")
    adb = ADB()
    logger.info("Frida Initialize")
    push_and_start_frida_server(adb)
    return package_name


def create_json_custom(list_api_to_monitoring):
    dict_category_custom = {"Category": "Custom", "HookType": "Java", "hooks": []}

    for api in list_api_to_monitoring:
        dict_method = {"clazz": api[0], "method": api[1]}
        dict_category_custom["hooks"].append(dict_method)

    return dict_category_custom


def read_api_to_monitoring(file_api_to_monitoring):
    if os.path.exists(file_api_to_monitoring):
        list_api_to_monitoring = []
        content = []
        with open(file_api_to_monitoring) as file_api:
            content = file_api.readlines()
        content = [x.strip() for x in content]
        for class_method in content:
            list_api_to_monitoring.append(
                (class_method.split(",")[0], class_method.split(",")[1])
            )
        return list_api_to_monitoring
    else:
        return None
