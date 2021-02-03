import numpy as np
import random

class Species:
    """A vehicle is a set of Replicants, fighting for survival together.
    They are represented in a numpy vector.
    0 -> gene not contained.
    1 -> gene contained."""

    def __init__(self, genome: np.ndarray, fitness: float):
        self.fitness = fitness
        self.genome = genome
        self.len = len(self.genome)
         # derive six hex digits from the fitness for a unique name and color
        six_hex_digits = hex(int(self.fitness * 16 ** 8))[2:8]
        self._name = 'V' + six_hex_digits
        self.color = '#' + six_hex_digits

    def __eq__(self, other):
        return np.array_equal(self.genome, other.genome)
    
    def __hash__(self):
        return str(self.genome)

    def mutated_genome(self):
        """Select a random index of the gene array, copy the array and return,
        a mutant with one bit of the array flipped.
        Can insert(0->1) or delete (1->0) a replicator."""
        loc = random.randrange(0, self.len)
        new_genome = self.genome.copy()
        new_genome[loc] = not new_genome[loc]
        return new_genome
