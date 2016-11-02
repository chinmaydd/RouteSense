# Using the local development version of pymote
import sys
import MCFAlgorithm
import pdb
sys.path.append("/home/chinmay_dd/Projects/ACN.WSN/pymote2.0")
from pymote import *

net_gen = NetworkGenerator(5, 5, 5)
net = net_gen.generate_random_network()
net.algorithms = ((MCFAlgorithm.MCF, {"sinkKey":"ICost"}),)

# Setting the 0th node to be the base.
first_node = net.nodes()[0]
first_node.memory["ICost"] = "0"
first_node.memory["BCost"] = "0"
first_node.type = "B"

sim = Simulation(net)
sim.run()
net.show()

pdb.set_trace()

# for node in net.nodes():
#     print node.id
#     print node.memory["BCost"]
#     print "-------"
