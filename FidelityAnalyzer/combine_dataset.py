from utils.general_util import scan_file
from utils.file_util import readPklFile,writePklFile

def combine_single_samples():
    single_samples_path = scan_file('samples/single_samples/', includeFile=True)
    training_samples = []
    training_labels = []
    for single_sample_path in single_samples_path:
        single_sample_desc_list, single_sample_label_list = readPklFile(single_sample_path)
        for index, desc in enumerate(single_sample_desc_list):
            training_samples.append(desc)
            training_labels.append(single_sample_label_list[index])
    writePklFile('samples/label_dataset.pkl', [training_samples, training_labels])
    print('finished')

def read_training_samples():
    samples = readPklFile('samples/label_dataset.pkl')
    print('test')

if __name__ == '__main__':
    # combine_single_samples()
    read_training_samples()