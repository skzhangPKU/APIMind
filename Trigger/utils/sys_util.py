import time
from utils.adbHelper import start_activity,force_stop
from utils.img_sim_hash import img_hash_distance
from loguru import logger
from utils.suppress_stdout import suppress_stdout_stderr
from utils.adbHelper import uninstallApp

def restart_app(app,appPackage,appActivity):
    flag = False
    current_apps = app.driver.app_list_running()
    running = appPackage in current_apps
    oth_package = app.driver.app_current().get('package')
    if running:
        if oth_package!=appPackage and oth_package != 'com.google.android.apps.nexuslauncher':
            force_stop(oth_package)
            if app.driver.app_current().get('package') != appPackage:
                start_activity(appPackage + '/' + appActivity)
                time.sleep(5)
                flag = True
    else:
        if oth_package == 'com.google.android.apps.nexuslauncher':
            start_activity(appPackage + '/' + appActivity)
            time.sleep(5)
            flag = True
        else:
            force_stop(oth_package)
            if app.driver.app_current().get('package') != appPackage:
                start_activity(appPackage + '/' + appActivity)
                time.sleep(5)
                flag = True
    flag_fresh = app_refresh(app,appPackage,appActivity)
    if flag_fresh:
        return True
    else:
        return flag

def app_refresh(app,appPackage,appActivity):
    flag = False
    while True:
        try:
            app.refreshNewObservation()
            break
        except:
            logger.info('appium driver dump page source failure')
            force_stop(appPackage)
            start_activity(appPackage + '/' + appActivity)
            time.sleep(5)
            flag = True
    return flag

def exception_process(app,appPackage):
    try:
        with suppress_stdout_stderr():
            old_gui = app.driver.screenshot(format='raw')
    except:
        uninstallApp('com.github.uiautomator')
        with suppress_stdout_stderr():
            old_gui = app.driver.screenshot(format='raw')
    app.driver.press("back")
    time.sleep(2)
    try:
        with suppress_stdout_stderr():
            new_gui = app.driver.screenshot(format='raw')
    except:
        uninstallApp('com.github.uiautomator')
        with suppress_stdout_stderr():
            new_gui = app.driver.screenshot(format='raw')
    distance = img_hash_distance(old_gui, new_gui)
    if distance < 2:
        force_stop(appPackage)
        return False
    return True