from utils import apk_util
from utils.general_util import scan_file
from utils.scraper import PlayStore
import pickle

def get_app_description(pkName):
    play_store = PlayStore(pkName)
    soup = play_store._generate_soup()
    description = play_store._fetch_description_xiaomi(soup)
    with open('appDescriptions/'+pkName+'.pkl', 'wb') as f:
        pickle.dump(description, f)
        print(pkName)
    pass


if __name__ == '__main__':
    apks = scan_file('apps')
    for application in apks:
        coverage_dict_template = {}
        appPackage, appActivity, _ = apk_util.parse_pkg(application, coverage_dict_template)
        try:
            get_app_description(appPackage)
        except:
            print(appPackage+' failure')
            pass