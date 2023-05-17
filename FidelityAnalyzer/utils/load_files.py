from PIL import Image
import json
import os

def preload(date):
    textual_semantics = date + '/textual_semantics.json'
    with open(textual_semantics, 'r') as file_obj:
        json_dict = json.load(file_obj)
    api_name_list = json_dict['api_name_list']
    api_description_list = json_dict['api_description_list']
    if 'widget_context_dependency' in json_dict:
        widget_context_dependency = json_dict['widget_context_dependency']
    else:
        widget_context_dependency = ''
    if 'widget_self_dependency' in json_dict:
        widget_self_dependency = json_dict['widget_self_dependency']
    else:
        widget_self_dependency = ''
    if 'op_widget_text' in json_dict:
        op_widget_text = json_dict['op_widget_text']
    else:
        op_widget_text = ''
    if 'op_widget_udid' in json_dict:
        op_widget_udid = json_dict['op_widget_udid']
    else:
        op_widget_udid = ''
    if 'op_widget_bounds' in json_dict:
        op_widget_bounds = json_dict['op_widget_bounds']
    else:
        op_widget_bounds = '[0,0,0,0]'
    new_img_path = date + '/new_gui.png'
    new_img = Image.open(new_img_path)
    new_img.close()
    old_img_path = date + '/old_gui.png'
    if not os.path.isfile(old_img_path):
        old_img_path = date + '/start.png'
    old_img = Image.open(old_img_path)
    old_img.close()
    new_xml_path = date + '/new_xml.xml'
    with open(new_xml_path, 'r') as f:
        new_xmls = f.read()
    old_xml_path = date + '/old_xml.xml'
    if not os.path.isfile(old_xml_path):
        old_xml_path = date + '/start.xml'
    with open(old_xml_path, 'r') as f:
        old_xmls = f.read()
    with open(date+'/label.txt','r') as f:
        label_str = f.read()
    labels = [int(item) for item in label_str.split(',')]
    return api_name_list, api_description_list, widget_context_dependency, widget_self_dependency,  op_widget_text, op_widget_udid, op_widget_bounds, new_img, old_img, new_xmls, old_xmls, labels

def preload_fewer(date):
    textual_semantics = date + '/textual_semantics.json'
    with open(textual_semantics, 'r') as file_obj:
        json_dict = json.load(file_obj)
    api_name_list = json_dict['api_name_list']
    api_description_list = json_dict['api_description_list']
    new_xml_path = date + '/new_xml.xml'
    with open(new_xml_path, 'r') as f:
        new_xmls = f.read()
    new_img_path = date + '/new_gui.png'
    new_img = Image.open(new_img_path)
    new_img.close()
    with open(date + '/label.txt', 'r') as f:
        label_str = f.read()
    labels = [int(item) for item in label_str.split(',')]
    return api_name_list, api_description_list, new_xmls, new_img,labels