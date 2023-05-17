import os
import argparse
from utils import apk_util
from loguru import logger
from RLApplicationEnv import RLApplicationEnv
from utils.general_util import scan_file
from models.dqn import DQN
import config
import logging
logging.basicConfig(level=logging.ERROR)
import traceback
from utils.adbHelper import start_activity
import time
import random
import torch
import numpy as np
from utils.sys_util import restart_app,exception_process,app_refresh
from utils.img_sim_hash import img_hash_distance
from utils.adbHelper import force_stop,clear,uninstallApp
import subprocess
from consist.api_descriptions import get_api_descriptions
from utils.screen_util import save_gui_image,save_json_file,save_xml_file
from utils.thread_kill import stop_thread
from utils.suppress_stdout import suppress_stdout_stderr
import gc
import pickle
from datetime import datetime
import uiautomator2 as u2
from utils.wifi_util import get_wifi_state,restart_wifi
from utils.general_util import parse_pages
from utils.adbHelper import checkPackageInstall
from PIL import Image
from io import BytesIO
from xml.etree import ElementTree as ET
from utils.widget_util import parse_widgets

def get_observation(page_source):
    xmlRoot = ET.fromstring(page_source)
    labeled_text = parse_widgets(xmlRoot, False, False, testing=False)
    widget_texts = []
    for key_, item in enumerate(labeled_text):
        if item[3] == 1 or item[3] == 2:
            item[2] = [item[2][0] / config.Device_resolution_x, item[2][1] / config.Device_resolution_y, item[2][2] / config.Device_resolution_x, item[2][3] / config.Device_resolution_y]
            widget_texts.append(item)
    return widget_texts


def start_page_xml_image():
    apks = scan_file('apps')
    pk_name_path = scan_file('dumps')
    pk_name_list = [pk_name.replace('dumps/', '') for pk_name in pk_name_path]
    driver = u2.connect('08221FDD4005ET')
    for i, application in enumerate(apks):
        while not get_wifi_state(driver):
            restart_wifi(driver)
            time.sleep(3)
            print('connect wifi automatically')
        if i > 0:
            appPackageClose, appActivityClose, appPermissionsClose = apk_util.parse_pkg(apks[i - 1], {})
            force_stop(appPackageClose)
            with suppress_stdout_stderr():
                driver.shell("pm clear %s" % appPackageClose)
            uninstallApp(appPackageClose)
        coverage_dict_template = {}
        appPackage, appActivity, appPermissions = apk_util.parse_pkg(application, coverage_dict_template)
        if appPackage not in pk_name_list:
            continue
        print('currnet package ',appPackage)
        with suppress_stdout_stderr():
            clear(appPackage)
        if not checkPackageInstall(appPackage):
            with suppress_stdout_stderr():
                os.system('adb install -r ' + application)
        start_activity(appPackage + '/' + appActivity)
        time.sleep(8)
        try:
            with suppress_stdout_stderr():
                page_source = driver.dump_hierarchy()
                current_screen = driver.screenshot(format='raw')
        except:
            uninstallApp('com.github.uiautomator')
            with suppress_stdout_stderr():
                page_source = driver.dump_hierarchy()
                current_screen = driver.screenshot(format='raw')
            print('uiautomator2 restart')
        im = Image.open(BytesIO(current_screen))
        im.save('dumps/' + appPackage + '/start.png')
        im.close()
        with open('dumps/' + appPackage + '/start.xml','w') as f:
            f.writelines(page_source)
        print('image and xml file saved ',appPackage)
        observations = get_observation(page_source)
        agree_widget, type = parse_pages(observations)
        if agree_widget is not None:
            if type == False:
                os.system('adb shell input tap %d %d' % (int(agree_widget[0]), int(agree_widget[1])))
            elif len(observations) < 8:
                os.system('adb shell input swipe %d %d %d %d %d' % (
                950, int(agree_widget[1]), 100, int(agree_widget[1]), 1000))
                os.system('adb shell input swipe %d %d %d %d %d' % (
                950, int(agree_widget[1]), 100, int(agree_widget[1]), 1000))
                os.system('adb shell input swipe %d %d %d %d %d' % (
                950, int(agree_widget[1]), 100, int(agree_widget[1]), 1000))
                os.system('adb shell input swipe %d %d %d %d %d' % (
                950, int(agree_widget[1]), 100, int(agree_widget[1]), 1000))
            time.sleep(4)
        try:
            with suppress_stdout_stderr():
                page_source2 = driver.dump_hierarchy()
                current_screen2 = driver.screenshot(format='raw')
        except:
            uninstallApp('com.github.uiautomator')
            with suppress_stdout_stderr():
                page_source2 = driver.dump_hierarchy()
                current_screen2 = driver.screenshot(format='raw')
        im2 = Image.open(BytesIO(current_screen2))
        im2.save('dumps/' + appPackage + '/end.png')
        im2.close()
        with open('dumps/' + appPackage + '/end.xml','w') as f:
            f.writelines(page_source2)
        print('image and xml file saved end ',appPackage)


if __name__ == '__main__':
    start_page_xml_image()