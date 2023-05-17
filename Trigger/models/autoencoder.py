from xml.etree import ElementTree as ET
import numpy as np
from PIL import Image
from utils.widget_util import parseBounds
import torch
import torch.nn as nn
import torch.nn.functional as F
import config

class ScreenLayout():

    def __init__(self, xmlStr):
        self.pixels = np.full((100,56,2), 0, dtype=float)
        self.vert_scale = 100 / config.Device_resolution_y
        self.horiz_scale = 56 / config.Device_resolution_x
        self.load_screen(xmlStr)

    def load_screen(self, xmlStr):
        xmlRoot = ET.fromstring(xmlStr)
        try:
            self.render_contents_u2(xmlRoot)
        except Exception as e:
            pass

    def render_contents_u2(self,node):
        if len(list(node)) !=0:
            for child_node in node:
                self.render_contents_u2(child_node)
        else:
            try:
                if ('visible-to-user' in node.attrib and node.attrib['visible-to-user']):
                    if 'bounds' in node.attrib:
                        if len(node.attrib['bounds']) >= 10:
                            boundStr = node.attrib['bounds']
                            left, top, right, bottom = parseBounds(boundStr)
                            x1 = int(left * self.horiz_scale)
                            y1 = int(top * self.vert_scale)
                            x2 = int(right * self.horiz_scale)
                            y2 = int(bottom * self.vert_scale)
                            if 'text' in node.attrib and node.attrib['text'] and node.attrib['text'].strip():
                                self.pixels[y1:y2, x1:x2, 0] = 1
                            else:
                                self.pixels[y1:y2, x1:x2, 1] = 1
            except Exception as e:
                print(e)

    def render_contents(self,node):
        if len(list(node)) !=0:
            for child_node in node:
                self.render_contents(child_node)
        else:
            try:
                if ('displayed' in node.attrib and node.attrib['displayed']):
                    if 'bounds' in node.attrib:
                        if len(node.attrib['bounds']) >= 10:
                            boundStr = node.attrib['bounds']
                            left, top, right, bottom = parseBounds(boundStr)
                            x1 = int(left * self.horiz_scale)
                            y1 = int(top * self.vert_scale)
                            x2 = int(right * self.horiz_scale)
                            y2 = int(bottom * self.vert_scale)
                            if 'text' in node.attrib and node.attrib['text'] and node.attrib['text'].strip():
                                self.pixels[y1:y2, x1:x2, 0] = 1
                            else:
                                self.pixels[y1:y2, x1:x2, 1] = 1
            except Exception as e:
                print(e)

    def convert_to_image(self):
        p = np.full((100,56,3), 255, dtype=np.uint)
        for y in range(len(self.pixels)):
            for x in range(len(self.pixels[0])):
                if (self.pixels[y][x] == [1,0]).all() or (self.pixels[y][x] == [1,1]).all():
                    p[y][x] = [0,0,255]
                elif (self.pixels[y][x] == [0,1]).all():
                    p[y][x] = [255,0,0]
        im = Image.fromarray(p.astype(np.uint8))
        im.save("example.png")

class LayoutEncoder(nn.Module):

    def __init__(self):
        super(LayoutEncoder, self).__init__()

        self.e1 = nn.Linear(11200, 2048)
        self.e2 = nn.Linear(2048, 256)
        self.e3 = nn.Linear(256, 64)


    def forward(self, input):
        encoded = F.relu(self.e3(F.relu(self.e2(F.relu(self.e1(input))))))
        return encoded


class LayoutDecoder(nn.Module):

    def __init__(self):
        super(LayoutDecoder, self).__init__()

        self.d1 = nn.Linear(64,256)
        self.d2 = nn.Linear(256, 2048)
        self.d3 = nn.Linear(2048, 11200)

    def forward(self, input):
        decoded = F.relu(self.d3(F.relu(self.d2(F.relu(self.d1(input))))))
        return decoded

class LayoutAutoEncoder(nn.Module):

    def __init__(self):
        super(LayoutAutoEncoder, self).__init__()

        self.enc = LayoutEncoder()
        self.dec = LayoutDecoder()

    def forward(self, input):
        return F.relu(self.dec(self.enc(input)))

