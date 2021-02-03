from mesa import Agent
import knapsack
import random
import sys
from replicant import Replicant

class Vehicle(Agent):
    """A vehicle is a set of Replicants, fighting for survival together."""
    def __init__(self, unique_id, model, replicants):
        super().__init__(unique_id, model) # no idea what this bit does, but i think mesa needs it.
        self.replicants = replicants
        self.fitness = self.fitness(replicants)
        self.dead = False
        
    def interact(self):
        """Action stage of the simulation. Vehicle interacts with a neighbor."""
        # Unresoved question: should the turns a node takes be equal for all,
        # or should it be proportional to the connections a node has?
        # i.e. should connections or nodes be the determining factor?
        # It seems that for memetic models, one-node-one-turn makes more sense,
        # since if you have many social contacts, you interact with each of them less frequently. (possibly)
        # How about in biological systems?
        # Seems similar. For instance people reproduce similarly much in mountainous regions and wide plain (with more neighbors).
                
        if self.dead:
            print("ERRROR: ", self.unique_id," was called, even though it is dead!" )
        
        
        # Choose a random neighbor.
        neighborhood = self.model.grid.get_neighborhood(
            self.pos,
            moore=False,
            include_center=False
        )
        
        # select one neighbor.
        neighborPos = self.random.choice(neighborhood)
        # if the neighbor is empty
        if self.model.grid.is_cell_empty(neighborPos):
            
            self.addToGridAndSchedule(self.child(), neighborPos)
            
        else:
            # get the neighbor
            # mesa only lets you do it as a list for some reason... silly
            neighborList = self.model.grid.get_cell_list_contents(neighborPos)
            neighbor = neighborList[0]
            
            if (neighbor.genome == self.replicants):
                # no point in fighting if both are the same
                # print("Family meeting.")
                pass
            else:
                #LETS FIGHT!
                winner, loser = self.fight(neighbor)
                print(winner.unique_id, " won against ", loser.unique_id)
                losersPosition = loser.pos
                #loser dies
                loser.kill()
                
                #winner replaces him
                winner.addToGridAndSchedule(self.child(), losersPosition)
            
    def rand_unique_id(self):
        """Generate random new id within large range, i.e. collisions must be rare!"""
        
        return random.randrange(0,1000)
        # return random.randrange(-sys.maxsize, sys.maxsize)
        # we use the largest possible range without bleeding into the LONG range
        # the chance of a collision should be acceptably low. (Birthday Problem)
    
    def fitness(self, replicants):
        """Determine the fitness of the vehicle, by how well its genome solve the knapsack problem."""
        listOfReplicantAttributes = [r.attribute for r in replicants]
        return knapsack.fitness(listOfReplicantAttributes)
    
    def fight(self, other):
        """Fight, and return the result in the tuple (winner,loser)"""
        
        #probability of "self" winning
        pWin = self.fitness / (self.fitness + other.fitness)
        #flip the coin to see who wins, weighted with pWin, ofc
        Win = (pWin > random.random())
        
        if Win:
            return (self, other)
        else:
            return (other, self)
    
    def child(self):
        """Clone a child."""
        # this is basically a clone with a new id
        child = Vehicle(self.rand_unique_id(), self.model, self.replicants)
        
        return child
        
        
    def addToGridAndSchedule(self, vehicle, position):
        """So that you dont forget adding new vehicles to BOTH Grid and Schedule!"""
        #add to grid
        self.model.grid.place_agent(vehicle, position)
        
        # add to schedule
        self.model.schedule.add(vehicle)
            
    def kill(self):
        """Removes itself from the Grid and the Schedule."""
        self.dead = True # for toubleshooting purposes, to confirm that dead aagents are never called
        self.model.grid.remove_agent(self)
        self.model.schedule.remove(self)
        
    def mutate(self):
        """Mutation stage of simulation. Every Vehicle has a chance to mutate."""
        
        if self.dead:
            print("ERRROR: ", self.unique_id," was called, even though it is dead!" ) 
        
        m = 0.1 # probability of a mutation
        #insertion and deletion mutations are equally likely, so that no bias towards more complex species exists
        
        mutated_replicants = self.replicants # basis for mutations
        mutated_bool = False # keep track of wether we mutated or not
        
        # roll dice for deletion mutation
        if m > random.random():
            # remove a random element
            mutated_replicants.pop(random.randrange(0,len(mutated_replicants)))
            mutated_bool =True
                
        # roll dice for insertion mutation
        if m > random.random():
            # add a random gene
            mutated_replicants.append(Replicant())
            mutated_bool =True
        
        # sort new list for ease of comparison
        
        # mutated_replicants list is finished.
        
        if len(mutated_replicants) == 0:
            self.kill() #no more genome means dying
            print(self.unique_id, " died, due to deleting its last Replicant.")
        
        elif mutated_bool:
            # ------------Create mutant-----------------
            mutant = Vehicle(self.rand_unique_id(), self.model, mutated_replicants)
            
            print(self.unique_id, " has mutated to ", mutant.unique_id)
            # if the vehicle has mutated, remove old self, replace with mutant
            pos = self.pos
            self.kill()
            self.addToGridAndSchedule(mutant, pos)