def knapsack(weights):
    """A normalised knapsack Problem."""
    return abs(sum(weights) -1)

def fitness (attributes):
    """A fitness function based on the knapsack problem"""
    k = knapsack(attributes)
    if k ==0:
        return float ('inf')
    else:
        return 1/knapsack(attributes)