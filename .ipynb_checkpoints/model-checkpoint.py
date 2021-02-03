from species import Species
import networkx as nx
import random


# The model class will consist of:
#     - a graph (networkx)
#     - a state, that is a list/array, that maps integers(i.e. nodes) to species
#     - a step function
#         - interaction step
#         - mutation step
#     - a display function

class Model:
    """The class used for a whole simulation run.
    Requires:   - Graph,
                - surrender_option_on = True/False
                - uncertainty
                - mutation ratio
                """

    def __init__(self, Graph: nx.Graph, mutation_ratio: int, uncertainty: float, surrender_option_on: bool):
        self.Graph = Graph
        self.N = Graph.number_of_nodes()
        self.State = [Species([])] * self.N  # The state will contain a mapping of nodes to the species that currently lives on it.
        self.mutation_ratio = mutation_ratio
        self.uncertainty = uncertainty
        self.surrender_option_on = surrender_option_on
        self.surrender_fight_ratio = None

    def step(self):
        """Advances the model by one step / time unit.
        Consists of mutating and interacting.
        Ration of interaction_step/mutation_step determined by mutation_ratio."""
        self.mutation_step()
        for i in range(0, self.mutation_ratio):
            self.interaction_step()

    def mutation_step(self):
        """Mutates two random nodes. One deletion, and one insertion."""
        self.d_mutate()
        self.i_mutate()

    def d_mutate(self):
        """Apply a deletion mutation to a random node."""
        # pick a random node in the graph, i.e. an integer
        node = random.randint(0, self.N - 1)
        # get the species currently living on that node
        species = self.State[node]
        # mutate the species and add it to the node in question.
        self.State[node] = species.deletion_mutation()

    def i_mutate(self):
        """Apply an insertion mutation to a random node."""
        # pick a random node in the graph, i.e. an integer
        node = random.randint(0, self.N - 1)
        # get the species currently living on that node
        species = self.State[node]
        # mutate the species and add it to the node in question.
        self.State[node] = species.insertion_mutation()

    def interaction_step(self):
        """Chooses a random node and has it interact with one of its neighbors.
        We chose to uniformly sample nodes instead of edges, since we think,
        that it makes sense that nodes with few neighbors interact more with each of them.
        """
        # pick a random node
        a = random.randint(0, self.N - 1)
        # get neighbors
        neighbors = [i for i in self.Graph[a]]
        # randomly select on neighbor
        b = random.choice(neighbors)

        # if the same species lives on both nodes, nothing happens, if not they interact
        # interact: one replaces the other, either violently or consensually
        if not self.State[a] == self.State[b]:

            if self.State[a].fitness > self.State[b].fitness:
                underdog_node = b
                favorite_node = a
                underdog = self.State[b]
                favorite = self.State[a]
            else:
                underdog_node = a
                favorite_node = b
                underdog = self.State[a]
                favorite = self.State[b]

            # now the genes in the underdog vote on wether to surrender or not.
            replicant_vote = [self.vote_surrender(i, underdog, favorite, underdog_node) for i in underdog.genome]

            majority_vote = replicant_vote.count(True) > 0.5 * len(replicant_vote)

            # print(underdog._name , " vs ", favorite._name , ": genome voted: ", replicant_vote)
            # majority vote is determined by 0.5. Cutoff may be changed, depending on how strong the veto vote is.
            # i.e. how strongly a "surrender"-vote is weighted compared to a "fight"-vote.

            if majority_vote and self.surrender_option_on:
                # voted for surrender!
                # print(underdog._name, " surrendered to ", favorite._name," Fitness:", underdog.fitness, " -> ", favorite.fitness)
                self.State[underdog_node] = favorite
                self.State[favorite_node] = favorite

            else:
                winner = self.fight(underdog, favorite)
                # print(underdog._name, " fought ", favorite._name, ". Winner = ", winner._name)

                # winner takes all: winner now replaces the loser on his node.
                self.State[underdog_node] = winner
                self.State[favorite_node] = winner

    def fight(self, a: Species, b: Species) -> Species:
        """A species a and b fight. Return the winner. Probabilistic"""
        p_a_wins = self.p_win(a, b)
        if p_a_wins > random.random():
            return a
        else:
            return b

    def p_win(self, a: Species, b: Species) -> float:
        """Returns the probability that a wins against b. Deterministic.
        Optimisation with memoisation is possible!"""

        return a.fitness / (a.fitness + b.fitness)

    def vote_surrender(self, replicant, underdog, favorite, underdog_node):
        """Does the gene in question (element of underdog) want to fight
        the favorite, or surrender?
        Parameters the gene is allowed to consider:
        1. fitness of his species (aka underdog)
        2. fitness of the species he is interacting with (aka favorite)
        3. fitness of his immediate neighbors (underdog.neighbors())
        4. uncertainty parameter.
        MEMOISABLE!
        """
        replicant_thinks_its_contained = replicant in favorite.genome  # is it contained or not?
        # Confusion step:
        if random.random() < self.uncertainty:
            replicant_thinks_its_contained = not replicant_thinks_its_contained  # flip it with P=uncertainty!

        # the other very important information for risking surrender, is the surrounding species.
        neighbor_nodes = [i for i in self.Graph[underdog_node]]  # list of neighbors
        neighbor_species = [self.State[i] for i in neighbor_nodes]
        # possibly remove the two combattants from the list? TODO ToDo

        # probability that the underdog wins agains a random neighbor
        # sum over all neighbors, with exception of the favorite.
        # also sum over other underdog and favorite nodes.

        p_u_beats_n = sum([self.p_win(underdog, n) for n in neighbor_species]) / len(neighbor_species)

        # probability that the favorite wins against a neighbor
        p_f_beats_n = sum([self.p_win(underdog, n) for n in neighbor_species]) / len(neighbor_species)

        # probability that the underdog wins against the favorite
        p_u_beats_f = self.p_win(underdog, favorite)

        if replicant_thinks_its_contained:  # gene thinks it is contained, but it knows it could be wrong and
            # considers pro and contra

            p_cont = 1 - self.uncertainty

            p_survive_if_surrender = p_cont * p_f_beats_n

            p_survive_if_fight = p_u_beats_f * p_u_beats_n + (1 - p_u_beats_f) * p_cont * p_f_beats_n

            return p_survive_if_surrender > p_survive_if_fight

        else:  # gene thinks it isn't contained, but it knows that it could be wrong

            # probability that gene survives against neighborhood, given that it surrenders
            # on the offchance that it is contained after all.
            p_cont = self.uncertainty

            p_survive_if_surrender = p_cont * p_f_beats_n

            p_survive_if_fight = p_u_beats_f * p_u_beats_n + (1 - p_u_beats_f) * p_cont * p_f_beats_n

            return p_survive_if_surrender > p_survive_if_fight
