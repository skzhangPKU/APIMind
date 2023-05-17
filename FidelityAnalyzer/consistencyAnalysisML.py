from utils.general_util import scan_file,retrieveAppDes
import json
from PIL import Image
import os
import pickle
import pytesseract
import jieba
from utils.translate import send_request
from utils.translateCHN2ENG import translate2eng
from utils.file_util import readPklFile,writePklFile

import nltk.tree
from stanford_corenlp.parse_action_resource import parse_behaviors
from functools import reduce
from stanford_corenlp.behaviors import Behavior

from stanford_corenlp.wrapper import StanfordCoreNLPWrapper
from utils.load_files import preload

from utils.general_util import textChn2Eng
import random

from utils.xml_util import extractTextFromXml,extractWidgetTextFromXml

parser = StanfordCoreNLPWrapper('stanford_corenlp/stanford-corenlp-full')

def extractAppDesActionResource(appPackage):
    # 先尝试读取文件夹
    if os.path.exists('data/appDesARPair/' + appPackage + '.pkl'):
        App_desc_AP_pair = readPklFile('data/appDesARPair/' + appPackage + '.pkl')
    else:
        eng_app_description = retrieveAppDes(appPackage)
        App_desc_AP_pair = extractActionResource(eng_app_description)
        writePklFile('data/appDesARPair/' + appPackage + '.pkl',App_desc_AP_pair)
    return App_desc_AP_pair

def extractActionResource(raw_text):
    if raw_text.strip()=='':
        x = Behavior()
        return x
    global parser
    try:
        parsed_result = parser.parse(raw_text)
    except:
        del parser
        parser = StanfordCoreNLPWrapper('stanford_corenlp/stanford-corenlp-full')
        parsed_result = parser.parse(raw_text)
    parsed_json = json.loads(parsed_result)
    parsed_info = parsed_json["sentences"]
    parse_trees = []
    for sentence in parsed_info:
        parse_tree = sentence["parse_tree"]
        parse_trees.append(parse_tree)
    dependencies = [nltk.tree.Tree.fromstring(parse_tree) for (
        parse_tree) in parse_trees]
    behaviors = list()
    for dependency in dependencies:
        behavior = parse_behaviors(dependency)
        behaviors.append(behavior)
    if behaviors:
        x = reduce(lambda x, y: x + y, behaviors)
    else:
        x = Behavior()
    return x

'''
def extractTextFromImage(old_gui):
    patch = Image.new("RGBA", (1080, 80), "#FFFFFF")
    old_gui.paste(patch)
    image_text = pytesseract.image_to_string(old_gui, lang='chi_sim').strip().replace('。', '')
    old_gui.close()
    eng_GUI_text = textChn2Eng(image_text)
    return eng_GUI_text
'''

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
    return api_name_list, api_description_list, new_xmls, new_img

def analysis():
    # read directory
    apks = scan_file('dumps')
    samples = []
    labels = []
    for apk in apks:
        if apk != 'dumps/com.cdsb.newsreader':
            continue
        appPackage = apk.split('/')[-1]
        # app description
        App_desc_AP_pair = extractAppDesActionResource(appPackage)
        dates = scan_file(apk)
        for date in dates:
            dumped_files = scan_file(date)
            print('===========================================================')
            if len(dumped_files) >= 6:
                # case 1
                api_name_list, api_desc_list, consistence_context_resource_str, consistence_view_dependency_str, \
                op_widget_text, op_widget_udid, op_widget_bounds, new_gui, old_gui, new_xmls, old_xmls = preload(date)
                # source and destination GUI context
                # eng_GUI_context_str_source = extractTextFromImage(old_gui)
                eng_GUI_context_str_source = extractTextFromXml(old_xmls,appPackage)
                # eng_GUI_context_str_destination = extractTextFromImage(new_gui)
                eng_GUI_context_str_destination = extractTextFromXml(new_xmls,appPackage)
                old_gui.close()
                new_gui.close()
                # widget context
                consistence_context_resource_str = textChn2Eng(consistence_context_resource_str)
                # widget self
                consistence_view_dependency_str = textChn2Eng(consistence_view_dependency_str)
                op_widget_text = extractWidgetTextFromXml(old_xmls, appPackage, op_widget_bounds)
                # op_widget_text = extractWidgetTextFromXml(op_widget_bounds)
                # op_widget_text = textChn2Eng(op_widget_text)
                # extract action resource pairs
                GUI_context_source_AR_pair = extractActionResource(eng_GUI_context_str_source)
                GUI_context_dest_AR_pair = extractActionResource(eng_GUI_context_str_destination)
                Widget_context_AR_pair = extractActionResource(consistence_context_resource_str)
                Widget_self_AR_pair = extractActionResource(consistence_view_dependency_str)
                Op_widget_AP_pair = extractActionResource(op_widget_text)
                for index, api_desc in enumerate(api_desc_list):
                    # api description
                    api_description = api_desc.replace('com android internal','').replace('com android server','').replace('com android', '').replace('android', '')
                    api_AR_pair = extractActionResource(api_description)
                    tmp_str = ""
                    all_tuples = [App_desc_AP_pair,GUI_context_source_AR_pair,GUI_context_dest_AR_pair,Widget_context_AR_pair,Widget_self_AR_pair,Op_widget_AP_pair,api_AR_pair]
                    for tuple in all_tuples:
                        tmp_str += " ".join(str(x) for x in tuple.pairs)
                        tmp_str += " " + " ".join(str(x) for x in tuple.actions)
                        tmp_str += " " + " ".join(str(x) for x in tuple.resources)
                    # generate_samples()
                    label = random.choice([0,1])
                    print(tmp_str)
                    samples.append(tmp_str)
                    labels.append(label)
    writePklFile('samples/label_dataset.pkl',[samples,labels])
    print('finished')

if __name__ == '__main__':
    # 1.确保monitoring下有api的描述信息
    analysis()