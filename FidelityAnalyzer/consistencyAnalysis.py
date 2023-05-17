from sentence_transformers import SentenceTransformer
from consist.api_descriptions import get_api_descriptions
from similarities import ClipSimilarity
from consist.visual_dependency import consist_visual_context_by_clipsim
from utils.general_util import scan_file
import json
from PIL import Image
from consist.self_dependency import consist_self_dependency
from consist.similarity_score import calculate_combined_score
from retrive_descriptions import get_app_description
import os
from sklearn.metrics.pairwise import cosine_similarity
import pickle

bert = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2').cuda()
clip_sim = ClipSimilarity()

def preload(date):
    textual_semantics = date + '/textual_semantics.json'
    with open(textual_semantics, 'r') as file_obj:
        json_dict = json.load(file_obj)
    api_name_list = json_dict['api_name_list']
    api_description_list = json_dict['api_description_list']
    widget_context_dependency = json_dict['widget_context_dependency']
    widget_self_dependency = json_dict['widget_self_dependency']
    op_widget_text = json_dict['op_widget_text']
    op_widget_udid = json_dict['op_widget_udid']
    op_widget_bounds = json_dict['op_widget_bounds']
    new_img_path = date + '/new_gui.png'
    new_img = Image.open(new_img_path)
    old_img_path = date + '/old_gui.png'
    old_img = Image.open(old_img_path)
    new_xml_path = date + '/new_xml.xml'
    with open(new_xml_path, 'r') as f:
        new_xmls = f.read()
    old_xml_path = date + '/old_xml.xml'
    with open(old_xml_path, 'r') as f:
        old_xmls = f.read()
    return api_name_list, api_description_list, widget_context_dependency, widget_self_dependency,  op_widget_text, op_widget_udid, op_widget_bounds, new_img, old_img, new_xmls, old_xmls

def preload_fewer(date):
    textual_semantics = date + '/textual_semantics.json'
    with open(textual_semantics, 'r') as file_obj:
        json_dict = json.load(file_obj)
    api_name_list = json_dict['api_name_list']
    api_description_list = json_dict['api_description_list']
    new_xml_path = date + '/new_xml.xml'
    with open(new_xml_path, 'r') as f:
        new_xmls = f.read()
    new_img_path = date + '/new_gui.png'
    new_img = Image.open(new_img_path)
    return api_name_list, api_description_list, new_xmls, new_img

def analysis():
    # read directory
    apks = scan_file('dumps')
    for apk in apks:
        if apk != 'dumps/com.cdsb.newsreader':
            continue
        appPackage = apk.split('/')[-1]
        dates = scan_file(apk)
        for date in dates:
            dumped_files = scan_file(date)
            print('===========================================================')
            if len(dumped_files) >= 6:
                # case 1
                api_name_list, api_desc_list, consistence_context_resource_str, consistence_view_dependency_str, \
                op_widget_text, op_widget_udid, op_widget_bounds, new_gui, old_gui, new_xmls, old_xmls = preload(date)
                context_dependency_feature = bert.encode(consistence_context_resource_str).reshape(1, -1)
                view_dependency_feature = bert.encode(consistence_view_dependency_str).reshape(1, -1)
                if os.path.exists('appDescriptions/'+appPackage+'.pkl'):
                    app_descriptions = consist_self_dependency(appPackage)
                else:
                    app_descriptions = get_app_description(appPackage)
                if app_descriptions is None:
                    app_descriptions = ''
                self_dependency_feature = bert.encode(app_descriptions).reshape(1, -1)
                # api descriptions
                inconsist_api_list = []
                for index, api_desc in enumerate(api_desc_list):
                    visual_dependency_score = consist_visual_context_by_clipsim(new_gui, api_desc, clip_sim)[0][0]
                    api_desc_feature = bert.encode(api_desc).reshape(1, -1)
                    # calculate similarity
                    context_api_score = cosine_similarity(context_dependency_feature, api_desc_feature)[0][0]
                    view_api_score = cosine_similarity(view_dependency_feature, api_desc_feature)[0][0]
                    self_api_score = cosine_similarity(self_dependency_feature, api_desc_feature)[0][0]
                    # if view_api_score > 0.4:
                    #     print('api_desc',api_desc)
                    #     print('consistence_context_resource_str',consistence_context_resource_str)
                    #     print('consistence_view_dependency_str',consistence_view_dependency_str)
                    #     print('========================================================================')
                    # sour_score_list = [visual_dependency_score, context_api_score, view_api_score, self_api_score]
                    sour_score_list = [view_api_score, context_api_score, self_api_score, visual_dependency_score]
                    combined_score = calculate_combined_score(sour_score_list)
                    print(date, 'visual, context, widget, app desc, combine ', visual_dependency_score, context_api_score, view_api_score, self_api_score,combined_score)
                    if combined_score < 0.5:
                        # print('detect inconsistency', combined_score)
                        inconsist_api_list.append(api_name_list[index])
                        print('Actual: Incosistency')
                    else:
                        print('Actual: Cosistency')
                # dump inconsist api list
                if os.path.exists(date + '/False.txt'):
                    print('current directory: InConsistency')
                else:
                    print('current directory: Consistency')
                with open(date+'/inconsist_api.pkl', 'wb') as f:
                    pickle.dump(inconsist_api_list, f)
                # print(date,' more files inconsist api dumped')
            else:
                # case 2
                api_name_list, api_desc_list, new_xmls, new_gui = preload_fewer(date)
                if os.path.exists('appDescriptions/'+appPackage+'.pkl'):
                    app_descriptions = consist_self_dependency(appPackage)
                else:
                    app_descriptions = get_app_description(appPackage)
                if app_descriptions is None:
                    app_descriptions = ''
                self_dependency_feature = bert.encode(app_descriptions).reshape(1, -1)
                # api descriptions
                inconsist_api_list = []
                for index, api_desc in enumerate(api_desc_list):
                    visual_dependency_score = consist_visual_context_by_clipsim(new_gui, api_desc, clip_sim)[0][0]
                    api_desc_feature = bert.encode(api_desc).reshape(1, -1)
                    # calculate similarity
                    self_api_score = cosine_similarity(self_dependency_feature, api_desc_feature)[0][0]
                    # sour_score_list = [visual_dependency_score,self_api_score]
                    sour_score_list = [self_api_score, visual_dependency_score]
                    combined_score = calculate_combined_score(sour_score_list)
                    print(date, 'visual, app desc, combine ', visual_dependency_score, self_api_score, combined_score)
                    if combined_score < 0.5:
                        inconsist_api_list.append(api_name_list[index])
                        print('Actual: Incosistency')
                    else:
                        print('Actual: Cosistency')
                # dump inconsist api list
                if os.path.exists(date + '/False.txt'):
                    print('current directory: InConsistency')
                else:
                    print('current directory: Consistency')
                with open(date + '/inconsist_api.pkl', 'wb') as f:
                    pickle.dump(inconsist_api_list, f)
                # print(date,' fewer files inconsist api dumped')
    print('finished')

if __name__ == '__main__':
    # 1.确保monitoring下有api的描述信息
    analysis()