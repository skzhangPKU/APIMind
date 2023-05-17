from sklearn.preprocessing import LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import FunctionTransformer
from utils.file_util import readPklFile
from utils.evaluation import Score
from warnings import simplefilter
from utils.data import split_set
import random
import numpy as np
import datetime
simplefilter(action='ignore', category=FutureWarning)
np.random.seed(1)
random.seed(1)

def to_dense(x):
    return x.todense()

def train():
    # load dataset
    data, raw_labels = readPklFile('samples/label_dataset.pkl')
    train_data, test_data = split_set(data,raw_labels,0.2,shuffle=True)
    training_samples_raw, training_labels_raw = zip(*train_data)
    test_samples_raw, test_labels_raw = zip(*test_data)
    print('training sample number is ',len(training_samples_raw))
    print('test sample number is ', len(test_samples_raw))
    # samples finished
    label_encoder = LabelEncoder().fit(training_labels_raw)
    training_labels = label_encoder.transform(training_labels_raw)
    # model
    clf = Pipeline([
        ("vectorizer", CountVectorizer(stop_words="english",
                                       ngram_range=(1, 2))),
        ("tfidf", TfidfTransformer()),
        ("to_dense", FunctionTransformer(to_dense,
                                         accept_sparse=True)),
        ("gbc", GradientBoostingClassifier(n_estimators=200, random_state=5000))
    ])
    clf.fit(training_samples_raw, training_labels)

    test_samples = data
    test_labels = np.array(raw_labels)
    test_prediction = clf.predict(test_samples)
    print(test_prediction)
    print(test_labels)
    scores = Score._calculate_scores(test_prediction,test_labels)
    Score._logging_scores(scores)

if __name__ == '__main__':
    start_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(start_time)
    train()
    end_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(end_time)
