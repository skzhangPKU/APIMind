# -*- coding: utf-8 -*-
import sys
import uuid
import requests
import hashlib
import time

import time


def encrypt(signStr):
    hash_algorithm = hashlib.sha256()
    hash_algorithm.update(signStr.encode('utf-8'))
    return hash_algorithm.hexdigest()


def truncate(q):
    if q is None:
        return None
    size = len(q)
    return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]


def do_request(data):
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    YOUDAO_URL = 'https://openapi.youdao.com/api'
    return requests.post(YOUDAO_URL, data=data, headers=headers)


def translate(q):
    q = q.replace('😂','')
    data = {}
    data['from'] = 'zh-CHS'
    data['to'] = 'EN'
    data['signType'] = 'v3'
    curtime = str(int(time.time()))
    data['curtime'] = curtime
    salt = str(uuid.uuid1())
    APP_KEY = '45ecbe778585a674'
    APP_SECRET = 'TrcFyZVp6VDZ85GJI1eTgjND6N8dOz2w'
    signStr = APP_KEY + truncate(q) + salt + curtime + APP_SECRET
    sign = encrypt(signStr)
    data['appKey'] = APP_KEY
    data['q'] = q
    data['salt'] = salt
    data['sign'] = sign
    data['vocabId'] = "您的用户词表ID"

    response = do_request(data)
    res_json = response.json()
    # try:
    #     tmp = res_json['translation'][0]
    # except:
    #     pass
    return res_json['translation'][0]

if __name__ == '__main__':
    translate('双十一')