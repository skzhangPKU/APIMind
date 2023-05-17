import os
from os import path
from utils.file_util import readPklFile,writePklFile
from retrive_descriptions import get_app_description
from utils.translate import send_request
import pickle
from xml.etree import ElementTree as ET

def scan_file(url,includeFile):
    file_names = []
    file_list = os.listdir(url)
    for file_item in file_list:
        file_name = path.join(url,file_item)
        if includeFile:
            file_names.append(file_name)
        else:
            if not os.path.isfile(file_name):
                file_names.append(file_name)
    return file_names

def textChn2Eng(raw_text):
    if raw_text.strip() == '':
        return ''
    text_list = raw_text.strip().split('\r')
    possible_sentences_list = []
    for line in text_list:
        item_list = line.split('\n')
        for item in item_list:
            item = item.replace('！','。').replace('？','。')
            possible_sentences_list.extend(item.split('。'))
    des_list = []
    for sens in possible_sentences_list:
        if sens.strip() == '':
            continue
        if '\n' in sens:
            sens = sens.replace('\n', '。')
        des_list.append(send_request(sens))
    eng_text = '. '.join(des_list) + '.'
    return eng_text

def get_app_descriptions_eng(appPackage):
    if os.path.exists('appDescriptions/' + appPackage + '.pkl'):
        app_descriptions = readPklFile('appDescriptions/' + appPackage + '.pkl')
    else:
        app_descriptions = get_app_description(appPackage)
    if app_descriptions is None:
        app_descriptions_new = ''
        return app_descriptions_new
    # translate Chinese to English
    app_descriptions_new = textChn2Eng(app_descriptions)
    return app_descriptions_new


def retrieveAppDes(appPackage):
    # 先读英文应用描述，如果没有则读中文描述
    if os.path.exists('appDescriptionsEng/'+appPackage+'.pkl'):
        app_descriptions_new = readPklFile('appDescriptionsEng/'+appPackage+'.pkl')
    else:
        app_descriptions_new = get_app_descriptions_eng(appPackage)
        writePklFile('appDescriptionsEng/' + appPackage + '.pkl',app_descriptions_new)
    return app_descriptions_new

