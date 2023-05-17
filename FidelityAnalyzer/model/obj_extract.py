from model.extract_tuples import findSVOs, nlp
tokens = nlp("Seated in Mission Control, Chris Kraft neared the end of a tedious Friday afternoon as he monitored a seemingly interminable ground test of the Apollo 1 spacecraft.")
svos = findSVOs(tokens)
print(svos)