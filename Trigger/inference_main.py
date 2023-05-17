import os
import argparse
from utils import apk_util
from loguru import logger
from RLApplicationEnv import RLApplicationEnv
from utils.general_util import scan_file
from models.dqn import DQN
import config
from appium_helper import AppiumLauncher
import logging
logging.basicConfig(level=logging.ERROR)
import traceback
from utils.adbHelper import start_activity
import time
import random
import torch
import numpy as np
from utils.sys_util import restart_app,exception_process
from utils.exception_util import multi_times_ui_unchanged, running_in_other_app, terminate_and_restart_app
from utils.img_sim_hash import img_hash_distance
from utils.adbHelper import force_stop,clear

seed = 1234
random.seed(seed)
np.random.seed(seed)
torch.cuda.manual_seed(seed)
torch.manual_seed(seed)
torch.backends.cudnn.deterministic=True

def main():
    parser = argparse.ArgumentParser(description='sensitive api monitoring demo')
    parser.add_argument('--iterations', type=int, default=500)
    parser.add_argument('--episods', type=int, default=1)
    parser.add_argument('--algo', choices=['SAC', 'random', 'Q'], type=str, default='Q')
    parser.add_argument('--appium_port', type=int, default='4723')
    parser.add_argument('--platform_name', choices=['Android', 'iOS'], type=str, default='Android')
    parser.add_argument('--platform_version', type=str, default='7')
    parser.add_argument('--udid', type=str, default='emulator-5554')
    parser.add_argument('--device_name', type=str, default='Xiaomi10')
    parser.add_argument('--android_port', type=str, default='5554')
    parser.add_argument('--apps', type=str, default='apps')
    parser.add_argument('--layout_model', type=str, default='pretrainedModel/layout_encoder.ep800')
    parser.add_argument('--memory_capacity', type=int, default=4)
    args = parser.parse_args()

    N = args.iterations
    episods = args.episods
    algo = args.algo
    appium_port = args.appium_port
    memory_capacity = args.memory_capacity
    apks = scan_file(args.apps)

    appium = AppiumLauncher(appium_port)
    dqn = DQN()
    dqn.load_state_dict(torch.load('saved/net_parameter.pkl'))
    try:
        for application in apks:
            app_name = os.path.basename(os.path.splitext(application)[0])
            coverage_dict_template = {}
            appPackage,appActivity,appPermissions = apk_util.parse_pkg(application,coverage_dict_template)
            app = RLApplicationEnv(params=args, appPackage=appPackage, appActivity=appActivity,application=application,allActivities = coverage_dict_template.keys())
            for episod in range(episods):
                cycle = 0
                change_flag = 0
                while cycle < N:
                    cycle += 1
                    logger.info(f'app: {app_name}, test {cycle} of {N} starting')
                    log_dir = os.path.join(os.getcwd(), 'logs', app_name, algo, str(cycle))
                    os.makedirs(log_dir, exist_ok=True)
                    change_flag = multi_times_ui_unchanged(change_flag, app, appPackage, appActivity)
                    if running_in_other_app(app, appPackage, appActivity):
                        continue
                    current_state, action, index, operatable_widget, common = dqn.choose_action(app)
                    if current_state is None and action is None and index is None and operatable_widget is None:
                        terminate_and_restart_app(app, appPackage, appActivity)
                        continue
                    if operatable_widget.visitCount >= 900000:
                        continue
                    if operatable_widget.visitCount > operatable_widget.maxVisitCount:
                        operatable_widget.visitCount = 100000
                        logger.info('Achieving maximum visit count or the widget cannot be clicked, visit Count '+str(operatable_widget.visitCount))
                    next_state,reward,done,info = app.step(operatable_widget,common)
                    logger.info('operatable widget visit count is '+str(operatable_widget.visitCount))
                    if next_state is None and reward is None and done is None:
                        if info == -2:
                            change_flag += 1
                            continue
                        restart_app(app, appPackage, appActivity)
                        continue
                    if operatable_widget.visitCount >= 100000:
                        print('cannot change ',operatable_widget.bounds)
                        continue
                    dqn.store_transition(current_state,action,next_state,reward)
                    if len(dqn.memory)>=memory_capacity:
                        dqn.learn()
                print(app.GUI_dict.keys())
                print(coverage_dict_template.keys())
                coverage_rate = len(app.GUI_dict.keys()) / len(coverage_dict_template.keys())
                logger.info('Activity coverage rate is '+str(coverage_rate))
            while app.driver.query_app_state(appPackage)!=1:
                force_stop(appPackage)
            config.thread_life = False
            app.driver.quit()
            print('App finished')
    except Exception as e:
        print('Catch Expection，', traceback.print_exc(), 'Error Info', e)
    finally:
        appium.terminate()
    return 0

if __name__ == '__main__':
    main()
