class Behavior(object):
    def __init__(self, pairs=None, actions=None, resources=None):
        self.pairs = list(pairs) if pairs else []
        self.actions = list(actions) if actions else []
        self.resources = list(resources) if resources else []

    def __add__(self, other):
        pairs = set(self.pairs + list(other.pairs))
        actions = set(self.actions + list(other.actions))
        resources = set(self.resources + list(other.resources))
        return Behavior(pairs=pairs, actions=actions, resources=resources)