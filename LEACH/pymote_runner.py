import sys
sys.path.append("/home/chinmay_dd/Projects/ACN.WSN/pymote2.0")
from pymote import *
from leach import Leach
from pymote.algorithms.broadcast import Flood
import random

NETWORK_SIZE = 101
NUM_CLUSTER_HEADS = 10
CLUSTER_SIZE = 9
cluster_heads = []

net_gen = NetworkGenerator(NETWORK_SIZE)
net = net_gen.generate_random_network()

# SETUP PHASE
base_station = net.nodes()[100]
base_station.type = 'B'
base_station.memory['cluster_head'] = ''
base_station.memory['cluster_nodes'] = net.nodes()
base_station.memory['aggregate_data'] = []
index = 0
pointer = -1

# Randomization algorithm constants
P = 0.10  # desired percentage of clusterheads
r = 1  # round number

while True:
    tN = float(P) / (1 - P * (r % float(1) / P))
    n = random.random()
    if n < tN and net.nodes()[index].type not in ['C', 'B'] and 'cluster_head' not in net.nodes()[index].memory:
       cluster_head = net.nodes()[index]

       # Set type to 'cluster_head'
       cluster_head.type = 'C'

       # Set *it's* cluster_head to the base_station
       cluster_head.memory['cluster_head'] = base_station
       cluster_head.memory['recv_count'] = 0
       cluster_head.memory['aggregate_data'] = []
       cluster_head.memory['recv_list'] = []

       # Choose the nodes that belong to its cluster
       cluster_nodes = []
       while len(cluster_nodes) != CLUSTER_SIZE:
           pointer = (pointer + 1) % NETWORK_SIZE
           member_node = net.nodes()[pointer]
           if 'cluster_head' not in member_node.memory:
               member_node.type = 'N'
               member_node.memory['cluster_head'] = cluster_head
               member_node.memory['cluster_nodes'] = []
               cluster_nodes.append(member_node)
       cluster_head.memory['cluster_nodes'] = cluster_nodes
       cluster_heads.append(cluster_head)
    index = (index + 1) % (NETWORK_SIZE)

    if len(cluster_heads) == NUM_CLUSTER_HEADS:
        break

print cluster_heads
# Testing simulation
src = base_station
src.memory['I'] = 'Request for data'
# for idx, node in enumerate(net.nodes()):
#     print node.memory, node.id, idx
net.algorithms = ( (Leach, {'informationKey':'I'}), )
sim = Simulation(net)
sim.run()
#for node in cluster_heads:
#    print node.memory
