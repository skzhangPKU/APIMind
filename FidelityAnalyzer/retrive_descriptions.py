from utils import apk_util
from utils.scraper import PlayStore
import pickle
from utils.file_util import writePklFile

def get_app_description(pkName):
    play_store = PlayStore(pkName)
    soup = play_store._generate_soup()
    # description = play_store._fetch_description(soup)
    description = play_store._fetch_description_xiaomi(soup)
    writePklFile('appDescriptions/'+pkName+'.pkl',description)
    return description
