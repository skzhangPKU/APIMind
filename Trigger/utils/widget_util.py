from collections.abc import Iterable
import re

def convert_class_to_text_label(the_class_of_text):
    lookup_class_label_dict = {"AdView": 1, "HtmlBannerWebView":1, "AdContainer":1, "ImageView":2, "BottomTagGroupView": 3, "BottomBar": 3, "ButtonBar": 4, "CardView": 5, "CheckBox": 6, "CheckedTextView":6, "DrawerLayout": 7, "DatePicker": 8, "ImageView": 9, "ImageButton": 10, "GlyphView": 10, "AppCompactButton": 10, "AppCompactImageButton": 10, "ActionMenuItemView":10, "ActionMenuItemPresenter":10, "EditText": 11, "SearchBoxView": 11, "AppCompatAutoCompleteTextView": 11, "TextView": 11, "ListView": 12, "RecyclerView": 12, "ListPopUpWindow": 12, "tabItem": 12, "GridView": 12, "MapView": 13, "SlidingTab": 14, "NumberPicker": 15, "Switch": 16, "ViewPageIndicatorDots": 17, "PageIndicator": 17, "CircleIndicator": 17, "PagerIndicator": 17, "RadioButton": 18, "CheckedTextView": 18, "SeekBar": 19, "Button": 20, "TextView": 20, "ToolBar": 21, "TitleBar": 21, "ActionBar": 21, "VideoView": 22, "WebView": 23}
    the_class_of_text = the_class_of_text.split(".")[-1]
    if lookup_class_label_dict.get(the_class_of_text):
        return lookup_class_label_dict.get(the_class_of_text)
    else:
        for key, val in lookup_class_label_dict.items():
            if the_class_of_text.endswith(key):
                return val
        return 0

def parse_widgets_u2(xmlRoot,in_list, in_drawer, testing):
    results = []
    text_class = 0
    if 'text' in xmlRoot.attrib and isinstance(xmlRoot.attrib['text'],Iterable) and xmlRoot.attrib['text'] and xmlRoot.attrib['text'].strip():
        text = xmlRoot.attrib['text']
    else:
        text = ''
    class_flag = False
    if 'class' in xmlRoot.attrib:
        the_class = xmlRoot.attrib['class']
        the_class = the_class.split('.')[-1]
    elif 'className' in xmlRoot.attrib:
        the_class = xmlRoot.attrib['className']
        the_class = the_class.split('.')[-1]
    else:
        class_flag = True
    if not class_flag:
        if the_class and the_class.strip():
            if the_class == 'TextView':
                if xmlRoot.attrib['clickable']=='true':
                    text_class = 20
                else:
                    text_class = 11
            else:
                text_class = convert_class_to_text_label(the_class)
        if text_class==0 and (in_drawer or in_list):
            if in_drawer:
                text_class = 25
            if in_list:
                text_class = 24
        if 'bounds' in xmlRoot.attrib and xmlRoot.attrib['bounds']:
            boundStr = xmlRoot.attrib['bounds']
            if len(boundStr)>=10:
                left, top, right, bottom = parseBounds(boundStr)
                bounds = [left, top, right, bottom]
            else:
                bounds = [0,0,0,0]
        if xmlRoot.attrib['clickable']=='true' or xmlRoot.attrib['scrollable']=='true':
            if xmlRoot.attrib['clickable']=='true':
                results.append([text,text_class,bounds,1])
            else:
                results.append([text, text_class, bounds, 2])
        elif the_class == 'TextView':
            results.append([text, text_class, bounds, 0])
    if len(list(xmlRoot)) != 0:
        for child_node in xmlRoot:
            if text_class == 12:
                in_list = True
            if text_class == 7:
                in_drawer = True
            results.extend(parse_widgets(child_node,in_list,in_drawer,testing))
    return results

