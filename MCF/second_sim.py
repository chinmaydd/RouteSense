# Using the local development version of pymote
import sys
import MCFSetup
import MCFAlgorithm
import pdb
sys.path.append("../pymote2.1")
from pymote.algorithm import Algorithm
from pymote.node import Node
from pymote import *

# Let's work with 10 nodes.
net_gen = NetworkGenerator(10,10,10)
net = net_gen.generate_random_network()
net.algorithms = ((MCFSetup.MCFSetup, {"sinkKey":"BCost"}),)

# Setting the 0th node to be the base.
first_node = net.nodes()[0]
first_node.memory["BCost"] = "0"
first_node.type = "B"

sim = Simulation(net)
sim.run()

net.show()

raw_input()

net.algorithms = ((MCFSetup.MCFSetup, {"sinkKey":"BCost"}),
    (MCFSetup.MCFSetup, {"sinkKey": "BCost"}),)

malicious_node = Node(commRange=1000, memory={"BCost":"0"})
net.add_node(malicious_node)

sim = Simulation(net)
sim.run()

net.show()

raw_input()

net.algorithms = ((MCFSetup.MCFSetup, {"sinkKey":"BCost"}), (MCFSetup.MCFSetup,
  {"sinkKey": "BCost"}), (MCFAlgorithm.MCFAlgorithm, {"transmitNode": "T"}),)

# Choosing random numbers 3 and 9
last_node = net.nodes()[9]
# Something
last_node.memory["T"] = "S"
last_node.status = "TRANSMIT"

# Set the status as wait.
first_node.status = "WAIT"

sim = Simulation(net)
sim.run()

net.show()

pdb.set_trace()
