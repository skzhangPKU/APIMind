#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
import scipy.spatial.distance
from gensim.models import KeyedVectors

# from pattern.singleton import Singleton


class EmbeddingModel(object):
    # __metaclass__ = Singleton

    def __init__(self, path=None):
        self._model = None
        if path:
            self._model = KeyedVectors.load(path)
        self.dimensions = self._model.vector_size

    def load(self, path):
        self._model = KeyedVectors.load(path)
        return self

    def vector(self, word):
        if word in self._model.vocab:
            vector = self._model[word]
            return vector
        else:
            return None

    def similarity(self, word1, word2):
        if word1 in self._model.vocab and word2 in self._model.vocab:
            return self._model.similarity(word1, word2)
        else:
            return 0

    def similar(self, text1, text2):
        words1 = text1.split(" ")
        words2 = text2.split(" ")
        v1 = [self.vector(i) for i in words1]
        v2 = [self.vector(i) for i in words2]
        v1 = [i for i in v1 if i is not None]
        v2 = [i for i in v2 if i is not None]
        if not v1 or not v2:
            return 0
        else:
            v1_sum = np.zeros(self.dimensions)
            for i in v1:
                v1_sum += i
            v2_sum = np.zeros(self.dimensions)
            for i in v2:
                v2_sum += i
            return 1 - scipy.spatial.distance.cosine(v1_sum, v2_sum)


if __name__ == '__main__':

    model = EmbeddingModel(path=Values.word2vec_model_path)
    print(model.similar("input password", "login"))
    print(model.similarity("password", "login"))
    print(model.vector("password"))