def parse_widgets(xmlRoot,in_list, in_drawer, testing):
    results = []
    text_class = 0
    if xmlRoot.tag != 'hierarchy':
        if 'text' in xmlRoot.attrib and isinstance(xmlRoot.attrib['text'],Iterable) and xmlRoot.attrib['text'] and xmlRoot.attrib['text'].strip():
            text = xmlRoot.attrib['text']
        else:
            text = ''
        if 'class' in xmlRoot.attrib:
            the_class = xmlRoot.attrib['class']
            the_class = the_class.split('.')[-1]
        elif 'className' in xmlRoot.attrib:
            the_class = xmlRoot.attrib['className']
            the_class = the_class.split('.')[-1]
        if the_class and the_class.strip():
            if the_class == 'TextView':
                if xmlRoot.attrib['clickable']=='true':
                    text_class = 20
                else:
                    text_class = 11
            else:
                text_class = convert_class_to_text_label(the_class)
        if text_class==0 and (in_drawer or in_list):
            if in_drawer:
                text_class = 25
            if in_list:
                text_class = 24
        if 'bounds' in xmlRoot.attrib and xmlRoot.attrib['bounds']:
            boundStr = xmlRoot.attrib['bounds']
            if len(boundStr)>=10:
                left, top, right, bottom = parseBounds(boundStr)
                bounds = [left, top, right, bottom]
            else:
                bounds = [0,0,0,0]
        if ('visible-to-user' in xmlRoot.attrib and xmlRoot.attrib['visible-to-user']=='true'):
            visibility = True
        else:
            visibility = False
        resource_id = xmlRoot.attrib['resource-id'] if 'resource-id' in xmlRoot.attrib else ''
        class_string = xmlRoot.attrib['class'] if 'class' in xmlRoot.attrib else ''
        scrollable = xmlRoot.attrib['scrollable'] if 'scrollable' in xmlRoot.attrib else 'false'
        content_desc = xmlRoot.attrib['content-desc'] if 'content-desc' in xmlRoot.attrib else ''
        index = xmlRoot.attrib['index'] if 'index' in xmlRoot.attrib else ''
        if visibility and testing and text_class==0:
            if xmlRoot.attrib['clickable']=='true' or xmlRoot.attrib['scrollable']=='true':
                results.append([text,text_class,bounds,the_class,resource_id,class_string,scrollable,content_desc,index])
            elif the_class == 'TextView':
                results.append([text, text_class, bounds, 0,resource_id,class_string,scrollable,content_desc,index])
        elif visibility:
            if xmlRoot.attrib['clickable']=='true' or xmlRoot.attrib['scrollable']=='true':
                if xmlRoot.attrib['clickable']=='true':
                    results.append([text,text_class,bounds,1,resource_id,class_string,scrollable,content_desc,index])
                else:
                    results.append([text, text_class, bounds, 2,resource_id,class_string,scrollable,content_desc,index])
            elif the_class == 'TextView':
                results.append([text, text_class, bounds, 0,resource_id,class_string,scrollable,content_desc,index])
    if len(list(xmlRoot)) != 0:
        for child_node in xmlRoot:
            if xmlRoot.tag == 'hierarchy':
                results.extend(parse_widgets(child_node, False, False, testing))
            else:
                if text_class == 12:
                    in_list = True
                if text_class == 7:
                    in_drawer = True
                results.extend(parse_widgets(child_node,in_list,in_drawer,testing))
    return results

def parseBounds(boundStr):
    boundPattern = '\\[-?(\\d+),-?(\\d+)\\]\\[-?(\\d+),-?(\\d+)\\]'
    result = re.match(boundPattern, boundStr)
    if result:
        left = int(result.group(1))
        top = int(result.group(2))
        right = int(result.group(3))
        bottom = int(result.group(4))
        return left, top, right, bottom

def generate_udid_str(activity_name,item_list):
    res = activity_name
    for i, item in enumerate(item_list):
        if i==2:
            continue
        res += str(item)
    return res