from utils.scraper import PlayStore
from  similarities import ClipSimilarity
from PIL import Image
from appium import webdriver
from appium_helper import AppiumLauncher
from xml.etree import ElementTree as ET
from utils.widget_util import parse_widgets
from utils.widget_util import generate_udid_str
import uuid
import wordninja
import pickle
import re

def consistence_analysis():
    pkName = 'org.wikipedia'
    play_store = PlayStore(pkName)
    soup = play_store._generate_soup()
    description = play_store._fetch_description(soup)

def find_button_uuid():
    xmlRoot = ET.fromstring(driver.page_source)
    labeled_text = parse_widgets(xmlRoot, False, False, testing=False)
    usable_widgets = []
    for key_, item in enumerate(labeled_text):
        if item[3] == 1 or item[3] == 2:
            udid_str = generate_udid_str(driver.current_activity, item)
            widget_udid = uuid.uuid3(uuid.NAMESPACE_DNS, udid_str)
            print(item[0])
            if item[0]=='LOG IN':
                print('temp find')

res = None
def updateRes(parnentNode):
    global res
    res = parnentNode

def widget_attribute_context():
    global res
    widget_udid = '5a8fe744-ea33-30b9-b737-7b96bf8daf86'
    coordinates = '[766,1218][1004,1348]'
    activity_name = 'org.wikipedia.main.MainActivity'
    text_class = 20
    the_class =1
    params = widget_udid,coordinates,activity_name,text_class,the_class
    layout_xml = driver.page_source
    xmlRoot = ET.fromstring(layout_xml)
    findLeafMostNodesAtPoint(params,xmlRoot,None)
    context_text = []
    context_resource = []
    if res is not None:
        for item in res:
            text = item.attrib['text'] if 'text' in item.attrib else ''
            resource_id = item.attrib['resource-id'] if 'resource-id' in item.attrib else ''
            context_text.append(text)
            resource_id_cut = ' '.join(wordninja.split(resource_id))
            context_resource.append(resource_id_cut)
        res = None
    context_text_str = ' '.join(context_text)
    context_resource_str = ' '.join(context_resource)

def findLeafMostNodesAtPoint(params, rootNode, parnentNode):
    foundInChild = False
    for node in rootNode:
        foundInChild |= findLeafMostNodesAtPoint(params,node,rootNode)
    if foundInChild:
        return True
    widget_udid, coordinates, activity_name, text_class, the_class = params
    if coordinates == rootNode.attrib['bounds']:
        text = rootNode.attrib['text'] if 'text' in rootNode.attrib else ''
        bounds = coordinates
        resource_id = rootNode.attrib['resource-id'] if 'resource-id' in rootNode.attrib else ''
        class_string = rootNode.attrib['class'] if 'class' in rootNode.attrib else ''
        scrollable = rootNode.attrib['scrollable'] if 'scrollable' in rootNode.attrib else 'false'
        content_desc = rootNode.attrib['content-desc'] if 'content-desc' in rootNode.attrib else ''
        index = rootNode.attrib['index'] if 'index' in rootNode.attrib else ''
        item = [text,text_class,bounds,the_class,resource_id,class_string,scrollable,content_desc,index]
        udid_str = generate_udid_str(activity_name, item)
        tmp_widget_udid = uuid.uuid3(uuid.NAMESPACE_DNS, udid_str)
        if str(tmp_widget_udid) == widget_udid:
            updateRes(parnentNode)
            return True
        return False
    else:
        return False

def GUI_text_similarity():
    img_fps = 'tmp/p1.png'
    texts = 'usename password log in'
    imgs = Image.open(img_fps)
    m = ClipSimilarity()
    sim_scores = m.similarity(imgs,texts)
    print('hah')

def api_info():
    api = 'com.android.server.ConnectivityService,getActiveNetworkInfo'
    api_name = api.replace(',','.')
    api_split = wordninja.split(api)

def load_permission_apis():
    api_des_dict = {}
    with open('monitoring/permissions_api_bak.txt','r') as f:
        permission_api_descriptions = f.readlines()
    for pad_item in permission_api_descriptions:
        pad_list = pad_item.split('|')
        api_name = pad_list[0].replace(',','.')
        self_api_name = api_name.replace('.', ' ').replace('$', ' ')
        self_sense_api_list = self_api_name.split(' ')
        reshape_sense_api = []
        for self_item in self_sense_api_list:
            reshape_sense_api.extend(camel_case_split(self_item))
        reshape_self_sense_api_str = ' '.join(reshape_sense_api)
        api_des = pad_list[1]
        api_des_dict[api_name] = [reshape_self_sense_api_str,api_des.strip()]
    with open('monitoring/permissions_api.pkl', 'wb') as f:
        pickle.dump(api_des_dict, f)
    print('finished')

def camel_case_split(api_name):
    return re.split("(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", api_name)

def get_api_descriptions(sens_api):
    with open('monitoring/permissions_api.pkl', 'rb') as f:
        api_des_dict = pickle.load(f)
    if sens_api in api_des_dict:
        api_des_list = api_des_dict[sens_api]
        self_description, comment_description = api_des_list[0], api_des_list[1]
        return self_description, comment_description
    else:
        class_name, function_name = sens_api.rsplit('.', 1)
        for item in api_des_dict.keys():
            if class_name in item and function_name in item:
                api_des_list = api_des_dict[item]
                self_description, comment_description = api_des_list[0], api_des_list[1]
                return self_description, comment_description
    return None,None

if __name__ == '__main__':
    # consistence_analysis()
    # GUI_text_similarity()
    # widget_attribute_context()
    # api_info()
    self_description, comment_description = get_api_descriptions('com.android.bluetooth.a2dpsink.A2dpSinkService$BluetoothA2dpSinkBinder.getConnectionState')
    # load_permission_apis()