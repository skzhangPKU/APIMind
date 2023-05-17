from utils.general_util import scan_file
import json
import os
from cliffs_delta import cliffs_delta

def get_all_apis(path):
    apks = scan_file(path,includeFile=False)
    RL_GEN_list = {}
    for apk in apks:
        dates = scan_file(apk,includeFile=False)
        apk_name = apk.split('/')[-1]
        apk_apis_name_dict = {apk_name:[]}
        for date in dates:
            dumped_files = scan_file(date,includeFile=True)
            textual_semantics = date + '/textual_semantics.json'
            if not os.path.exists(textual_semantics):
                continue
            with open(textual_semantics, 'r') as file_obj:
                json_dict = json.load(file_obj)
            api_name_list = json_dict['api_name_list']
            apk_apis_name_dict[apk_name].extend(list(set(api_name_list)))
        apk_apis_name_dict[apk_name] = list(set(apk_apis_name_dict[apk_name]))
        RL_GEN_list.update(apk_apis_name_dict)
    return RL_GEN_list

def get_all_statistics():
    path1 = '/home/andrew/workspace/GUIFuzzing/baselines/API_RL_baseline_image_state_change_reward/dumps'
    RL_GEN_list = get_all_apis(path1)
    path2 = '/home/andrew/workspace/GUIFuzzing/baselines/API_RL_baseline_image_state_reward_api_code/dumps'
    RL_API_list = get_all_apis(path2)
    path3 = '/home/andrew/workspace/GUIFuzzing/FlowCog/labeledSamples'
    GUIMind_list = get_all_apis(path3)
    # calculate sum
    RL_GEN_key = {}
    RL_GEN_sum = 0
    for pk_key in RL_GEN_list:
        RL_GEN_key[pk_key] = len(RL_GEN_list[pk_key])
        RL_GEN_sum += len(RL_GEN_list[pk_key])
    # second
    RL_API_key = {}
    RL_API_sum = 0
    for pk_key in RL_API_list:
        RL_API_key[pk_key] = len(RL_API_list[pk_key])
        RL_API_sum += len(RL_API_list[pk_key])
    # third
    GUIMIND_key = {}
    GUIMIND_sum = 0
    for pk_key in GUIMind_list:
        GUIMIND_key[pk_key] = len(GUIMind_list[pk_key])
        GUIMIND_sum += len(GUIMind_list[pk_key])
    # return GUIMIND_key,RL_GEN_key,RL_API_key
    return GUIMind_list,RL_GEN_list,RL_API_list

def rq11_statistic():
    GUIMIND_key,RL_GEN_key,RL_API_key = get_all_statistics()
    # calculate cliff delta
    RL_API_nums = []
    RL_GEN_nums = []
    GUIMind_nums = []
    for pk_key in GUIMIND_key:
        if pk_key in RL_GEN_key:
            RL_GEN_nums.append(RL_GEN_key[pk_key])
        else:
            RL_GEN_nums.append(0)
        if pk_key in RL_API_key:
            RL_API_nums.append(RL_API_key[pk_key])
        else:
            RL_API_nums.append(0)
        GUIMind_nums.append(GUIMIND_key[pk_key])
    print(cliffs_delta(GUIMind_nums,RL_API_nums))
    print(cliffs_delta(GUIMind_nums,RL_GEN_nums))
    print(cliffs_delta(RL_API_nums,RL_GEN_nums))


def rq12_statistic():
    GUIMind_list,RL_GEN_list,RL_API_list = get_all_statistics()
    # get commons
    comm = 0
    for pk_key in GUIMind_list:
        if pk_key in RL_GEN_list:
            list1 = RL_GEN_list[pk_key]
            list2 = GUIMind_list[pk_key]
            comm += len(set(list1) & set(list2))
    comm1 = 0
    for pk_key in GUIMind_list:
        if pk_key in RL_API_list:
            list1 = RL_API_list[pk_key]
            list2 = GUIMind_list[pk_key]
            comm1 += len(set(list1) & set(list2))
    comm2 = 0
    for pk_key in RL_API_list:
        if pk_key in RL_GEN_list:
            list1 = RL_GEN_list[pk_key]
            list2 = RL_API_list[pk_key]
            comm2 += len(set(list1) & set(list2))
    print('haha')


def rq13_statistic():
    GUIMind_list,RL_GEN_list,RL_API_list = get_all_statistics()
    # find difference
    # in RL_API not in GUIMind
    comm = 0
    for pk_key in RL_API_list:
        list2 = RL_API_list[pk_key]
        if pk_key in GUIMind_list:
            list1 = GUIMind_list[pk_key]
            comm += len([i for i in list2 if i not in list1])
        else:
            comm += len(list2)
    # in GUIMind not in RL_API
    comm1 = 0
    for pk_key in GUIMind_list:
        list2 = GUIMind_list[pk_key]
        if pk_key in RL_API_list:
            list1 = RL_API_list[pk_key]
            comm1 += len([i for i in list2 if i not in list1])
        else:
            comm1 += len(list2)
    print('haha')


def rq14_statistic():
    GUIMind_list,RL_GEN_list,RL_API_list = get_all_statistics()
    # find difference
    # in RL_API not in GUIMind
    comm = 0
    for pk_key in RL_GEN_list:
        list2 = RL_GEN_list[pk_key]
        if pk_key in GUIMind_list:
            list1 = GUIMind_list[pk_key]
            comm += len([i for i in list2 if i not in list1])
        else:
            comm += len(list2)
    # in GUIMind not in RL_API
    comm1 = 0
    for pk_key in GUIMind_list:
        list2 = GUIMind_list[pk_key]
        if pk_key in RL_GEN_list:
            list1 = RL_GEN_list[pk_key]
            comm1 += len([i for i in list2 if i not in list1])
        else:
            comm1 += len(list2)
    print('haha')

if __name__ == '__main__':
    # rq11_statistic()
    # rq12_statistic()
    # rq13_statistic()
    rq14_statistic()
    print('haha')

# 791 813 1194
# 1442 1495 2178
# RL-GEN  1442  1423（中位数更小） 289（标准差更大）[1098,1423,1805]
# RL-API  1495  1452（中位数更小）248（标准差更大）[1215,1452,1818]
# GUIMIND 2178  2219（中位数更大） 102（标准差更小）[2038, 2219, 2277]
