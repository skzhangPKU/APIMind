import re
import os
import numpy as np
import time
from multiprocessing import Process, Queue
import random
from xml.etree import ElementTree as ET
from utils.widget_util import parse_widgets
from utils.screen_util import get_screen,get_screen_rgb
from entity_dao.widget import Widget
from entity_dao.GUI import GUI
import torch
from models.autoencoder import ScreenLayout
import imgsim
from sentence_transformers import SentenceTransformer
from models.widget_embed import WidgetEmbed
from models.autoencoder import LayoutAutoEncoder
from monitoring import papi_monitor
from threading import Thread
from utils.adbHelper import checkIfInstalled,dump_layout,get_current_activity,screencap
from utils.monitoring_utils import install_app_and_install_frida
import uiautomator2 as u2
import config
from loguru import logger
from utils.widget_util import generate_udid_str
import uuid
import datetime
from utils.img_sim_hash import img_hash_distance
import traceback
from utils.adbHelper import force_stop,clear,start_activity
from utils.screen_util import image_match,get_class_list
import Levenshtein
from consist.layout_dependency import consist_layout_context
from consist.visual_dependency import consist_visual_context_by_clipsim
from consist.consist_input import get_layout_inputs
from consist.self_dependency import consist_self_dependency
from consist.api_descriptions import get_api_descriptions
from sklearn.metrics.pairwise import cosine_similarity
from similarities import ClipSimilarity
from consist.similarity_score import calculate_combined_score
from utils.screen_util import save_gui_image,save_json_file,save_xml_file
from utils.thread_kill import stop_thread
from utils.adbHelper import checkPackageInstall,dump_layout
from utils.suppress_stdout import suppress_stdout_stderr
from utils.adbHelper import uninstallApp

