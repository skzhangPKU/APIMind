import cv2
import numpy as np
import torch
from PIL import Image

def image_match(reverse=True):
    pil_target = Image.open('tmp/p2.png')
    pil_image = Image.open('tmp/p1.png')
    cv2_target = cv2.cvtColor(np.asarray(pil_target), cv2.COLOR_RGBA2BGR)
    cv2_image = cv2.cvtColor(np.asarray(pil_image), cv2.COLOR_RGBA2BGR)
    img_gray = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2GRAY)
    template = cv2.cvtColor(cv2_target, cv2.COLOR_BGR2GRAY)
    w, h = template.shape[::-1]
    thresholdFlag = True
    if thresholdFlag:
        ret0,img_gray = cv2.threshold(img_gray, 225, 255, cv2.THRESH_BINARY)
        ret1,template = cv2.threshold(template, 225, 255, cv2.THRESH_BINARY)
    if reverse:
        template = 255 - template
    res = cv2.matchTemplate(img_gray,template,cv2.TM_CCOEFF_NORMED)
    threshold = 0.9
    res_max = np.amax(res)
    print('res_max ',res_max)#226
    if res_max>=threshold:
        loc = np.where(res >= res_max)
    else:
        return None
    for pt in zip(*loc[::-1]):
        x = int(pt[0] + w/2)
        y = int(pt[1] + h/2)
        return (x,y)


if __name__ == '__main__':
    final = image_match(False)
    final2 = image_match(True)
    print(final)