import numpy as np
import random
from replicant import Replicant


class Species:
    """A vehicle is a set of Replicants, fighting for survival together."""

    def __init__(self, replicants):
        self.replicants = replicants
        self.fitness = self.fitness()
        
        # derive six hex digits from the fitness for a unique name and color
        six_hex_digits = hex(int(self.fitness * 16 ** 8))[2:8]
        self._name = 'V' + six_hex_digits
        self.color = '#' + six_hex_digits

    def __eq__(self, other):
        return set(self.replicants) == set(other.genome)
    
    def __hash__(self):
        if self.replicants ==[]:
            return 0
        else:
            return hash(tuple(sorted(self.replicants))) # sorted-> hash is independent of order

    def fitness(self):
        """New idea: implement highly nonlinear fitness function -> use a hash."""
        return hash(self)

        # """Determine the fitness of the vehicle, by how well its genome solve the knapsack problem."""
        # list_of_replicant_attributes = [r.attribute for r in self.genome]
        # return knapsack.fitness(list_of_replicant_attributes)

    def insertion_mutation(self):
        """Return a mutant of self, with one additional random Replicant."""

        new_replicants = self.replicants.copy()  # clone
        new_replicants.append(Replicant())  # add a random gene
        return Species(new_replicants)

    def deletion_mutation(self):
        """Return a mutant of self, with one random gene removed."""

        if len(self.replicants) == 0:  # if the species is the "null species" there are no genes to delete.
            return self
        else:
            # pick a random gene and delete it
            new_replicants = self.replicants.copy()  # clone
            
            new_replicants.pop(random.randint(0, len(self.replicants) -1))  # pop a random gene
            return Species(new_replicants)
