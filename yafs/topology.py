import logging
import warnings
from typing import Tuple, Dict

import networkx as nx


# TODO Is this entire class necessary? Wouldn't it be smarter to just use a nx.networkx instance?


class Topology:
    """Unifies the functions to deal with **Complex Networks** as a network topology within of the simulator.

    In addition, it facilitates its creation, and assignment of attributes.
    """

    LINK_BW = "BW"  # Link feature: Bandwidth
    LINK_PR = "PR"  # Link feature: Propagation delay
    # LINK_LATENCY = "LATENCY"  # A edge or a network link has a Bandwidth"

    NODE_IPT = "IPT"  # Node feature: Instructions per Simulation Time

    def __init__(self, logger=None):  # TODO Remove logger
        self.__idNode = -1
        self.G: nx.networkx = None  # TODO ??

        # TODO VERSION 2. THIS VALUE SHOULD BE REMOVED
        # INSTEAD USE NX.G. attributes
        self.nodeAttributes = {}

        # A simple *cache* to have all cloud  nodes
        # TODO VERSION 2. THIS VALUE SHOULD BE REMOVED
        self.cloudNodes = []

        self.logger = logger or logging.getLogger(__name__)

    def __init_uptimes(self):
        for key in self.nodeAttributes:
            self.nodeAttributes[key]["uptime"] = (0, None)

    def get_edges(self):
        """Returns a list of graph edges, i.e.: ((1,0),(0,2),...)"""
        return self.G.edges

    def get_edge(self, key: Tuple[int, int]):
        """
        Args:
            key: a edge identifier, i.e. (1,9)

        Returns:
            list: a list of edge attributes
        """
        return self.G.edges[key]

    def get_nodes(self):
        """
        Returns:
            list: a list of all nodes features
        """
        return self.G.nodes

    def get_node(self, key: int):
        """
        Args:
            key: a node identifier

        Returns:
            list: a list of node features
        """
        return self.G.node[key]

    def get_info(self):
        return self.nodeAttributes

    def create_topology_from_graph(self, G: nx.Graph):
        """Generates the topology from a NetworkX graph"""
        if isinstance(G, nx.classes.graph.Graph):
            self.G = G
            self.__idNode = len(G.nodes)
        else:
            raise TypeError

    def create_random_topology(self, nxGraphGenerator, params):
        """
        It generates the topology from a Graph generators of NetworkX

        Args:
             nxGraphGenerator (function): a graph generator function

        Kwargs:
            params (dict): a list of parameters of *nxGraphGenerator* function
        """
        try:
            self.G = nxGraphGenerator(*params)
            self.__idNode = len(self.G.node)
        except:
            raise Exception

    def load(self, data: Dict):
        """Generates the topology from a JSON file"""
        self.G = nx.Graph()
        for edge in data["link"]:
            self.G.add_edge(edge["s"], edge["d"], BW=edge[self.LINK_BW], PR=edge[self.LINK_PR])

        # TODO This part can be removed in next versions
        for node in data["entity"]:
            self.nodeAttributes[node["id"]] = node
        # end remove

        # Correct way to use custom and mandatory topology attributes

        valuesIPT = {}
        valuesRAM = {}
        for node in data["entity"]:
            try:
                valuesIPT[node["id"]] = node["IPT"]
            except KeyError:
                valuesIPT[node["id"]] = 0
            try:
                valuesRAM[node["id"]] = node["RAM"]
            except KeyError:
                valuesRAM[node["id"]] = 0

        nx.set_node_attributes(self.G, values=valuesIPT, name="IPT")
        nx.set_node_attributes(self.G, values=valuesRAM, name="RAM")

        self.__idNode = len(self.G.nodes)
        self.__init_uptimes()

    def load_all_node_attr(self, data):
        self.G = nx.Graph()
        for edge in data["link"]:
            self.G.add_edge(edge["s"], edge["d"], BW=edge[self.LINK_BW], PR=edge[self.LINK_PR])

        dc = {str(x): {} for x in list(data["entity"][0].keys())}
        for ent in data["entity"]:
            for key in list(ent.keys()):
                dc[key][ent["id"]] = ent[key]
        for x in list(data["entity"][0].keys()):
            nx.set_node_attributes(self.G, values=dc[x], name=str(x))

        for node in data["entity"]:
            self.nodeAttributes[node["id"]] = node

        self.__idNode = len(self.G.nodes)
        self.__init_uptimes()

    def load_graphml(self, filename):
        warnings.warn(
            "The load_graphml function is deprecated and " "will be removed in version 2.0.0. " "Use NX.READ_GRAPHML function instead.",
            FutureWarning,
            stacklevel=8,
        )

        self.G = nx.read_graphml(filename)
        attEdges = {}
        for k in self.G.edges():
            attEdges[k] = {"BW": 1, "PR": 1}
        nx.set_edge_attributes(self.G, values=attEdges)
        attNodes = {}
        for k in self.G.nodes():
            attNodes[k] = {"IPT": 1}
        nx.set_node_attributes(self.G, values=attNodes)
        for k in self.G.nodes():
            self.nodeAttributes[k] = self.G.node[k]  # it has "id" att. TODO IMPROVE

    def get_nodes_att(self):
        """
        Returns:
            A dictionary with the features of the nodes
        """
        return self.nodeAttributes

    def find_IDs(self, value):
        """
        Search for nodes with the same attributes that value

        Args:
             value (dict). example value = {"model": "m-"}. Only one key is admitted

        Returns:
            A list with the ID of each node that have the same attribute that the value.value
        """
        keyS = list(value.keys())[0]

        result = []
        for key in list(self.nodeAttributes.keys()):
            val = self.nodeAttributes[key]
            if keyS in val:
                if value[keyS] == val[keyS]:
                    result.append(key)
        return result

    def size(self):
        """
        Returns:
            an int with the number of nodes
        """
        return len(self.G.nodes)

    def add_node(self, nodes, edges=None):
        """
        Add a list of nodes in the topology

        Args:
            nodes (list): a list of identifiers

            edges (list): a list of destination edges
        """
        self.__idNode = +1
        self.G.add_node(self.__idNode)
        self.G.add_edges_from(list(zip(nodes, [self.__idNode] * len(nodes))))

        return self.__idNode

    def remove_node(self, id_node):
        """
        Remove a node of the topology

        Args:
            id_node (int): node identifier
        """

        self.G.remove_node(id_node)
        return self.size()

    def write(self, path):
        nx.write_gexf(self.G, path)

    def draw_png(self, path_file):
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(nrows=1, ncols=1)
        pos = nx.spring_layout(self.G)
        nx.draw(self.G, pos)
        labels = nx.draw_networkx_labels(self.G, pos)
        fig.savefig(path_file)  # save the figure to file
        plt.close(fig)  # close the figure
