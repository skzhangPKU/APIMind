import pickle

def get_api_descriptions(sens_api):
    with open('monitoring/permissions_api.pkl', 'rb') as f:
        api_des_dict = pickle.load(f)
    if sens_api in api_des_dict:
        api_des_list = api_des_dict[sens_api]
        self_description, comment_description = api_des_list[0], api_des_list[1]
        return self_description+' '+ comment_description
    else:
        class_name, function_name = sens_api.rsplit('.', 1)
        for item in api_des_dict.keys():
            if class_name in item and function_name in item:
                api_des_list = api_des_dict[item]
                self_description, comment_description = api_des_list[0], api_des_list[1]
                return self_description+' '+ comment_description
    return ''