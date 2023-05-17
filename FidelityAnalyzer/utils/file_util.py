import pickle

def readPklFile(file_path):
    with open(file_path, 'rb') as f:
        content = pickle.load(f)
    return content

def writePklFile(file_path,content):
    with open(file_path, 'wb') as f:
        pickle.dump(content, f)