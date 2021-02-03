import random


class Replicant:
    """The actual agent of this simulation. Tries to reproduce as much as possible."""

    def __init__(self):
        self.attribute = random.uniform(-1, 1)
        self._name = 'R' + str(self.attribute)[2:8]
    
    def __str__(self):
        return '{self.__class__.__name__} {self.device}'.format(self=self)
