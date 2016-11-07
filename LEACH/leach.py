import sys
sys.path.append("../pymote2.0")
from pymote.algorithm import NodeAlgorithm
from pymote.message import Message
import sys

class Leach(NodeAlgorithm):
    required_params = ('informationKey',)
    default_params = {'neighborsKey': 'Neighbors'}
    done_count = 0

    def initializer(self):
        ini_nodes = []
	for node in self.network.nodes():
            node.memory[self.neighborsKey] = node.compositeSensor.read()['Neighbors']
            node.status = 'IDLE'
            if self.informationKey in node.memory:
                node.status = 'INITIATOR'
                ini_nodes.append(node)
        for ini_node in ini_nodes:
            self.network.outbox.insert(0, Message(header=NodeAlgorithm.INI, destination=ini_node))

    def initiator(self, node, message):
        assert message.header == NodeAlgorithm.INI
        node.status = 'IDLE'
        data = node.memory[self.informationKey]
        # Initiation can occur only from base_station
        if node.type == 'B':
            # Base station always sends to all
            node.send(Message(header='Information', data=data))
        else:
            print("Only base station can initiate communication!")
            sys.exit(1)

    def idle(self, node, message):
        if node.type == 'N' and message.data == "Request for data":
            dst = node.memory['cluster_head']
            data = "Sensor Id: %s" % str(node.id)
            node.send(Message(header='Information', data=data, destination=dst))
        elif node.type == 'C' and message.data.startswith("Sensor Id"):
            if message.source.id not in node.memory['recv_list']:
                node.memory['recv_list'].append(message.source.id)
                node.memory['aggregate_data'].append(message.data.split(": ")[1])
                node.memory['recv_count'] += 1
                print("Cluster_head Id %s: recv_count %s" % (str(node.id), str(node.memory['recv_count'])))
                if node.memory['recv_count'] == 9:
                    dst = node.memory['cluster_head']
                    nodeIds = node.memory['aggregate_data']
                    node.send(Message(header='Information', data=nodeIds, destination=dst))

        elif node.type == 'B' and type(message.data) is list and message.destination == node:
            aggregate_data = message.data
            to_save = "Node %s was responsible for %s" % (str(message.source.id), aggregate_data)
            self.done_count += 1
            node.memory['aggregate_data'].append(to_save)
            if self.done_count == 10:
                node.status = 'DONE'

        if message.data == "Request for data":
            destination_nodes = list(node.memory[self.neighborsKey])
            destination_nodes.remove(message.source)
            if destination_nodes:
                node.send(Message(destination=destination_nodes, header='Information', data=message.data))

    def done(self, node, message):
        pass

    STATUS = {
	'INITIATOR': initiator,
	'IDLE': idle,
	'DONE': done
	}
