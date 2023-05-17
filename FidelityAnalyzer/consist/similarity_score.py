def calculate_combined_score(sour_score_list):
    # sour_score_list = [visual_dependency_score,context_api_score,view_api_score,self_api_score]
    score_norm_list = []
    for item_score in sour_score_list:
        # if item_score < 0.6:
        #     score_norm_list.append(0)
        # else:
        #     score_norm_list.append(item_score)
        score_norm_list.append(item_score)
    # sort
    score_norm_list.sort(reverse=True)
    combined_score = 0
    for index,item in enumerate(score_norm_list):
        combined_score += item * pow(0.7, index+1)
    return combined_score