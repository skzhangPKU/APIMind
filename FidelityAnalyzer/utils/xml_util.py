from collections.abc import Iterable
import re
from xml.etree import ElementTree as ET
from utils.translate import send_request
from utils.general_util import textChn2Eng

def parseBounds(boundStr,flag=True):
    if flag:
        boundPattern = '\\[-?(\\d+),-?(\\d+)\\]\\[-?(\\d+),-?(\\d+)\\]'
    else:
        boundPattern = '\\[-?(\\d+),-?(\\d+),-?(\\d+),-?(\\d+)\\]'
    result = re.match(boundPattern, boundStr)
    if result:
        left = int(result.group(1))
        top = int(result.group(2))
        right = int(result.group(3))
        bottom = int(result.group(4))
        return left, top, right, bottom

def parse_bounds(boundStr):
    if len(boundStr) >= 10:
        left, top, right, bottom = parseBounds(boundStr,flag=True)
        bounds = [left, top, right, bottom]
    else:
        bounds = [0, 0, 0, 0]
    return bounds

def parse_widgets(xmlRoot, pkgName):
    results = []
    if xmlRoot.tag != 'hierarchy':
        if 'package' in xmlRoot.attrib and (xmlRoot.attrib['package']==pkgName or xmlRoot.attrib['package']!='com.android.systemui'):
            if 'bounds' in xmlRoot.attrib and xmlRoot.attrib['bounds']:
                bounds = parse_bounds(xmlRoot.attrib['bounds'])
                if bounds[2] < 1080 and bounds[3] < 2340:
                    if 'text' in xmlRoot.attrib and isinstance(xmlRoot.attrib['text'],Iterable) and xmlRoot.attrib['text'] and xmlRoot.attrib['text'].strip():
                        text = xmlRoot.attrib['text']
                        if ('visible-to-user' in xmlRoot.attrib and xmlRoot.attrib['visible-to-user']=='true'):
                            results.append(text)
    # recursive childrens
    if len(list(xmlRoot)) != 0:
        for child_node in xmlRoot:
            results.extend(parse_widgets(child_node,pkgName))
    return results

def batch_requests(labeled_text):
    text_list = []
    for words in labeled_text:
        if words.strip() == '':
            continue
        if '\n' in words:
            words = words.replace('\n', '。')
        text_list.append(textChn2Eng(words))
    eng_text = '. '.join(text_list) + '.'
    return eng_text

def extractTextFromXml(xml_str,appPackage):
    xmlRoot = ET.fromstring(xml_str)
    labeled_text = parse_widgets(xmlRoot,appPackage)
    eng_text = batch_requests(labeled_text)
    return eng_text


def parse_widgets_inner_text(xmlRoot,pkgName, widget_coords):
    results = []
    if xmlRoot.tag != 'hierarchy':
        if 'package' in xmlRoot.attrib and (xmlRoot.attrib['package']==pkgName or xmlRoot.attrib['package']!='com.android.systemui'):
            if 'bounds' in xmlRoot.attrib and xmlRoot.attrib['bounds']:
                bounds = parse_bounds(xmlRoot.attrib['bounds'])
                scrollable = xmlRoot.attrib['scrollable'] if 'scrollable' in xmlRoot.attrib else 'false'
                if scrollable == 'false':
                    if bounds[0]>=widget_coords[0] and bounds[1]>=widget_coords[1] and bounds[2] <= widget_coords[2] and bounds[3] < widget_coords[3]:
                        if 'text' in xmlRoot.attrib and isinstance(xmlRoot.attrib['text'],Iterable) and xmlRoot.attrib['text'] and xmlRoot.attrib['text'].strip():
                            text = xmlRoot.attrib['text']
                            if ('visible-to-user' in xmlRoot.attrib and xmlRoot.attrib['visible-to-user']=='true'):
                                results.append(text)
    # recursive childrens
    if len(list(xmlRoot)) != 0:
        for child_node in xmlRoot:
            results.extend(parse_widgets_inner_text(child_node,pkgName,widget_coords))
    return results

def extractWidgetTextFromXml(xml_str,appPackage,op_widget_bounds):
    xmlRoot = ET.fromstring(xml_str)
    widget_coords = parseBounds(op_widget_bounds.replace(' ', ''), flag=False)
    labeled_text = parse_widgets_inner_text(xmlRoot,appPackage,widget_coords)
    eng_text = batch_requests(labeled_text)
    return eng_text