from utils.widget_util import parse_widgets
from entity_dao.widget import Widget
import uuid
from utils.widget_util import generate_udid_str

class GUI:
    def __init__(self, xmlRoot,activity_name,driver):
        self.xmlRoot = xmlRoot
        self.activity_name = activity_name
        self.driver = driver
        self.initialWidgets()
        self.sensitive_apis_trigged = []
        self.sensitive_apis_trigged_num = 0
        self.unvisited_widgets_num = len(self.operatable_widgets)
        self.visited_widgets_list = []
        self.layout_feature = None
        self.child_GUI_widget_list = []

    def initialWidgets(self):
        self.labeled_text = parse_widgets(self.xmlRoot, False, False, testing=False)
        self.widget_dict = {}
        self.operatable_widgets = []
        self.display_widgets = []
        for key_, item in enumerate(self.labeled_text):
            udid_str = generate_udid_str(self.activity_name,item)
            widget_udid  = uuid.uuid3(uuid.NAMESPACE_DNS, udid_str)
            self.widget_dict[str(widget_udid)] = Widget(item[0], item[1], item[2], item[3],widget_udid,self.driver)
            if item[3] == 1 or item[3]==2:
                self.operatable_widgets.append(str(widget_udid))
            else:
                self.display_widgets.append(str(widget_udid))
        self.mask = [0]*100

    def add_trigged_api(self,sens_api_name_list):
        for sens_api_name in sens_api_name_list:
            if sens_api_name not in self.sensitive_apis_trigged:
                self.sensitive_apis_trigged.append(sens_api_name)
                self.sensitive_apis_trigged_num += 1

    def add_visited_widgets(self,key_widget):
        if key_widget not in self.visited_widgets_list:
            self.visited_widgets_list.append(key_widget)
            if self.unvisited_widgets_num>0:
                self.unvisited_widgets_num -= 1


