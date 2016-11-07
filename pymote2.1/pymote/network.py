import inspect
from copy import deepcopy
import json
import pdb

from numpy.random import rand
from numpy.core.numeric import Inf, allclose
from numpy import array, pi, sign, max, min, isnan
from numpy.lib.function_base import average
from networkx import DiGraph, Graph, is_connected
import networkx as nx
from networkx.readwrite import json_graph

from pymote.logger import logger
from pymote.conf import settings
from environment import Environment
from channeltype import ChannelType, Doi
from node import Node
from pymote.energy import EnergyModel
from pymote import propagation
from algorithm import Algorithm
from pymote.sensor import CompositeSensor
from pymote.utils.helpers import pymote_equal_objects


class Network(Graph):

    def __init__(self, environment=None, channelType=None, algorithms=(),
                 networkRouting=True, propagation_type=2, **kwargs):

        Graph.__init__(self)
        self._environment = environment or Environment()
        # assert(isinstance(self.environment, Environment))
        self.channelType = channelType or ChannelType(self._environment)
        if isinstance(self.channelType, Doi):
            doi = kwargs.pop('doi', 0)
            # print "In DOI %s" %doi
            self.channelType.set_params(doi=doi)
        self.channelType.environment = self._environment
        self.propagation = propagation.PropagationModel(propagation_type=propagation_type)
        self.pos = {}
        self.ori = {}
        self.labels = {}
        #self.star = star_graph
        self.name = "WSN"
        self._algorithms = ()
        self.algorithms = algorithms or settings.ALGORITHMS
        self.algorithmState = {'index': 0, 'step': 1, 'finished': False}
        self.outbox = []
        self.networkRouting = networkRouting
        self.comm_range = kwargs.pop('commRange', None) or settings.COMM_RANGE
        logger.info("Instance of Network has been initialized with %s (%s)" % (self.propagation, self.comm_range))
        print("------------------------------")

    def subgraph(self, nbunch):
        """ Returns Graph instance with nbunch nodes, see subnetwork. """
        return Graph(self).subgraph(nbunch)

    # TODO: incomplete add other properties
    def subnetwork(self, nbunch, pos=None):
        """ Returns Network instance with nbunch nodes, see subgraph. """
        if not pos:
            pos = self.pos
        H = Graph.subgraph(self, nbunch)
        for node in H:
            H.pos.update({node: pos[node][:2]})
            if len(pos[node]) > 2:
                H.ori.update({node: pos[node][2]})
            else:
                H.ori.update({node: self.ori[node]})
            H.labels.update({node: self.labels[node]})
        H._environment = deepcopy(self._environment)
        assert(isinstance(H, Network))
        return H

    def nodes(self, data=False):
        """ Override, sort nodes by id, important for message ordering."""
        return list(sorted(self.nodes_iter(data=data), key=lambda k: k.id))

    @property
    def algorithms(self):
        """
        Set algorithms by passing tuple of Algorithm subclasses.

        >>> net.algorithms = (Algorithm1, Algorithm2,)

        For params pass tuples in form (Algorithm, params) like this

        >>> net.algorithms = ((Algorithm1, {'param1': value,}), Algorithm2)

        """
        return self._algorithms

    @algorithms.setter
    def algorithms(self, algorithms):
        #self.reset()
        self._algorithms = ()
        if not isinstance(algorithms, tuple):
            raise PymoteNetworkError('algorithm')
        for algorithm in algorithms:
            if inspect.isclass(algorithm) and issubclass(algorithm, Algorithm):
                self._algorithms += algorithm(self),
            elif (isinstance(algorithm, tuple) and
                  len(algorithm) == 2 and
                  issubclass(algorithm[0], Algorithm) and
                  isinstance(algorithm[1], dict)):
                self._algorithms += algorithm[0](self, **algorithm[1]),
            else:
                raise PymoteNetworkError('algorithm')

    @property
    def environment(self):
        return self._environment

    @environment.setter
    def environment(self, environment):
        """ If net environment is changed all nodes are moved into and
            corresponding channelType environment must be changed also. """
        self._environment = environment
        self.channelType.environment = environment
        for node in self.nodes():
            self.remove_node(node)
            self.add_node(node)
        logger.warning('All nodes are moved into new environment.')

    def remove_node(self, node):
        """ Remove node from network. """
        if node not in self.nodes():
            logger.error("Node not in network")
            return
        Graph.remove_node(self, node)
        del self.pos[node]
        del self.labels[node]
        node.network = None
        logger.info('Node with id %d is removed.' % node.id)

    def add_node(self, node=None, pos=None, ori=None, commRange=None, find_random=False):
        """
        Add node to network.

        Attributes:
          `node` -- node to add, default: new node is created
          `pos` -- position (x,y), default: random free position in environment
          `ori` -- orientation from 0 to 2*pi, default: random orientation

        """
        if (not node):
            node = Node(commRange=commRange or self.comm_range)
        if not node.commRange:
            node.commRange = commRange or self.comm_range

        assert(isinstance(node, Node))
        if not node.network:
            node.network = self
        else:
            logger.warning('Node is already in another network, can\'t add.')
            return None

        pos = pos if (pos is not None and not isnan(pos[0])) else self.find_random_pos(n=100)
        ori = ori if ori is not None else rand() * 2 * pi
        ori = ori % (2 * pi)

        got_random = False
        if find_random and not self._environment.is_space(pos):
            pos = self.find_random_pos(n=100)
            got_random = True

        if (self._environment.is_space(pos)):
            Graph.add_node(self, node)
            self.pos[node] = array(pos)
            self.ori[node] = ori
            self.labels[node] = ('C' if node.type == 'C' else "") + str(node.id)
            logger.debug('Node %d is placed on position %s %s %s'
                         % (node.id, pos,
                            '[energy=%5.3f]' %node.power.energy
                                    if node.power.energy != EnergyModel.E_INIT  else '',
                            'Random' if got_random else ''))
            self.recalculate_edges([node])
        else:
            Node.cid -= 1
            logger.error('Given position is not free space. [%s] %s' % (Node.cid, pos))
            node = None
        return node

    def node_by_id(self, id_):
        """ Returns first node with given id. """
        for n in self.nodes():
            if (n.id == id_):
                return n
        logger.error('Network has no node with id %d.' % id_)
        return None

    def avg_degree(self):
        return average(self.degree().values())

    def modify_avg_degree(self, value):
        """
        Modifies (increases) average degree based on given value by
        modifying nodes commRange."""
        # assert all nodes have same commRange
        assert allclose([n.commRange for n in self], self.nodes()[0].commRange)
        #TODO: implement decreasing of degree, preserve connected network
        assert value + settings.DEG_ATOL > self.avg_degree()  # only increment
        step_factor = 7.
        steps = [0]
        #TODO: while condition should call validate
        while not allclose(self.avg_degree(), value, atol=settings.DEG_ATOL):
            steps.append((value - self.avg_degree())*step_factor)
            for node in self:
                node.commRange += steps[-1]
            # variable step_factor for step size for over/undershoot cases
            if len(steps)>2 and sign(steps[-2])!=sign(steps[-1]):
                step_factor /= 2
        logger.debug("Modified degree to %f" % self.avg_degree())

    def get_current_algorithm(self):
        """ Try to return current algorithm based on algorithmState. """
        if len(self.algorithms) == 0:
            logger.warning('There is no algorithm defined in a network.')
            return None
        if self.algorithmState['finished']:
            if len(self.algorithms) > self.algorithmState['index'] + 1:
                self.algorithmState['index'] += 1
                self.algorithmState['step'] = 1
                self.algorithmState['finished'] = False
            else:
                return None
        return self.algorithms[self.algorithmState['index']]

    def reset(self):
        logger.info('Resetting network.')
        self.algorithmState = {'index': 0, 'step': 1, 'finished': False}
        self.reset_all_nodes()

    def show(self, *args, **kwargs):
        fig = self.get_fig(*args, **kwargs)
        fig.show()

    def savefigpdf(self, fname='network', figkwargs={}, *args, **kwargs):
        from matplotlib.backends.backend_pdf import PdfPages
        with PdfPages(fname+".pdf") as pdf:
            pdf.savefig(self.get_fig(*args, **kwargs))
            d = pdf.infodict()
            d['Title'] = kwargs.pop('title', fname)
            d['Author'] = kwargs.pop('author', 'Farrukh Shahzad')
            d['Subject'] = kwargs.pop('subject','PhD Dissertation Nov 2015 - KFUPM')


    def savefig(self, fname='network', format='pdf', figkwargs={}, *args, **kwargs):
        if 'pdf' in format:
            self.savefigpdf(fname, figkwargs={}, *args, **kwargs)
        else:
            self.get_fig(*args, **kwargs).savefig(fname+'.'+format, format=format, transparent=True, **figkwargs)

    def get_fig(self, title="Topology", xlabel="X-axis", ylabel="Y-axis",
                positions=None, edgelist=None, nodeColor='b',
                show_labels=True, **kwargs):
        try:
            from matplotlib import pyplot as plt
        except ImportError:
            raise ImportError("Matplotlib required for show()")

        # TODO: environment when positions defined
        node_size = 30  # in points^2
        # calculate label delta based on network size
        label_delta = self.get_size()/max([30, len(self)])
        label_delta = self.get_size()/30
        dpi = 100
        h, w = self.environment.im.shape
        size = w, h
        scale = 600/w
        fig_size = (tuple(array(size)*scale/ dpi))
        # figsize in inches
        # default matplotlibrc is dpi=80 for plt and dpi=100 for savefig
        fig = plt.figure(num=0, figsize=fig_size, dpi=dpi, frameon=False)
        #fig.set_facecolor("#000000")
        plt.axis('off')
        plt.clf()
        plt.imshow(self._environment.im, cmap='binary_r', vmin=0,
                   origin='lower')
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        if kwargs.pop('grid', False):
            plt.grid()
        #plt.axis('tight')
        plt.xlim(-0.01*w, 1.01*w)
        plt.ylim(-0.01*h , 1.01*h)
        if positions:
            # truncate positions to [x, y], i.e. lose theta
            for k, v in positions.items():
                positions[k] = v[:2]
            pos = positions
            net = self.subnetwork(pos.keys())
            label_delta = (max(pos.values(), axis=0) -
                           min(pos.values(), axis=0))/max([60, len(positions)])
        else:
            pos = self.pos
            net = self
        label_pos = {}
        node_sizes = []
        node_colors = []
        colors = {'C': 'red', 'B': 'green', 'N': 'blue'}
        sizes = {'C': 80, 'B': 100, 'N': 30}
        lab_off = {'C': 0, 'B': 0, 'N': 0}
        coord = []
        for n in net.nodes():
            label_pos[n] = pos[n].copy() - lab_off[n.type]*label_delta
            node_sizes.append(sizes.get(n.type, 20))
            if n.power.have_energy():
                node_colors.append(colors.get(n.type, 'pink'))
            else:
                node_colors.append('light'+colors.get(n.type, 'pink'))
            if n.type == 'C':
                coord.append(n)
            elif len(net)>20:
                self.labels[n] = ''

        label_color = kwargs.pop('label_color', 'w')
        nx.draw_networkx_edges(net, pos, edgelist=edgelist, style='dotted', edge_color='#0F0F0F')
        nx.draw_networkx_nodes(net, pos, node_size=node_sizes, node_color=node_colors, node_shape='s')
        nx.draw_networkx_nodes(net, pos, nodelist=coord, node_shape='o', node_size=130)
        if show_labels:
            nx.draw_networkx_labels(net, label_pos, labels=net.labels, font_size=6, font_color=label_color)

        #print plt.xlim()
        return fig

    def neighbors(self, node):
        all_neighbors = []
        for n in self.nodes():
            if self.channelType.in_updated_comm_range(self, node, n):
                all_neighbors.append(n)

        return all_neighbors

    def recalculate_edges(self, nodes=[]):
        """ Recalculate edges for given nodes or for all self.nodes().
        Edge between nodes n1 and n2 are added if both are
        ChannelType.in_comm_range of each other"""
        if(not nodes):
            nodes = self.nodes()
        for n1 in nodes:
            for n2 in self.nodes():
                if (n1 != n2):
                    if (self.channelType.in_updated_comm_range(self, n1, n2)):
                        Graph.add_edge(self, n1, n2)
                    elif (Graph.has_edge(self, n1, n2)):
                        Graph.remove_edge(self, n1, n2)

    def add_edge(self):
        logger.warn('Edges are auto-calculated from channelType and commRange')

    def find_random_pos(self, n=100):
        """ Returns random position, position is free space in environment if
         it can find free space in n iterations """
        while (n > 0):
            pos = rand(self._environment.dim) * \
                tuple(reversed(self._environment.im.shape))
            if self._environment.is_space(pos):
                break
            n -= 1
        return pos

    def reset_all_nodes(self):
        for node in self.nodes():
            node.reset()
        logger.info('Resetting all nodes.')

    def communicate(self):
        """Pass all messages from node's outboxes to its neighbors inboxes."""
        # Collect messages
        for node in self.nodes():
            self.outbox.extend(node.outbox)
            node.outbox = []
        while self.outbox:
            message = self.outbox.pop(0)
            #print message.data
            if (message.destination == None and message.nexthop == None):
                # broadcast
                self.broadcast(message)
            elif (message.nexthop != None):
                # Node routing
                try:
                    self.send(message.nexthop, message)
                except PymoteMessageUndeliverable, e:
                    pass
            elif (message.destination != None):
                # Destination is neighbor
                if (message.source in self.nodes() and
                    message.destination in self.neighbors(message.source)):
                    self.send(message.destination, message)
                elif (self.networkRouting):
                # Network routing
                # TODO: program network routing so it goes hop by hop only
                #       in connected part of the network
                    self.send(message.destination, message)
                else:
                    raise PymoteMessageUndeliverable('Can\'t deliver message.',
                                                      message)


    def broadcast(self, message):
        if message.source in self.nodes():
            neighbors = self.neighbors(message.source)
            for node in neighbors:
                neighbors_message = message.copy()
                neighbors_message.destination = node
                self.send(node, neighbors_message)
        else:
            raise PymoteMessageUndeliverable('Source not in network. \
                                             Can\'t broadcast', message)

    def send(self, destination, message):
        logger.debug('Sending message from %s to %s (%s).' %
                      (repr(message.source), destination, message.data))

        if destination in self.nodes():
            destination.push_to_inbox(message)
            #if message.source:
                #message.source.power.decrease_tx_energy(message.message_length())  # TODO
        else:
            raise PymoteMessageUndeliverable('Destination not in network.',
                                             message)

    def info(self):
        return self.__str__()

    def get_size(self):
        """ Returns network width and height based on nodes positions. """
        return max(self.pos.values(), axis=0) - min(self.pos.values(), axis=0)

    def save_json(self, filename, scale=(1, 1)):
        data = json_graph.node_link_data(self)
        data.pop('nodes')
        data.pop('links')


        #adj = json_graph.adjacency_data(self)
        #print adj
        h, w = self.environment.im.shape
        nodes = []
        colors = {'C': 'red', 'B': 'green', 'N': 'blue'}
        shapes = {'C': 'circle', 'B': 'circle', 'N': 'square'}
        sizes = {'C': 15, 'B': 10, 'N': 10}
        k=0
        for node in self.nodes():
            node.id = k
            nodes.append({'name': str(node.id), 'id': node.id, "size":sizes[node.type],
                "x": round(self.pos[node][0]*scale[0]), "color": colors[node.type],
                "y": (h - round(self.pos[node][1]))*scale[1], "shape": shapes[node.type]
                })
            k += 1

        data['graph']['r'] = int(node.commRange * scale[0])
        data['graph']['width'] = int(w * scale[0])
        data['graph']['height'] = int (h * scale[1])
        data['graph']['drag'] = True
        name = data['graph']['name']

        data['graph']['name'] = (name.split("\n")[0]).replace("$","")
        edges = nx.edges(self)
        edge_list = []
        for edge in edges:
            edge_list.append({'source': edge[0].id, 'target': edge[1].id})
        #print data
        #print nodes
        data['nodes'] = nodes
        data['links'] = edge_list
        with open(filename, 'w') as outfile:
            json.dump(data, outfile, indent=4)

    def get_dic(self):
        """ Return all network data in form of dictionary. """
        algorithms = {'%d %s' % (ind, alg.name): 'active'
                      if alg == self.algorithms[self.algorithmState['index']]
                      else '' for ind, alg in enumerate(self.algorithms)}
        pos = {n: 'x: %.2f y: %.2f theta: %.2f deg' %
               (self.pos[n][0], self.pos[n][1], self.ori[n] * 180. / pi)
               for n in self.nodes()}
        return {'nodes': pos,
                'algorithms': algorithms,
                'algorithmState': {'name':
                                   self.get_current_algorithm().name
                                   if self.get_current_algorithm() else '',
                                  'step': self.algorithmState['step'],
                                  'finished': self.algorithmState['finished']}}

    def get_tree_net(self, treeKey):
        """
        Returns new network with edges that are not in a tree removed.

        Tree is defined in nodes memory under treeKey key as a list of tree
        neighbors or a dict with 'parent' (node) and 'children' (list) keys.

        """
        edgelist = []
        for node in self.nodes():
            nodelist = []
            if not treeKey in node.memory:
                continue
            if isinstance(node.memory[treeKey], list):
                nodelist = node.memory[treeKey]
            elif (isinstance(node.memory[treeKey], dict) and
                  'children' in node.memory[treeKey]):
                nodelist = node.memory[treeKey]['children']
            edgelist.extend([(node, neighbor) for neighbor in nodelist
                              if neighbor in self.nodes()])
        treeNet = self.copy()
        for e in treeNet.edges():
            if e not in edgelist and (e[1], e[0]) not in edgelist:
                treeNet.remove_edge(*e)
        return treeNet

    def validate_params(self, params):
        """ Validate if given network params match its real params. """
        logger.info('Validating params')
        count = params.get('count', None)  #  for unit tests
        if count:
            if isinstance(count, list):
                assert(len(self) in count)
            else:
                assert(len(self)==count)
        n_min = params.get('n_min', 0)
        n_max = params.get('n_max', Inf)
        assert(len(self)>=n_min and len(self)<=n_max)
        for param, value in params.items():
            if param=='connected':
                assert(not value or is_connected(self))
            elif param=='degree':
                assert(allclose(self.avg_degree(), value,
                                atol=settings.DEG_ATOL))
            elif param=='environment':
                assert(self.environment.__class__==value.__class__)
            elif param=='channelType':
                assert(self.channelType.__class__==value.__class__)
            elif param=='comm_range':
                for node in self:
                    assert(node.commRange==value)
            elif param=='sensors':
                compositeSensor = CompositeSensor(Node(), value)
                for node in self:
                    assert(all(map(lambda s1, s2: pymote_equal_objects(s1, s2),
                                   node.sensors, compositeSensor.sensors)))
            elif param=='aoa_pf_scale':
                for node in self:
                    for sensor in node.sensors:
                        if sensor.name()=='AoASensor':
                            assert(sensor.probabilityFunction.scale==value)
            elif param=='dist_pf_scale':
                for node in self:
                    for sensor in node.sensors:
                        if sensor.name()=='DistSensor':
                            assert(sensor.probabilityFunction.scale==value)
            #TODO: refactor this part as setting algorithms resets nodes
            """
            elif param=='algorithms':
                alg = self._algorithms
                self.algorithms = value
                assert(all(map(lambda a1, a2: pymote_equal_objects(a1, a2),
                               alg, self.algorithms)))
                #restore alg
                self._algorithms = alg
            """


class PymoteMessageUndeliverable(Exception):
    def __init__(self, e, message):
        self.e = e
        self.message = message

    def __str__(self):
        return self.e + repr(self.message)


class PymoteNetworkError(Exception):
    def __init__(self, type_):
        if type_ == 'algorithm':
            self.message = ('\nAlgorithms must be in tuple (AlgorithmClass,)'
                            ' or in form: ((AlgorithmClass, params_dict),).'
                            'AlgorithmClass should be subclass of Algorithm')
        else:
            self.message = ''

    def __str__(self):
        return self.message
