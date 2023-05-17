from appium import webdriver
from appium_helper import AppiumLauncher
import uuid
from lxml import etree
from xmldiff import main, formatting
from PIL import Image
from io import BytesIO
import numpy as np
from scipy.stats import wasserstein_distance
from xml.etree import ElementTree as ET
import Levenshtein

def generate_xml():
    appium = AppiumLauncher(4723)
    desired_caps = {'platformName': 'Android',
                     'platformVersion': '7',
                     'udid': 'emulator-5554',
                     'deviceName': 'Xiaomi10',
                     'autoGrantPermissions': False,
                     'fullReset': False,
                     'resetKeyboard': True,
                     'androidInstallTimeout': 30000,
                     'isHeadless': False,
                     'automationName': 'uiautomator2',
                     'adbExecTimeout': 30000,
                     'appWaitActivity': '*',
                     'newCommandTimeout': 200}

    driver = webdriver.Remote(f'http://127.0.0.1:4723/wd/hub', desired_caps)
    xml_a = driver.page_source
    class_list_a = get_class_list(xml_a)
    xml_b = driver.page_source
    class_list_b = get_class_list(xml_b)
    score = Levenshtein.seqratio(class_list_a, class_list_b)

def get_class_list(xml_a):
    ele_a = ET.fromstring(xml_a)
    elements_a = ele_a.findall('.//*')
    class_list = []
    for item in elements_a:
        class_ = item.attrib['class']
        class_list.append(class_)
    return class_list

def fromimage(im, flatten):
    if flatten:
        im = im.convert('F')
    a = np.array(im)
    return a

def get_histogram(img):
  h, w = img.shape
  hist = [0.0] * 256
  for i in range(h):
    for j in range(w):
      hist[img[i, j]] += 1
  return np.array(hist) / (h * w)

def normalize_exposure(img):
  img = img.astype(int)
  hist = get_histogram(img)
  cdf = np.array([sum(hist[:i+1]) for i in range(len(hist))])
  sk = np.uint8(255 * cdf)
  height, width = img.shape
  normalized = np.zeros_like(img)
  for i in range(0, height):
    for j in range(0, width):
      normalized[i, j] = sk[img[i, j]]
  return normalized.astype(int)

def get_img(img, norm_exposure=False):
    pil_img = Image.open(BytesIO(img))
    img = fromimage(pil_img, flatten=True)
    if norm_exposure:
        img = normalize_exposure(img)
    return img

def earth_movers_distance(img_b, img_a):
    pil_imga = get_img(img_a, norm_exposure=True)
    pil_imgb = get_img(img_b, norm_exposure=True)
    hist_a = get_histogram(pil_imga)
    hist_b = get_histogram(pil_imgb)
    return wasserstein_distance(hist_a, hist_b)

def find_difference():
    with open('xmls/basic_xml.xml','r') as f:
        basic_xml = f.readlines()
    with open('xmls/differ_xml1.xml', 'r') as f:
        differ_xml1 = f.readlines()
    diff = main.diff_files('xmls/basic_xml.xml', 'xmls/differ_xml1.xml',
                           formatter=formatting.XMLFormatter())
    print('difference')

if __name__ == '__main__':
    generate_xml()
