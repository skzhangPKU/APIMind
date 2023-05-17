import pickle

def consist_self_dependency(pkName):
    with open('appDescriptions/'+pkName+'.pkl','rb') as f:
        description = pickle.load(f)
    return description