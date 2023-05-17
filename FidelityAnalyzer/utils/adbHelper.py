import os
import json
import numpy as np
import os
import time
import subprocess
import re
from PIL import Image
import io
# from config import REPLAY_RESOLUTION_X,REPLAY_RESOLUTION_Y

def call_adb(command, deviceId = None):
    command_result = ''
    if deviceId is None:
        command_text = 'adb %s' % command
    else:
        command_text = 'adb -s %s %s' % (deviceId, command)
    # results = os.popen(command_text, "r")
    with subprocess.Popen(command_text,shell=True,stdout=subprocess.PIPE,bufsize=-1) as p:
        results = os._wrap_close(io.TextIOWrapper(p.stdout), p)
        while 1:
            line = results.readline()
            if line == '':
                break
            command_result += line
        # results.close()
        return command_result

def checkPackageInstall(pkName):
    result = call_adb('shell pm list package | grep %s' % pkName)
    result = result.replace('\r\n', '').strip()
    if result == '':
        return False
    else:
        packageName = result[8:]  #8 is length of package:
        if pkName in packageName:
            return True
        else:
            return False

def clear(packageName):
    result = call_adb("shell pm clear %s" % packageName)
    return result

def force_stop(package):
    # adb shell am force-stop <package>
    call_adb('shell am force-stop %s' % package)

def start_activity2(activity):
    # adb shell am start -n <activity>
    call_adb('shell am start -n %s' % activity)
    # call_adb('shell am start -W %s' % activity)

def start_activity(activity):
    proc = subprocess.Popen('adb shell am start -n ' + activity, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=-1)
    result = os._wrap_close(io.TextIOWrapper(proc.stdout), proc)
    result.close()
    # print('---start activity now---')

def uninstallApp(pkName):
    call_adb('uninstall %s' % pkName)

def checkIfInstalled(pkName,activityName,application):
    while True:
        ret = checkPackageInstall(pkName)
        if ret is True:
            # print('%s has installed..' % pkName)
            # clear(pkName)
            # force_stop(pkName)
            time.sleep(0.5)
            start_activity(pkName+'/'+activityName)
            time.sleep(0.5)
            break
        else:
            print('sleep 0.5s to wait %s install finish' % pkName)
            call_adb('install -r %s',application)
            time.sleep(0.5)
    time.sleep(3)

def mkdirs(dirPath):
    result = None
    #mkdir if dir is not exist
    if ls(dirPath) is False:
        result = call_adb("shell mkdir -p %s" % dirPath)
    return result

def ls(path):
    result = call_adb("shell ls -l %s" % path)
    if "No such file or directory" in result:
        return False
    else:
        return True

def pull(remote,local):
    result = None
    if ls(remote) is True:
        result = call_adb("pull %s %s" % (remote, local))
    return result

def delete(filePath):
    result = call_adb("shell rm -rf %s" % filePath)
    return repr(result)

def is_valid(file):
    valid = True
    try:
        Image.open(file).load()
    except OSError:
        valid = False
    return valid

def screencap(saveFile):
    time.sleep(2)
    tmpDir = '/data/local/tmp'
    mkdirs(tmpDir)
    remoteFile = tmpDir+'/'+'phoneHomePage.png'
    call_adb("shell screencap -p %s" % remoteFile)
    pull(remoteFile, saveFile)
    delete(remoteFile)
    # time.sleep(2)
    valid = is_valid(saveFile)
    if not valid:
        patch = Image.new("RGBA", (REPLAY_RESOLUTION_X, REPLAY_RESOLUTION_Y), "#FFFFFF")
        patch.save(saveFile)

def run(cmd):
    return subprocess.check_output(('adb %s' % (cmd)).split(' '))

def dump_layout(dump_file):
    try:
        tmpDir = '/data/local/tmp'
        mkdirs(tmpDir)
        remoteFile = tmpDir + '/' + 'hierarchy.xml'
        # run('shell uiautomator dump %s' % remoteFile)
        call_adb('shell uiautomator dump %s' % remoteFile)
        pull(remoteFile, dump_file)
        delete(remoteFile)
        with open(dump_file, "r",encoding='utf-8') as f:
            xml = f.read()
        os.remove(dump_file)
    except IOError as e:
        print('exception')
        xml = dump_layout(dump_file)
    return xml


def get_current_activity():
    shell_activity_name = "adb shell dumpsys window windows | grep -E 'mCurrentFocus|mFocusedApp'"
    # stdout = call_adb(shell_activity_name)

    process = subprocess.Popen(
        shell_activity_name, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    stdout = (
        process.communicate(timeout=None)[0]
            .strip()
            .decode(errors="backslashreplace")
    )

    activity_regex = re.compile('^\\s*mCurrentFocus.+\\{.+\\s([^\\s\\/]+)\\/([^\\s]+)\\b',re.X)
    current_activity = activity_regex.match(stdout).group(2)
    return current_activity