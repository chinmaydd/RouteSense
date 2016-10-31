###########################
# Minimum Cost Forwarding #
# Author: chinmay_dd      #
###########################

# Using the local development version of pymote
import sys
sys.path.append("/home/chinmay_dd/Projects/ACN.WSN/pymote2.0")
from pymote.message import Message
from pymote.algorithm import NodeAlgorithm
import pdb
# Using infinity from the numpy module
# Although, we will be using a infinity-like value in the actual implementation,
# this particular logic helps in algorithm implementation.
from numpy import inf
from math import isinf

# MCF Algorithm implementation (along with optimization)
class MCF(NodeAlgorithm):
  # Key for data being updated in the node.
  required_params = ('sinkKey',)
  default_params = {}

  # Header used to advertise the lowest cost.
  ADV = "advertisement"

  def step(self, node):
    message = node.receive()
    if message:
      if (message.destination == None or message.destination == node):
        # when destination is None it is broadcast message
        return self._process_message(node, message)
      elif (message.nexthop == node.id):
        self._forward_message(node, message)

  # Helper method to check if the message is an advertisement
  def check_if_adv(self, message):
    return (message.header == self.ADV or message.header == NodeAlgorithm.INI)

  # Status initializer for each node.
  def initializer(self):
    for node in self.network.nodes():
      # If the node is a sink node, broadcase the message and set it to done.
      if self.sinkKey in node.memory:
        self.network.outbox.insert(0, Message(header=NodeAlgorithm.INI,
          source=node, data=node.memory[self.sinkKey]))
        node.status = "DONE"
      else:
        # Set all other nodes to "IDLE"
        node.status = "IDLE"
        node.memory["BCost"] = inf
  
  # Method to calculate link cost from A->B
  # Cost of the link maybe a composite of:
  # hop count
  # consumed wireless energy
  # delay between source and sink
  # function of received signal strength (we can use the snr component, 
  # i.e signal to noise ratio
  # number of retransmissions
  def calculate_cost(self, message):
    # Energy consumed during receving the message
    # consumed_wireless_energy = message.destination.power.energy_consumption
    # Closer the SNR is to 0 ==> Better the signal received
    # SNR contains all the params. We can choose it to calculate link_cost
    signal_to_noise_ratio = message.destination.snr[0]
    # Normalizing the snr value as (0-snr/10) and adding the already existing
    # message cost(received from the message) to the same.
    link_cost = float(message.data) + (0-(signal_to_noise_ratio/10))
    
    return link_cost
  
  # After the initialization process, each node is set to an idle state.
  # On receiving the first "ADV", the node should transition itself to the
  # listening state. 
  # This implies that further messages are received but not broadcasted.
  # The broadcast duration will depend on a "backoff" algorithm as mentioned in
  # the reference paper.
  def idle(self, node, message):
    # Now, depending on the header of the message we can make two choices:
    # If the header is NodeAlgorithm.INI, this implies that the node is a
    # neighbor to the sink node.
    # Otherwise, the node is just another node in the network.
    # Either way, we will have the node transition into the "LISTENING" state
    # and implement the backoff algorithm.
    if self.check_if_adv(message):
      node.memory["BCost"] = self.calculate_cost(message)
      node.status = "LISTENING"
    else:
      # This implies that the algorithm is now in operational mode.
      pass

  def done(self, node, message):
    pass

  # After the node has received the first initialization message, it sets a
  # value in its memory for the link_cost.
  def listening(self, node, message):
    pdb.set_trace()
    if self.check_if_adv(message):
      message_cost = self.calculate_cost(message)
      if message_cost < node.memory["BCost"]:
        node.memory["BCost"] = message_cost
        node.memory["Timer"] = int(message_cost/2)
      else:
        node.memory["Timer"] -= 1
    
    if node.memory["Timer"] == 0:
      node.status = "TRANSITION"
    
  def transition(self, node, message):
    # Broadcast the local cost.
    print(message)
    node.status = "DONE"

  STATUS = {
      "IDLE": idle,
      "DONE": done,
      "LISTENING": listening,
      "TRANSITION": transition
      }
