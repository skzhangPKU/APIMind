from utils.general_util import scan_file
from utils.adbHelper import clear,checkPackageInstall
from utils import apk_util
import logging
logging.basicConfig(level=logging.ERROR)
import os

def install_app(pkName):
    apks = scan_file('/home/andrew/workspace/GUIFuzzing/API_flow_EX_uiautomator2/apps')
    for i, application in enumerate(apks):
        appPackageClose, appActivityClose, appPermissionsClose = apk_util.parse_pkg(application, {})
        if appPackageClose != pkName:
            continue
        if not checkPackageInstall(appPackageClose):
            clear(appPackageClose)
            os.system('adb install -r ' + application)
            break

if __name__ == '__main__':
    pkName = 'air.tv.douyu.android'
    clear(pkName)
    # install_app(pkName)
    # os.system('abd uninstall '+pkName)