from utils.sys_util import restart_app, exception_process
from loguru import logger

def multi_times_ui_unchanged(change_flag, app, appPackage, appActivity):
    if change_flag > 4:
        e_flag = exception_process(app, appPackage)
        if e_flag:
            change_flag = 0
        restart_app(app, appPackage, appActivity)
    return change_flag

def running_in_other_app(app, appPackage, appActivity):
    if app.driver.app_current().get('package') != appPackage:
        terminate_and_restart_app(app, appPackage, appActivity)
        return True
    return False

def terminate_and_restart_app(app, appPackage, appActivity):
    logger.info('Terminate app if UI remains unchanged and then restart app.')
    exception_process(app, appPackage)
    restart_app(app, appPackage, appActivity)

