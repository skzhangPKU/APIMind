import cv2
import numpy as np
import torch
from PIL import Image
from io import BytesIO
from xml.etree import ElementTree as ET
import json

def imread(path):
    im = Image.open(path)
    return np.array(im)

def save_gui_image(path,img_dict):
    for img_name in img_dict.keys():
        gui_img = img_dict[img_name]
        im = Image.open(BytesIO(gui_img))
        im.save(path+'/'+img_name+'.png')

def save_xml_file(path,xml_dict):
    for xml_name in xml_dict.keys():
        xml_file = xml_dict[xml_name]
        with open(path+'/'+xml_name+'.xml','w') as f:
            f.writelines(xml_file)

def save_json_file(path,json_dict):
    with open(path+'/textual_semantics.json','w') as file_obj:
        json.dump(json_dict,file_obj)

def toimage(arr):
    data = np.asarray(arr)
    shape = list(data.shape)
    strdata = data.tostring()
    shape = (shape[1], shape[0])
    image = Image.frombytes('RGB', shape, strdata)
    return image

def fromimage(im):
    return np.array(im)

def imresize(arr, size,interp='bilinear'):
    im = toimage(arr)
    size = (size[1], size[0])
    func = {'nearest': 0, 'lanczos': 1, 'bilinear': 2, 'bicubic': 3, 'cubic': 3}
    imnew = im.resize(size, resample=func[interp])
    return fromimage(imnew)

def get_screen_rgb(im=None):
    MEAN_TORCH_BGR = np.array((103.53, 116.28, 123.675), dtype=np.float32).reshape((1, 3, 1, 1))
    STD_TORCH_BGR = np.array((57.375, 57.12, 58.395), dtype=np.float32).reshape((1, 3, 1, 1))
    func = {'nearest': 0, 'lanczos': 1, 'bilinear': 2, 'bicubic': 3, 'cubic': 3}
    imnew = im.resize((180,320), resample=func['bilinear'])
    img = fromimage(imnew)
    norm_img = (img[..., [2, 1, 0]] - MEAN_TORCH_BGR.flat) / STD_TORCH_BGR.flat
    norm_img = np.transpose(norm_img, (2, 0, 1))[np.newaxis, ...]
    norm_img = torch.autograd.Variable(torch.Tensor(norm_img)).cuda()
    return norm_img

def get_screen(param=None,flag=None):
    MEAN_TORCH_BGR = np.array((103.53, 116.28, 123.675), dtype=np.float32).reshape((1, 3, 1, 1))
    STD_TORCH_BGR = np.array((57.375, 57.12, 58.395), dtype=np.float32).reshape((1, 3, 1, 1))
    if flag=='img_path':
        img = imresize(imread(param), (320, 180))
    elif flag=='bytes_io':
        screen = cv2.imdecode(np.frombuffer(param, np.uint8), cv2.IMREAD_COLOR)
        img = imresize(screen, (320, 180))
    norm_img = (img[..., [2, 1, 0]] - MEAN_TORCH_BGR.flat) / STD_TORCH_BGR.flat
    norm_img = np.transpose(norm_img, (2, 0, 1))[np.newaxis, ...]
    norm_img = torch.autograd.Variable(torch.Tensor(norm_img)).cuda()
    return norm_img

def image_match(bytes_target,bytes_image,value,reverse):
    img_gray = cv2.cvtColor(cv2.imdecode(np.frombuffer(bytes_image, np.uint8), cv2.IMREAD_COLOR), cv2.COLOR_BGR2GRAY)
    template = cv2.cvtColor(cv2.imdecode(np.frombuffer(bytes_target, np.uint8), cv2.IMREAD_COLOR), cv2.COLOR_BGR2GRAY)
    w, h = template.shape[::-1]
    thresholdFlag = True
    if thresholdFlag:
        ret0,img_gray = cv2.threshold(img_gray, 225, 255, cv2.THRESH_BINARY)
        ret1,template = cv2.threshold(template, 225, 255, cv2.THRESH_BINARY)
    if reverse:
        template = 255 - template
    res = cv2.matchTemplate(img_gray,template,cv2.TM_CCOEFF_NORMED)
    threshold = value
    res_max = np.amax(res)
    if res_max>=threshold:
        loc = np.where(res >= res_max)
    else:
        return None
    for pt in zip(*loc[::-1]):
        x = int(pt[0] + w/2)
        y = int(pt[1] + h/2)
        return (x,y)

def get_class_list(xml_a):
    ele_a = ET.fromstring(xml_a)
    elements_a = ele_a.findall('.//*')
    class_list = []
    for item in elements_a:
        class_ = item.attrib['class']
        class_list.append(class_)
    return class_list