class RLApplicationEnv():

    def __init__(self,driver,params,appPackage,appActivity,application,bert,layout_autoencoder,vtr,allActivities):
        self.driver = driver
        self.udid = params.udid
        self.layout_model = params.layout_model
        self.appPackage = appPackage
        self.appActivity = appActivity
        self.allActivities = allActivities
        self.timesteps = 0
        self.app_description = None
        self.bert = bert
        self.layout_autoencoder = layout_autoencoder
        self.vtr = vtr
        install_app_and_install_frida(application,appPackage,appActivity)
        if not checkPackageInstall(appPackage):
            raise
        self.grant_permissions()
        self.monitoring_thread = Thread(target=papi_monitor.start_monitoring, args=(self.appPackage,))
        self.monitoring_thread.start()
        time.sleep(8)
        start_activity(appPackage + '/' + appActivity)
        self.old_activity = None
        self.executed_widget = None
        self.GUI_dict = set()
        self.all_widget_dict = {}
        self.all_sensitive_api_list = []
        logger.info('Pretrained model loaded')
        time.sleep(8)
        if self.driver.app_current().get('package')!=appPackage:
            raise
        if self.driver._get_orientation()!=0:
            raise
        self.refreshNewObservation()
        self.un_variable_num = 0

    def loadPretrainedModel(self,bert):
        self.layout_autoencoder = LayoutAutoEncoder()
        self.layout_autoencoder.load_state_dict(torch.load(self.layout_model))
        self.vtr = imgsim.Vectorizer(device='cuda')
        self.bert = bert
        self.clip_sim = ClipSimilarity()

    def grant_permissions(self):
        permissions = ['android.permission.ACCESS_WIFI_STATE', 'android.permission.BLUETOOTH', \
                       'android.permission.ACCESS_FINE_LOCATION', 'android.permission.CAMERA',
                       'android.permission.READ_CALENDAR', \
                       'android.permission.READ_CONTACTS', 'android.permission.READ_EXTERNAL_STORAGE',
                       'android.permission.READ_PHONE_STATE', \
                       'android.permission.GET_TASKS', 'android.permission.WRITE_CALENDAR',
                       'android.permission.WRITE_CONTACTS', \
                       'android.permission.ACCESS_COARSE_LOCATION', 'android.permission.WRITE_EXTERNAL_STORAGE',
                       'android.permission.RECORD_AUDIO', \
                       'android.permission.READ_SMS', 'android.permission.RECEIVE_SMS']
        for permission in permissions:
            self.driver.shell('pm grant %s %s' % (self.appPackage, permission))

    def refreshNewObservation(self):
        try:
            with suppress_stdout_stderr():
                page_source = self.driver.dump_hierarchy()
                current_screen = self.driver.screenshot(format='raw')
        except:
            uninstallApp('com.github.uiautomator')
            with suppress_stdout_stderr():
                page_source = self.driver.dump_hierarchy()
                current_screen = self.driver.screenshot(format='raw')
            print('uiautomator2 restart')
        self.current_activity = self.driver.app_current().get('activity')
        self.GUI_dict.add(self.current_activity)
        self.layout_feature = self.get_layout_feature(page_source)
        self.visual_feature = self.get_visual_feature(current_screen)
        xmlRoot = ET.fromstring(page_source)
        labeled_text = parse_widgets(xmlRoot, False, False, testing=False)
        self.usable_widgets = []
        widget_texts = []
        widget_visit_counts = []
        widget_shallow_visit_counts = []
        self.next_widgets = []
        for key_, item in enumerate(labeled_text):
            if item[3] == 1 or item[3] == 2:
                udid_str = generate_udid_str(self.current_activity,item)
                widget_udid  = uuid.uuid3(uuid.NAMESPACE_DNS, udid_str)
                if str(widget_udid) not in self.all_widget_dict:
                    self.all_widget_dict[str(widget_udid)] = Widget(item[0], item[1], item[2], item[3], widget_udid, current_screen)
                    self.next_widgets.append(str(widget_udid))
                poten_operatable_widget = self.all_widget_dict[str(widget_udid)]
                self.usable_widgets.append(str(widget_udid))
                widget_visit_counts.append(poten_operatable_widget.visitCount)
                widget_shallow_visit_counts.append(poten_operatable_widget.shallow_visitCount)
                item[2] = [item[2][0]/config.Device_resolution_x, item[2][1]/config.Device_resolution_y, item[2][2]/config.Device_resolution_x, item[2][3]/config.Device_resolution_y]
                widget_texts.append(item)
        if self.executed_widget is not None:
            self.executed_widget.nextGUIWidgetSet.update(self.usable_widgets)
            self.executed_widget.maxVisitCount = len(self.executed_widget.nextGUIWidgetSet)
        self.current_mask = [0] * 100
        self.observation = [self.visual_feature, self.layout_feature, [widget_texts],[widget_visit_counts],[widget_shallow_visit_counts]]

    def get_visual_feature(self,screen_shot):
        screen = get_screen(param=screen_shot,flag='bytes_io')
        with torch.no_grad():
            visual_feature = self.vtr.my_model(screen)
        return visual_feature

    def get_layout_feature(self,page_source):
        layout_embedder = self.layout_autoencoder.enc
        screen_to_add = ScreenLayout(page_source)
        screen_pixels = screen_to_add.pixels.flatten()
        encoded_layout = layout_embedder(torch.as_tensor(screen_pixels, dtype=torch.float).unsqueeze(0))
        return encoded_layout

    def checkSensitiveAPIs(self):
        sense_api_trigged_list = list(config.api_trigged_list)
        config.api_trigged_list = set()
        print('Sensitive aps trigged times ',str(len(sense_api_trigged_list)),sense_api_trigged_list)
        return sense_api_trigged_list

    def checkAppStatus(self):
        tmpCurrentActivity = self.driver.app_current().get('activity')
        if tmpCurrentActivity in self.allActivities or self.appPackage+str(tmpCurrentActivity) in self.allActivities:
            return 1
        else:
            return -1

    def step(self, operatable_widget):
        self.timesteps += 1
        operatable_widget.add_visit_count()
        reward_part1 = 2 / operatable_widget.shallow_visitCount
        try:
            with suppress_stdout_stderr():
                layout_file = self.driver.dump_hierarchy()
                old_gui = self.driver.screenshot(format='raw')
        except:
            uninstallApp('com.github.uiautomator')
            with suppress_stdout_stderr():
                layout_file = self.driver.dump_hierarchy()
                old_gui = self.driver.screenshot(format='raw')
            print('uiautomator2 restart')
        old_xml_layout_class_list = get_class_list(layout_file)
        layout_params = get_layout_inputs(operatable_widget, self.current_activity, layout_file)
        consistence_context_resource_str,consistence_view_dependency_str = consist_layout_context(*layout_params)
        self.perform_touch_action(operatable_widget)
        self.driver.shell('service call statusbar 2')
        try:
            with suppress_stdout_stderr():
                new_layout_file = self.driver.dump_hierarchy()
                new_gui = self.driver.screenshot(format='raw')
        except:
            uninstallApp('com.github.uiautomator')
            try:
                with suppress_stdout_stderr():
                    new_layout_file = self.driver.dump_hierarchy()
                    new_gui = self.driver.screenshot(format='raw')
                print('uiautomator2 restart')
            except:
                print('appium driver dump page source failure1')
                return None, None, None, None
        new_xml_layout_class_list = get_class_list(new_layout_file)
        xml_score = Levenshtein.seqratio(old_xml_layout_class_list, new_xml_layout_class_list)
        old_gui_vector = self.get_visual_feature(old_gui)
        new_gui_vector = self.get_visual_feature(new_gui)
        distance = np.linalg.norm(old_gui_vector.cpu().numpy() - new_gui_vector.cpu().numpy())
        if xml_score > 0.95:
            self.un_variable_num += 1
            if distance < 2:
                operatable_widget.maxVisitCount = 1
            else:
                operatable_widget.maxVisitCount = 2
        else:
            self.un_variable_num = 0
        if self.checkAppStatus() == -1:
            print('app status = -1')
            self.executed_widget = None
            return None,None,None,None
        sens_api_name_list = self.checkSensitiveAPIs()
        self.all_sensitive_api_list.extend(sens_api_name_list)
        operatable_widget.add_trigged_api(sens_api_name_list)
        if len(sens_api_name_list) > 0:
            os.makedirs('dumps/' + self.appPackage, exist_ok=True)
            dir_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            dir_time_path = 'dumps/' + self.appPackage + '/' + dir_time
            os.makedirs(dir_time_path, exist_ok=True)
            api_desc_list = []
            for sens_api in sens_api_name_list:
                api_desc = get_api_descriptions(sens_api)
                api_desc_list.append(api_desc)
            save_gui_image(path = dir_time_path, img_dict={'old_gui':old_gui,'new_gui':new_gui})
            save_xml_file(path = dir_time_path, xml_dict={'old_xml':layout_file,'new_xml':new_layout_file})
            save_json_file(path = dir_time_path, json_dict={'api_description_list':api_desc_list,'api_name_list':sens_api_name_list,'widget_context_dependency':consistence_context_resource_str,
                                                            'widget_self_dependency':consistence_view_dependency_str,'op_widget_text':operatable_widget.text,'op_widget_udid':str(operatable_widget.widget_udid),
                                                            'op_widget_bounds':str(operatable_widget.bounds)})
        api_level_reward = len(sens_api_name_list)
        self.executed_widget = operatable_widget
        pre_usable_widgets = self.usable_widgets
        try:
            self.refreshNewObservation()
        except:
            print('appium driver dump page source failure1')
            return None, None, None, None
        reward_part2 = self.compute_reward()/5
        if distance < 2:
            reward_part3 = 0
        else:
            reward_part3 = 1
        widget_level_reward = reward_part1 + reward_part2
        activity_level_reward = reward_part3
        reward = np.float32(50 * api_level_reward + 2 * activity_level_reward + widget_level_reward )
        print(50 * api_level_reward, 2 * activity_level_reward, widget_level_reward)
        done = self._termination()
        return self.observation, reward, done, {}

    def perform_touch_action(self,operatable_widget):
        try:
            pixel_bounds = operatable_widget.bounds
            if operatable_widget.operatable == 1:
                x = (pixel_bounds[0] + pixel_bounds[2])/2
                y = (pixel_bounds[1] + pixel_bounds[3])/2
                os.system('adb shell input tap %d %d' % (int(x), int(y)))
                print('Touching Action at coordinates %d %d' % (int(x), int(y)))
            elif operatable_widget.operatable == 2:
                x = (pixel_bounds[0] + pixel_bounds[2]) / 2
                if int(pixel_bounds[3])-200 > 0:
                    os.system('adb shell input swipe %d %d %d %d %d' % (int(x), int(pixel_bounds[3]) - 100, int(x), int(pixel_bounds[3])-200, 500))
                else:
                    os.system('adb shell input swipe %d %d %d %d %d' % (int(x), int(pixel_bounds[3]), int(x), int(pixel_bounds[1]), 500))
                print('Performing scroll events %d %d %d %d' % (int(x), int(pixel_bounds[3]), int(x), int(pixel_bounds[1])))
        except Exception as e:
            print(e)

    def compute_reward(self):
        unvisited_widgets_num = 0
        if self.executed_widget is not None:
            if len(self.next_widgets) == 0:
                return 0
            unvisited_widgets_num = len(self.next_widgets)
        reward_unvisit = np.clip(unvisited_widgets_num,0,20,dtype=np.float32)
        return reward_unvisit

    def _termination(self):
        return False

    def reset(self):
        self.timesteps = 0
        try:
            self.driver.reset()
        except Exception as e:
            pass
        self.get_observation()
        return self.observation

    def clear(self):
        self.old_activity = None
        self.executed_widget = None
        self.GUI_dict = {}
        self.current_activity = None
        self.currentGUI = None
        self.observation = None