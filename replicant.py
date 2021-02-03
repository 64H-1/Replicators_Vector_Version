import random


class Replicant:
    """The actual agent of this simulation. Tries to reproduce as much as possible."""

    def __init__(self):
        self.attribute = random.uniform(-1, 1)
        self._name = 'R' + str(self.attribute)[2:8]

    def __eq__(self, other):
        return self.attribute == other.attribute

    def __hash__(self):
        return hash(self.attribute)

    def __lt__(self, other):
        return self.attribute < other.attribute
