import logging
import string

import nltk.corpus
import nltk.tree
import simplejson as json
from stanford_corenlp.behaviors import Behavior
# import strfilters.tokenizer

def get_common_prefix(str1, str2):
    min_len = min(len(str1), len(str2))
    for i in range(min_len):
        if str1[i] == str2[i]:
            continue
        else:
            return str1[:i]
    return str1[:min_len]

def parse_behaviors(tree):
    stopwords = nltk.corpus.stopwords.words("english") + (
        ["-LRB-", "-RRB-"]) + list(string.punctuation)
    leaf_pos = tree.treepositions("leaves")

    nn_pos = [pos for pos in leaf_pos if "NN" in (
        tree[pos[:len(pos) - 1]].label()) and tree[pos] not in stopwords]
    vb_pos = [pos for pos in leaf_pos if "VB" in (
        tree[pos[:len(pos) - 1]].label()) and tree[pos] not in stopwords]

    resources = set([tree[pos] for pos in nn_pos])
    actions = set([tree[pos] for pos in vb_pos])

    nn_seq = ["".join(map(str, pos)) for pos in nn_pos]
    vb_seq = ["".join(map(str, pos)) for pos in vb_pos]
    vp_seq = []
    np_seq = []
    noun_phrases = {}
    for pos in tree.treepositions():
        if pos in leaf_pos:
            continue
        if "VP" in tree[pos].label():
            vp_seq.append("".join(map(str, pos)))
        if "NP" in tree[pos].label():
            np_seq.append("".join(map(str, pos)))
            pos_tagged_wrods = tree[pos].pos()
            if len(pos_tagged_wrods) < 2:
                continue
            for i in range(len(pos_tagged_wrods)):
                if i >= len(pos_tagged_wrods) - 1:
                    continue
                if ("NN" or "PRP") in pos_tagged_wrods[i][1] and "NN" in (
                        pos_tagged_wrods[i + 1][1]):
                    noun_phrase = pos_tagged_wrods[i][0] + "_" + (
                        pos_tagged_wrods[i + 1][0])
                    noun_phrases[noun_phrase] = "".join(map(str, pos))

    behavior_pairs = []
    # bi-gram verb + noun
    for i, nn in enumerate(nn_seq):
        for j, vb in enumerate(vb_seq):
            prefix = get_common_prefix(nn, vb)
            if prefix in vp_seq:
                noun = tree[nn_pos[i]]
                verb = tree[vb_pos[j]]
                behavior_pairs.append(verb + " " + noun)

    # tri-gram verb + phrase
    for phrase, pos in noun_phrases.items():
        for j, vb in enumerate(vb_seq):
            prefix = get_common_prefix(pos, vb)
            if prefix in vp_seq:
                verb = tree[vb_pos[j]]
                behavior_pairs.append(verb + " " + phrase)

    behavior_pairs_set = set([])
    for pair in set(behavior_pairs):
        action, resource = pair.split(" ")
        behavior_pairs_set.add(action + " " + resource.replace("_", " "))

    noun_phrase = list(set([p.replace("_", " ") for p in
                            noun_phrases.keys()]))

    resources = list(resources) + noun_phrase

    return Behavior(pairs=behavior_pairs_set, actions=actions, resources=resources)
    # return semantic.behavior.Behavior(pairs=behavior_pairs_set, actions=actions, resources=resources)