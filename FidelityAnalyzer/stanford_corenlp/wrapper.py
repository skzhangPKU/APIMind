#!/usr/bin/env python
# -*- coding:utf-8 -*-

import json
import logging
import os.path
import re

import enum
import pexpect
import nltk.tree
from stanford_corenlp.parse_action_resource import parse_behaviors
from functools import reduce
from stanford_corenlp.behaviors import Behavior


class CoreNLPParseFlowState(enum.Enum):
    start = 0
    text = 1
    words = 2
    tree = 3
    dependency = 4
    end = 5


class StanfordCoreNLPWrapper(object):
    """Command-line interaction with Stanford CoreNLP java utilities"""

    _word_pattern = re.compile(r"\[([^\]]+)\]")
    _cr_pattern = re.compile(r"\((\d*),(\d)*,\[(\d*),(\d*)\]\) ->"
                             r" \((\d*),(\d)*,\[(\d*),(\d*)\]\),"
                             r" that is: \"(.*)\" -> \"(.*)\"")

    def __init__(self, classpath=None, Xmx=8192, logger=None):
        """
        Search the jars in the current path and starts with subprocess in
        command line.
        :param classpath: Path to search all jar files related to
        StanfordCoreNLPWrapper.
        :param Xmx: Java Xmx parameter, which stands for maximum memory
        allocation pool size of JVM.
        :param logger: Use a given logger or use "root" logger if None.
        """

        logger = logger or logging.getLogger()

        jars = ["stanford-corenlp-3.7.0.jar",
                "stanford-corenlp-3.7.0-models.jar",
                "joda-time.jar",
                "xom.jar",
                "jollyday.jar"]

        java_cmd = "java"
        Xmx = "-Xmx" + str(Xmx) + "m"
        classname = "edu.stanford.nlp.pipeline.StanfordCoreNLP"

        properties_path = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), "default.properties")
        properties = "-props " + properties_path

        classpath = classpath or os.path.realpath(".")
        for i, jar in enumerate(jars):
            abs_jar_path = os.path.join(classpath, jar)
            if not os.path.exists(abs_jar_path):
                logger.error("Cannot found %s in path \"%s\"" % (
                    jar, classpath))
                raise ValueError("Cannot found %s in path \"%s\"" % (
                    jar, classpath))
            jars[i] = abs_jar_path

        self._start_corenlp_cli = "%s %s -cp %s %s %s" % (
            java_cmd, Xmx, os.pathsep.join(jars), classname, properties)
        # logger.debug(self._start_corenlp_cli)

        self._process = pexpect.spawn(self._start_corenlp_cli)
        self._process.expect("Entering interactive shell.")

    def _parse(self, text):
        # clean up anything leftover
        buffer_size = 4000
        checking_frequency = 0.5
        while True:
            try:
                self._process.read_nonblocking(buffer_size, checking_frequency)
            except pexpect.TIMEOUT:
                break

        self._process.sendline(text)

        result = ""
        while True:
            try:
                result += self._process.read_nonblocking(
                    buffer_size, checking_frequency).decode("utf-8")
                if "\nNLP>" in result:
                    break
            except pexpect.TIMEOUT:
                continue
            except pexpect.EOF:
                break

        try:
            results = self.parse_parser_result(result)
        except Exception as e:
            raise e

        return results

    def parse(self, text):
        """
        This function takes a text string, sends it to the Stanford parser,
        reads in the result, parses the results and returns a list
        with one dictionary entry for each parsed sentence, in JSON format.
        """
        response = self._parse(text)
        return json.dumps(response)

    @staticmethod
    def remove_id(word):
        """
        Removes the numeric suffix from the parsed recognized words.
        e.g. 'word-2' > 'word'
        :param word: a word with suffix
        """
        return word.count("-") == 0 and word or word[0:word.rindex("-")]

    @staticmethod
    def parse_bracketed(s):
        """Parse word features [abc=... def = ...]
        Also manages to parse out features that have XML within them
        """
        word = None
        attrs = {}
        temp = {}
        # Substitute XML tags, to replace them later
        for i, tag in enumerate(re.findall(r"(<[^<>]+>.*<\/[^<>]+>)", s)):
            temp["^^^%d^^^" % i] = tag
            s = s.replace(tag, "^^^%d^^^" % i)
        # Load key-value pairs, substituting as necessary
        for attr, val in re.findall(r"([^=\s]*)=([^=\s]*)", s):
            if val in temp:
                val = temp[val]
            if attr == "Text":
                word = val
            else:
                attrs[attr] = val
        return word, attrs

    @staticmethod
    def parse_parser_result(text):
        """ This is the nasty bit of code to interact with the command-line
        interface of the CoreNLP tools.  Takes a string of the parser results
        and then returns a Python list of dictionaries, one for each parsed
        sentence.
        """
        results = {"sentences": []}
        state = CoreNLPParseFlowState.start
        for line in text.split("\n"):
            line = line.strip()

            if line.startswith("Sentence #"):
                sentence = {'words': [], 'parse_tree': [], 'dependencies': []}
                results["sentences"].append(sentence)
                state = CoreNLPParseFlowState.text

            elif state == CoreNLPParseFlowState.text:
                sentence['text'] = line
                state = CoreNLPParseFlowState.words

            elif state == CoreNLPParseFlowState.words:
                if not line.startswith("[Text="):
                    state = CoreNLPParseFlowState.tree
                    sentence["parse_tree"].append(line)
                for s in StanfordCoreNLPWrapper._word_pattern.findall(line):
                    sentence['words'].append(
                        StanfordCoreNLPWrapper.parse_bracketed(s))

            elif state == CoreNLPParseFlowState.tree:
                if len(line) == 0:
                    state = CoreNLPParseFlowState.dependency
                    sentence['parse_tree'] = " ".join(sentence['parse_tree'])
                else:
                    sentence['parse_tree'].append(line)

            elif state == CoreNLPParseFlowState.dependency:
                if len(line) == 0:
                    state = CoreNLPParseFlowState.end
                else:
                    split_entry = re.split("\(|, ", line[:-1])
                    if len(split_entry) == 3:
                        rel, left, right = map(
                            lambda x: StanfordCoreNLPWrapper.remove_id(x),
                            split_entry)
                        sentence['dependencies'].append(
                            tuple([rel, left, right]))
        return results

    def __del__(self):
        if self._process:
            self._process.terminate()


if __name__ == '__main__':

    parser = StanfordCoreNLPWrapper('./stanford-corenlp-full')
    # print(parser.parse("I like cats"))
    parsed_result = parser.parse("In order to protect your account and use security, you need to authorize us to read your mobile phone number, and you have the right to refuse or cancel the authorization, which will not affect your use of other services provided by us. 3. In order to recommend nearby preferential information, products and services to you on the Koubei homepage, you need to authorize us to obtain your location permission, and you have the right to refuse or cancel the authorization, which will not affect your use of other services provided by us.")
    parsed_json = json.loads(parsed_result)
    parsed_info = parsed_json["sentences"]
    parse_trees = []
    for sentence in parsed_info:
        parse_tree = sentence["parse_tree"]
        parse_trees.append(parse_tree)
    dependencies = [nltk.tree.Tree.fromstring(parse_tree) for (
        parse_tree) in parse_trees]
    behaviors = list()
    for dependency in dependencies:
        behavior = parse_behaviors(dependency)
        behaviors.append(behavior)
    if behaviors:
        x = reduce(lambda x, y: x + y, behaviors)
        print(x)
    else:
        x = Behavior()
    print(x.pairs)
    # print(parser.parse(""))
    # print(parser.parse("test"))
