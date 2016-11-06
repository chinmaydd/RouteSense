# Using the local development version of pymote
import sys
import MCFSetup
import MCFAlgorithm
import pdb
sys.path.append("/home/chinmay_dd/Projects/ACN.WSN/pymote2.0")
from pymote.algorithm import Algorithm
from pymote import *

# Let's work with 10 nodes.
net_gen = NetworkGenerator(10,10,10)
net = net_gen.generate_random_network()
net.algorithms = ((MCFSetup.MCFSetup, {"sinkKey":"ICost"}),)

# Setting the 0th node to be the base.
first_node = net.nodes()[0]
first_node.memory["ICost"] = "0"
first_node.memory["BCost"] = "0"
first_node.type = "B"

sim = Simulation(net)
sim.run()

net.algorithms = ((MCFSetup.MCFSetup, {"sinkKey":"ICost"}), (MCFAlgorithm.MCFAlgorithm, {"transmitNode": "T"}),)

# Choosing random numbers 3 and 9
last_node = net.nodes()[9]
# Something
last_node.memory["T"] = "S"
last_node.status = "TRANSMIT"

# Set the status as wait.
first_node.status = "WAIT"

sim = Simulation(net)
sim.run()

print [x.memory["BCost"] for x in net.nodes()]

net.show()

pdb.set_trace()
