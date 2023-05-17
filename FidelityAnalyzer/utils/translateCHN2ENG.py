from utils.translate import send_request

def translate2eng(chn_str):
    chn_strip = chn_str.strip()
    if chn_strip != '':
        chn_strip = send_request(chn_strip)
    return chn_strip