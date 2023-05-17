import os
import sys
from androguard.misc import AnalyzeAPK
from androguard.core.androconf import load_api_specific_resource_module

path = r"apps"
out_path = r"out"
files = []
path_list = os.listdir(path)
path_list.sort()
for name in path_list:
    if os.path.isfile(os.path.join(path, name)):
        files.append(name)

def main():
    for apkFile in files:
        file_name = os.path.splitext(apkFile)[0]
        print(apkFile)
        out = AnalyzeAPK(path + '/' + apkFile)
        a = out[0]
        d = out[1]
        dx = out[2]

        for meth in dx.classes['Ljava/io/File;'].get_methods():
            print("usage of method {}".format(meth.name))
            for _, call, _ in meth.get_xref_from():
                print("  called by -> {} -- {}".format(call.class_name, call.name))

if __name__ == '__main__':
    main()