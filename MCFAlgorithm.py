# Using the local development version of pymote
import sys
sys.path.append("/home/chinmay_dd/Projects/ACN.WSN/pymote2.0")
from pymote.message import Message
from pymote.algorithm import NodeAlgorithm
import pdb
from pymote.logger import logger
# Using infinity from the numpy module
# Although, we will be using a infinity-like value in the actual implementation,
# this particular logic helps in algorithm implementation.
from numpy import inf
from math import isinf

# Some premise for application of this algorithm.
# The minimum cost field must already be setup.
# A node should be chosen who wants to transmit data to another.
# It's status should be "TRANSMIT"
# It's memory should contain the destination node as "DEST"
class MCFAlgorithm(NodeAlgorithm):
    required_params = ('transmitNode',)
    default_params = {}
    destination = None

    TRA = "TRANSMIT"

    def initializer(self):
        for node in self.network.nodes():
            if node.status == "TRANSMIT":
                cost_string = "MCost=" + str(node.memory["BCost"])
                node.send(Message(header=self.TRA, data=cost_string))
                node.status = "DONE"
            elif node.id != 1: # Hacky, but works for now
                node.status = "IDLE"

    def link_cost(self, message):
        # Using SNR for this.
        signal_to_noise_ratio = message.destination.snr[0]
        l_cost = (0-(signal_to_noise_ratio/10))

        return l_cost

    def idle(self, node, message):
        BCost = float(message.data.split("=")[1])
        mlink_cost = self.link_cost(message)
        
        remaining_budget = BCost - mlink_cost

        if float(node.memory["BCost"]) <= remaining_budget:
            cost_string = "MCost="+str(node.memory["BCost"])
            node.send(Message(header=self.TRA, data=cost_string))
          
        node.status = "DONE"

    def done(self, node, message):
        pass

    def wait(self, node, message):
        if message.header == self.TRA:
          logger.info("Message to sink received!")

    STATUS = {
            "WAIT": wait,
            "IDLE": idle,
            "DONE": done,
            }
