from PIL import Image
from io import BytesIO
import numpy as np
from utils.screen_util import toimage
import cv2

class Widget:
    def __init__(self, text, text_class, bounds, operatable, widget_udid, current_screen):
        self.text = text
        self.text_class = text_class
        self.bounds = bounds
        self.operatable = operatable
        self.widget_udid = widget_udid
        self.screen = self.crop_screen(current_screen)
        self.nextGUI = None
        self.visitCount = 0
        self.shallow_visitCount = 0
        self.GUITrans = False
        self.maxVisitCount = 2
        self.nextGUIWidgetSet = set()
        self.sensitive_apis_trigged = []
        self.sensitive_apis_trigged_num = 0

    def crop_screen(self,current_screen):
        np_screen = cv2.imdecode(np.frombuffer(current_screen, np.uint8), cv2.IMREAD_COLOR)
        screen_crop2 = np_screen[int(self.bounds[1]):int(self.bounds[3]),int(self.bounds[0]):int(self.bounds[2])]
        temp2 = cv2.imencode('.png', screen_crop2)[1].tostring()
        return temp2

    def add_visit_count(self):
        self.visitCount += 1
        self.shallow_visitCount += 1

    def update_next_GUI(self, nextGUI):
        self.nextGUI = nextGUI

    def add_trigged_api(self,sens_api_name_list):
        for sens_api_name in sens_api_name_list:
            if sens_api_name not in self.sensitive_apis_trigged:
                self.sensitive_apis_trigged.append(sens_api_name)
                self.sensitive_apis_trigged_num += 1
