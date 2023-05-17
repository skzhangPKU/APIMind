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

seed = 1234
random.seed(seed)
np.random.seed(seed)
torch.cuda.manual_seed_all(seed)
torch.manual_seed(seed)

def check_learning_time(app):
    current_time = datetime.now()
    if config.TIMER is not None:
        senc = (current_time - config.TIMER).seconds
        if senc > config.duration and app.monitoring_thread.is_alive():
            try:
                config.thread_life = False
                print('time limited!!!')
                stop_thread(app.monitoring_thread)
            except:
                pass

def common_ops(appPackage,app_name):
    gc.collect()
    config.thread_life = True
    config.TIMER = None
    force_stop(appPackage)

def main():
    parser = argparse.ArgumentParser(description='sensitive api monitoring demo')
    parser.add_argument('--iterations', type=int, default=600)
    parser.add_argument('--episods', type=int, default=20)
    parser.add_argument('--algo', choices=['SAC', 'random', 'Q'], type=str, default='Q')
    parser.add_argument('--platform_name', choices=['Android', 'iOS'], type=str, default='Android')
    parser.add_argument('--platform_version', type=str, default='12')
    # parser.add_argument('--udid', type=str, default='emulator-5554')
    parser.add_argument('--udid', type=str, default='08221FDD4005ET')
    parser.add_argument('--device_name', type=str, default='Pixel5')
    parser.add_argument('--android_port', type=str, default='5554')
    parser.add_argument('--apps', type=str, default='apps_unexplore')
    parser.add_argument('--layout_model', type=str, default='pretrainedModel/layout_encoder.ep800')
    parser.add_argument('--memory_capacity', type=int, default=32)
    args = parser.parse_args()

    N = args.iterations
    episods = args.episods
    algo = args.algo
    memory_capacity = args.memory_capacity
    apks = scan_file(args.apps)

    dqn = DQN()
    api_coverage_dicts = {}
    driver = u2.connect(args.udid)
    flag_con = True
    try:
        for i,application in enumerate(apks):
            if not application.endswith(".apk"):
                continue
            # if flag_con and application != 'apps_unexplore\\360省电王_7.3.3_Apkpure.apk':
            #     continue
            # else:
            #     flag_con = False
            while not get_wifi_state(driver):
                restart_wifi(driver)
                time.sleep(3)
                print('connect wifi automatically')
            dqn.tmp_memory.clear()
            # part 1
            if i > 0:
                print(apks[i-1])
                appPackageClose, appActivityClose, appPermissionsClose = apk_util.parse_pkg(apks[i-1], {})
                print(appPackageClose)
                force_stop(appPackageClose)
                with suppress_stdout_stderr():
                    driver.shell("pm clear %s" % appPackageClose)
                uninstallApp(appPackageClose)
            # part 2
            if (i+1) % 20 == 0:
                torch.save(dqn.state_dict(), 'saved/net_parameter_'+str(i+1)+'.pkl')
                print('saved parameters ',application)
            config.TIMER = datetime.now()
            config.thread_life = True
            print('current apps ',application)
            app_name = os.path.basename(os.path.splitext(application)[0])
            coverage_dict_template = {}
            appPackage,appActivity,appPermissions = apk_util.parse_pkg(application,coverage_dict_template)
            try:
                with suppress_stdout_stderr():
                    clear(appPackage)
                app = RLApplicationEnv(driver=driver,params=args, appPackage=appPackage, appActivity=appActivity, application=application, bert = dqn.bert,layout_autoencoder=dqn.layout_autoencoder,vtr=dqn.vtr, allActivities = coverage_dict_template.keys())
                if 'app' in locals().keys() and app is not None:
                    if not app.monitoring_thread.is_alive():
                        common_ops(appPackage, app_name)
                        with open('apiTrigger/' + app_name + '_api_trigger.pkl', 'wb') as f:
                            pickle.dump(app.all_sensitive_api_list, f)
                        if application != apks[-1]:
                            del app
                            app = None
                        print('App monitoring skip this app: ', application)
                        continue
            except:
                print('Env failure skip this app: ', application)
                if 'app' in locals().keys() and app is not None:
                    with open('apiTrigger/' + app_name + '_api_trigger.pkl', 'wb') as f:
                        pickle.dump(app.all_sensitive_api_list, f)
                common_ops(appPackage, app_name)
                if application != apks[-1]:
                    app = None
                continue
            START_PAGE_FLAG = True
            pre_activity = app.driver.app_current().get('activity')
            for episod in range(episods):
                cycle = 0
                while cycle < N:
                    while not get_wifi_state(driver):
                        restart_wifi(driver)
                        time.sleep(3)
                        print('connect wifi automatically')
                    if not app.monitoring_thread.is_alive():
                        common_ops(appPackage, app_name)
                        if 'app' in locals().keys() and app is not None:
                            with open('apiTrigger/' + app_name + '_api_trigger.pkl', 'wb') as f:
                                pickle.dump(app.all_sensitive_api_list, f)
                        if application != apks[-1]:
                            del app
                        print('monitoring thread dead!!!')
                        break
                    cycle += 1
                    logger.info(f'app: {app_name}, test {cycle} of {N} starting')
                    check_learning_time(app)
                    log_dir = os.path.join(os.getcwd(), 'logs', app_name, algo, str(cycle))
                    os.makedirs(log_dir, exist_ok=True)
                    if START_PAGE_FLAG:
                        sens_api_name_list = app.checkSensitiveAPIs()
                        app.all_sensitive_api_list.extend(sens_api_name_list)
                        if len(sens_api_name_list) > 0:
                            os.makedirs('dumps/' + app.appPackage, exist_ok=True)
                            dir_time = datetime.now().strftime("%Y%m%d%H%M%S")
                            dir_time_path = 'dumps/' + app.appPackage + '/' + dir_time
                            os.makedirs(dir_time_path, exist_ok=True)
                            api_desc_list = []
                            for sens_api in sens_api_name_list:
                                api_desc = get_api_descriptions(sens_api)
                                api_desc_list.append(api_desc)
                            try:
                                with suppress_stdout_stderr():
                                    new_layout_file = app.driver.dump_hierarchy()
                                    new_gui = app.driver.screenshot(format='raw')
                            except:
                                print('uiautomator2 restart')
                                uninstallApp('com.github.uiautomator')
                                with suppress_stdout_stderr():
                                    new_layout_file = app.driver.dump_hierarchy()
                                    new_gui = app.driver.screenshot(format='raw')
                            save_gui_image(path=dir_time_path, img_dict={'new_gui': new_gui})
                            save_xml_file(path=dir_time_path,xml_dict={'new_xml': new_layout_file})
                            save_json_file(path=dir_time_path,json_dict={'api_description_list': api_desc_list, 'api_name_list': sens_api_name_list})
                    if episod == 0 and cycle <= 4:
                        logger.info('Special operations for initial GUI states')
                        agree_widget,type = parse_pages(app.observation[2][0])
                        if agree_widget is not None:
                            if type == False:
                                os.system('adb shell input tap %d %d' % (int(agree_widget[0]), int(agree_widget[1])))
                            elif len(app.observation[2][0]) < 8:
                                os.system('adb shell input swipe %d %d %d %d %d' % (950, int(agree_widget[1]), 100, int(agree_widget[1]), 1000))
                                os.system('adb shell input swipe %d %d %d %d %d' % (950, int(agree_widget[1]), 100, int(agree_widget[1]), 1000))
                                os.system('adb shell input swipe %d %d %d %d %d' % (950, int(agree_widget[1]), 100, int(agree_widget[1]), 1000))
                                os.system('adb shell input swipe %d %d %d %d %d' % (950, int(agree_widget[1]), 100, int(agree_widget[1]), 1000))
                            time.sleep(3)
                            app.driver.shell('service call statusbar 2')
                            app.refreshNewObservation()
                            continue
                    try:
                        current_state, action, operatable_widget = dqn.choose_action(app)
                    except:
                        START_PAGE_FLAG = restart_app(app, appPackage, appActivity)
                        continue
                    if operatable_widget is None:
                        exception_process(app, appPackage)
                        START_PAGE_FLAG = restart_app(app, appPackage, appActivity)
                        continue
                    if operatable_widget.shallow_visitCount > operatable_widget.maxVisitCount:
                        operatable_widget.shallow_visitCount = float('inf')
                        print('Achieving maximum visit count or the widget cannot be clicked')
                    try:
                        next_state,reward,done,info = app.step(operatable_widget)
                        START_PAGE_FLAG = False
                    except:
                        next_state, reward, done, info = None, None, None, None
                    if next_state is None and reward is None and done is None:
                        START_PAGE_FLAG = restart_app(app, appPackage, appActivity)
                        continue
                    if len(next_state[3][0]) == 0:
                        START_PAGE_FLAG = restart_app(app, appPackage, appActivity)
                        continue
                    dqn.store_transition(current_state,action,next_state,reward)
                    curr_activity = app.driver.app_current().get('activity')
                    if app.un_variable_num >= 5:
                        print('.......................trapped and restart.......................')
                        force_stop(appPackage)
                        time.sleep(5)
                        start_activity(appPackage + '/' + appActivity)
                        time.sleep(5)
                        app_refresh(app,appPackage,appActivity)
                        START_PAGE_FLAG = True
                        app.un_variable_num = 0
                        continue
                    if (i+1) % 20 == 0:
                        if len(dqn.memory) >= memory_capacity:
                            print('training all apps')
                            dqn.learn('allApp')
                    if len(dqn.tmp_memory) >= memory_capacity:
                        print('training current apps')
                        dqn.learn('currentApp')
                    coverage_rate = len(app.GUI_dict) / len(coverage_dict_template.keys())
                    logger.info('Activity coverage rate is ' + str(coverage_rate))
                if not 'app' in locals().keys():
                    print('episod: no apps in keys')
                    break
                print(app.GUI_dict)
                print(coverage_dict_template.keys())
                coverage_rate = len(app.GUI_dict) / len(coverage_dict_template.keys())
                logger.info('Activity coverage rate is '+str(coverage_rate))
            if not 'app' in locals().keys():
                print('application: no apps in keys and skip')
                continue
            print('====================all sensitive api list====================')
            print(app.all_sensitive_api_list)
            with open('apiTrigger/' + app_name + '_api_trigger.pkl', 'wb') as f:
                pickle.dump(app.all_sensitive_api_list, f)
            current_apps = app.driver.app_list_running()
            while appPackage in current_apps:
                force_stop(appPackage)
                current_apps = app.driver.app_list_running()
            config.thread_life = False
            if app.monitoring_thread.is_alive():
                try:
                    stop_thread(app.monitoring_thread)
                    print('thread teminate')
                except:
                    pass
            print('App finished')
    except Exception as e:
        print('Capture Exception，', traceback.print_exc(), 'Error Info,', e)
    finally:
        config.thread_life = False
    torch.save(dqn.state_dict(), 'saved/net_parameter_final.pkl')
    with open('saved/all_memory.pkl', 'wb') as f:
        pickle.dump(dqn.memory, f)
    return 0

if __name__ == '__main__':
    main()
