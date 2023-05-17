import hashlib
import random
import time
import requests
import re
from bs4 import BeautifulSoup
from faker import Faker
from utils.youdao_util import translate


def send_request(content):
    parse_result = translate(content)
    return parse_result

def send_request_window(content):#send_request_window
    salt = str(round(time.time() * 1000)) + str(random.randint(0, 9))
    data = "fanyideskweb" + content + salt + "Tbh5E8=q6U3EXe+&L[4c@"
    sign = hashlib.md5()
    sign.update(data.encode("utf-8"))
    sign = sign.hexdigest()
    url = 'http://fanyi.youdao.com/translate_o?smartresult=dict&smartresult=rule'
    ua = Faker().user_agent()
    headers = {
        'User-Agent': ua,
        'Cookie': 'OUTFOX_SEARCH_USER_ID=-1927650476@223.97.13.65;',
        'Host': 'fanyi.youdao.com',
        'Origin': 'http://fanyi.youdao.com',
        'Referer': 'http://fanyi.youdao.com/'
        # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.146 Safari/537.36',
    }
    data = {
        'i': str(content),
        'from': 'AUTO',
        'to': 'AUTO',
        'smartresult': 'dict',
        'client': 'fanyideskweb',
        'salt': str(salt),
        'sign': str(sign),
        'version': '2.1',
        'keyfrom': 'fanyi.web',
        'action': 'FY_BY_REALTlME',
    }
    # patent = '"tgt":"(.*?)"}'
    res = requests.post(url=url, headers=headers, data=data).json()
    # res2 = requests.post(url=url, headers=headers, data=data)
    # data = re.findall(patent, res2.text)
    return res['translateResult'][0][0]['tgt']


def send_request_mobile(content):#send_request
    # time.sleep(2)
    salt = str(round(time.time() * 1000)) + str(random.randint(0, 9))
    data = "fanyideskweb" + content + salt + "Tbh5E8=q6U3EXe+&L[4c@"
    sign = hashlib.md5()
    sign.update(data.encode("utf-8"))
    sign = sign.hexdigest()
    url = 'https://m.youdao.com/translate'
    ua = Faker().user_agent()
    headers = {
        'Cookie': 'OUTFOX_SEARCH_USER_ID=-1135780632@10.108.162.139;',
        'Host': 'm.youdao.com',
        'Origin': 'https://m.youdao.com',
        'Referer': 'https://m.youdao.com/translate',
        # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.146 Safari/537.36',
        # 'User-Agent':'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36',
        'User-Agent': ua
    }
    data = {
        'inputtext': str(content),
        # 'type': 'AUTO'
        'type':'ZH_CN2EN'
    }
    response = requests.post(url=url, headers=headers, data=data)
    con = response.content.decode('utf-8')
    soup = BeautifulSoup(con, "html.parser")
    parse_result = soup.select("#translateResult")[0].text.strip()
    return parse_result

if __name__ == '__main__':
    content = '隐私政策'
    result = send_request(content)
    print(result)