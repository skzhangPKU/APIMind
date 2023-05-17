import uuid
from xml.etree import ElementTree as ET
from utils.widget_util import generate_udid_str
import wordninja

res = None
self_widget_text = None
def updateRes(parnentNode,widgetText):
    global res
    global self_widget_text
    res = parnentNode
    self_widget_text = widgetText

def consist_layout_context(widget_udid,coordinates,activity_name,text_class,the_class,layout_xml):
    global res
    global self_widget_text
    params = widget_udid, coordinates, activity_name, text_class, the_class
    xmlRoot = ET.fromstring(layout_xml)
    findLeafMostNodesAtPoint(params,xmlRoot,None)
    context_text = []
    context_resource = []
    content_desc_list = []
    if res is not None:
        for item in res:
            text = item.attrib['text'] if 'text' in item.attrib else ''
            resource_id = item.attrib['resource-id'] if 'resource-id' in item.attrib else ''
            content_desc = item.attrib['content-desc'] if 'content-desc' in item.attrib else ''
            if text.strip() != '':
                context_text.append(text)
            if resource_id.strip() != '':
                resource_id_cut = ' '.join(wordninja.split(resource_id))
                context_resource.append(resource_id_cut)
            if content_desc.strip() != '':
                content_desc_list.append(content_desc)
        res = None
    context_text_str = ' '.join(context_text)
    context_resource_str = ' '.join(context_resource)
    content_desc_str = ' '.join(content_desc_list)
    context_str = context_text_str + ' '+ context_resource_str +' '+content_desc_str
    view_dependency_input = ''
    if self_widget_text is not None:
        widget_resource_id_cut = ' '.join(wordninja.split(self_widget_text[1]))
        view_dependency_input = str(self_widget_text[0])
        if str(widget_resource_id_cut).strip() != '':
            view_dependency_input =  view_dependency_input + ' '+ str(widget_resource_id_cut)
        if str(self_widget_text[2]).strip() != '':
            view_dependency_input = view_dependency_input + ' '+str(self_widget_text[2])
        self_widget_text = None
    return context_str,view_dependency_input

def findLeafMostNodesAtPoint(params, rootNode, parnentNode):
    foundInChild = False
    for node in rootNode:
        foundInChild |= findLeafMostNodesAtPoint(params,node,rootNode)
    if foundInChild:
        return True
    widget_udid, coordinates, activity_name, text_class, the_class = params
    if 'bounds' in rootNode.attrib:
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
                updateRes(parnentNode,[text,resource_id,content_desc])
                return True
    return False
