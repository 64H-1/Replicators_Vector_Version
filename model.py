from species import Species
import networkx as nx
import random
import numpy as np

# The model class will consist of:
#     - a graph (networkx)
#     - a state, that is a list/array, that maps integers(i.e. nodes) to species
#     - a step function
#         - interaction step
#         - mutation step
#     - a display function


def gene_decide(p_cont, p_u_beats_n, p_f_beats_n, p_u_beats_f) -> bool:
    
    # survival upon surrender: contained and f is successful in the next interaction.
    p_survive_if_surrender = p_cont * p_f_beats_n
    
    # survival if fight: win and survive the next round, or lose, be contained, AND win the next round as a gene of "favorite"
    p_survive_if_fight = p_u_beats_f * p_u_beats_n + (1 - p_u_beats_f) * p_cont * p_f_beats_n
    
    return p_survive_if_surrender > p_survive_if_fight


def p_win(a: Species, b: Species) -> float:
    """Returns the probability that a wins against b in a fight."""
    # print("p_win called for Species", a, b)
    if a.fitness == b.fitness:
        return 0.5
    else:
        return a.fitness / (a.fitness + b.fitness)


class Model:
    """The class used for a whole simulation run.
    Requires:   - Graph,
                - surrender_option_on = True/False
                - uncertainty
                - mutation ratio
                """

    def __init__(self, Graph: nx.Graph, coupling_tensor: np.ndarray, mutation_rate: int, uncertainty: float, surrender_option_on: bool): #F: isn't mutation rate a float in [0,1) ?
    
        self.coupling_tensor = coupling_tensor
        # check if coupling tensor is square
        if not all([coupling_tensor.shape[0] == i for i in coupling_tensor.shape]): #F: Replace by the below, saves the iteration.
        #F: if(coupling_tensor.shape[0]!=coupling_tensor.shape[1])
            raise Exception("Coupling tensor is not square.")
        self.genome_len = coupling_tensor.shape[0]

        self.Graph = Graph
        self.N = Graph.number_of_nodes()
        self.empty_species = Species(np.zeros(self.genome_len, dtype=bool), self.fitness(np.zeros(self.genome_len, dtype=bool))) #initialise the State with a species with empty genomes
        self.State = [self.empty_species] * self.N  # The state will contain a mapping of nodes to the species that currently lives on it.


        self.mutation_rate = mutation_rate
        self.uncertainty = uncertainty
        self.surrender_option_on = surrender_option_on

    def fitness(self, genome):
        f = 0 #F: replace loop with np.dot construction --> saves run-time
        for i in range(0, self.genome_len):
            for j in range(0, self.genome_len):
                f += genome[i] * genome[j] * self.coupling_tensor[i][j]
        # f = np.dot(genome,np.dot(self.coupling_tensor,genome))

        # Problem: we need negative coupling coefficients, because otherwise
        # more genes are simply better, and optimising is trivial. #F: Alternatively regularise (i.e. penalise having too many genes by subtracting lp-norm of genome vector).
        # In a biological context this might correspond to limitations on the organism (or maybe something else, who knows?).

        # at the same time negative fitness is no bueno for the p_win() formula:
        # p(a wins over b) = f_a / (f_a + f_b)
        # so: we will use exp(f) to map (-inf,inf) -> (0, inf) so that we no longer have negative values. #F: this implies that fitness 

        # In order to simulate a population already near optimum/equilibrium,
        # we will add a large constant factor to the fitness.
        # We expect that this will emphasise the difference between, surrender_on and surrender_off
        const = 999999999 #F: Maybe the factor should depend somehow on the coupling matrix, e.g. a 
        # constant times its exp of its Frobenius-norm or 2-operator norm (?), as we want exp(f) to be small compared to const, right?
        return const + np.exp(f)

    def step(self):
        """Advances the model by one step / time unit.
        Consists of mutating and interacting.
        Ration of interaction_step/mutation_step determined by mutation_ratio."""
        self.interaction_step()
        if random.random() < self.mutation_rate: # probabilistically mutate, with chance mutation_rate.
            self.mutation_step()
            

    def mutation_step(self):
        """Mutates a random node."""
        # pick a random node in the graph, i.e. an integer
        node = random.randint(0, self.N - 1)
        # get the species currently living on that node
        species = self.State[node]
        # mutate the species and add it to the node in question.
        new_genome = species.mutated_genome()
        self.State[node] = Species(new_genome, self.fitness(new_genome))

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
            # print(self.State[a], "is unequal", self.State[b])

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

            # first: determine the number of genes in the underdog genome
            num_genes = np.sum(underdog.genome)

            if num_genes == 0: # if the underdog is an empty node, simply replace him.
                self.State[underdog_node] = favorite
                self.State[favorite_node] = favorite

            else:

                # determine the number of genes contained in both the underdog and the favorite genome
                num_common_genes = np.sum(underdog.genome * favorite.genome)

                # Probability that a randomly chosen underdog gene is contained in the favorites genome
                p_gene_cont = num_common_genes/num_genes

                # Adding CONFUSION: uncertainty
                # Probability that a randomly chosen underdog gene THINKS (!!) it is contained in the favorites genome
                p_gene_thinks_cont = p_gene_cont * (1 - self.uncertainty) + (1- p_gene_cont) * self.uncertainty


                # the other very important information for risking surrender, is the surrounding species.
                neighbor_species = [self.State[i] for i in self.Graph[underdog_node]]  # list of neighbors
                # possibly remove the two combatants from the list? TODO ToDo

                # probability that the underdog wins against a random neighbor
                # sum over all neighbors, with exception of the favorite.
                # also sum over other underdog and favorite nodes.

                p_u_beats_n = sum([p_win(underdog, n) for n in neighbor_species]) / len(neighbor_species)

                # probability that the favorite wins against a neighbor
                p_f_beats_n = sum([p_win(underdog, n) for n in neighbor_species]) / len(neighbor_species)

                # probability that the underdog wins against the favorite
                p_u_beats_f = p_win(underdog, favorite)

                # if we now randomly pick an underdog gene that gets to choose whether to surrender or not, what does that gene know?
                # it knows with uncertainty whether it is contained in the opponent or not.
                # it knows that uncertainty.
                # it knows its present genomes chance to survive the next interaction with a neighbor.
                # it knows the favorites chance to survive the next interaction with a neighbor.
                # So, in order to surrender, the gene must think it's survival chances are better upon surrender.



                #Firste let's determine if the gene thinks its contained or not.

                if p_gene_thinks_cont > random.random():
                    #Gene thinks it's contained, now let's see how it estimates, its survival chances given that information.

                    gene_decision = gene_decide((1-self.uncertainty), p_u_beats_n, p_f_beats_n, p_u_beats_f)
                else:
                    # Gene thinks it isn't contained, but knows it migh still be, with prob = uncertainty.
                    gene_decision = gene_decide((self.uncertainty), p_u_beats_n, p_f_beats_n, p_u_beats_f)

                # gene has decided, to surrender or not, apply the consequences to the model state
                if gene_decision and self.surrender_option_on:
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
        p_a_wins = p_win(a, b)
        if p_a_wins > random.random():
            return a
        else:
            return b
