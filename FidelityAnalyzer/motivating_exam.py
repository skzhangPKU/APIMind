from utils.general_util import scan_file
import json
import os

def motivating_example():
    apks = scan_file('/home/andrew/workspace/GUIFuzzing/API_flow_EX_uiautomator2/dumps')
    for apk in apks:
        dates = scan_file(apk)
        api_name_list = []
        for date in dates:
            dumped_files = scan_file(date)
            textual_semantics = date + '/textual_semantics.json'
            if not os.path.exists(textual_semantics):
                continue
            with open(textual_semantics, 'r') as file_obj:
                json_dict = json.load(file_obj)
            try:
                api_name_list = json_dict['api_name_list']
                for api_name in api_name_list:
                    if 'Line' in api_name:
                        print(date, ' current api name', api_name)
                # if 'Line' in json_dict['api_name']:
                #     print(date, ' current api name', json_dict['api_name'])
            except:
                continue
            api_name_list.append(json_dict['api_name_list'])
        # print(apk.split('/')[-1],api_name_list)
        # print('finished')

def motivating_example2():
    dates = scan_file('com.ihope.hbdt')
    api_name_list = []
    for date in dates:
        dumped_files = scan_file(date)
        textual_semantics = date + '/textual_semantics.json'
        with open(textual_semantics, 'r') as file_obj:
            json_dict = json.load(file_obj)
        if 'Line' in json_dict['api_name']:
            print(date,' current api name', json_dict['api_name'])
        api_name_list.append(json_dict['api_name'])
    print(api_name_list)

if __name__ == '__main__':
    motivating_example()