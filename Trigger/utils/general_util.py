import os
from os import path

def scan_file(url):
    file_names = []
    file_list = os.listdir(url)
    for file_item in file_list:
        file_name = path.join(url,file_item)
        file_names.append(file_name)
    return file_names

def parse_pages(widget_list):
    for widget in widget_list:
        # user agreements
        if widget[0] == '我同意' or widget[0].find('同意')==0 or widget[0] == 'Agree':
            coord_list = [widget[2][0] * 1080, widget[2][1] * 2340, widget[2][2] * 1080, widget[2][3] * 2340]
            x,y = (coord_list[0] + coord_list[2])/2, (coord_list[1] + coord_list[3])/2
            return (x,y), False
    for widget in widget_list:
        # slide UI pages
        if 'ViewPager' in widget[5]:
            x_diff = widget[2][2] - widget[2][0]
            y_diff = widget[2][3] - widget[2][1]
            if x_diff >= 0.9 and y_diff >= 0.7:
                coord_list = [widget[2][0] * 1080, widget[2][1] * 2340, widget[2][2] * 1080, widget[2][3] * 2340]
                x, y = (coord_list[0] + coord_list[2]) / 2, (coord_list[1] + coord_list[3]) / 2
                return (x,y), True
    return None, None
