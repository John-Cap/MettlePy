###################
#Erdos network
from datetime import datetime
import random
import networkx as nx
import matplotlib.pyplot as plt
from collections import deque, defaultdict
import math
NETWORK_INSTANCES={}
NETWORK_INSTANCE_CNTR=1

def pingPythia():
    return "Hello from Mettle.networks!"


class Network:
    def __init__(self):
        self.graph = defaultdict(list)
        self.nxGraph = nx.Graph()

    def addConnection(self, node1, node2):
        self.graph[node1].append(node2)
        self.graph[node2].append(node1)
        self.nxGraph.add_edge(node1, node2)

    def visualizeNetwork(self):
        pos = nx.spring_layout(self.nxGraph)  # positions for all nodes

        # nodes
        nx.draw_networkx_nodes(self.nxGraph, pos, node_size=700)

        # edges
        nx.draw_networkx_edges(self.nxGraph, pos, edgelist=self.nxGraph.edges(), width=6)

        # labels
        nx.draw_networkx_labels(self.nxGraph, pos, font_size=20, font_family='sans-serif')

        plt.title("Network Graph")
        plt.show()

    def areConnected(self, startNode, endNode):
        if startNode == endNode:
            return True

        visited = set()
        queue = deque([startNode])
        visited.add(startNode)

        while queue:
            currentNode = queue.popleft()
            for neighbor in self.graph[currentNode]:
                if neighbor == endNode:
                    return True
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return False
    
    def getConnectionChain(self, startNode, endNode):
            if startNode == endNode:
                return [startNode]

            visited = set()
            queue = deque([(startNode, [startNode])])
            visited.add(startNode)

            while queue:
                currentNode, path = queue.popleft()

                for neighbor in self.graph.get(currentNode, []):
                    if neighbor == endNode:
                        return path + [endNode]

                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))

            return []

ERDOSNETWORK_INSTANCE=None

class ErdosNetwork(Network):
    def __init__(self):
        super().__init__()

    @staticmethod
    def initP():
        global ERDOSNETWORK_INSTANCE

        ERDOSNETWORK_INSTANCE = ErdosNetwork()

    @staticmethod
    def deInitP():
        global ERDOSNETWORK_INSTANCE

        ERDOSNETWORK_INSTANCE = None

class Pos:
    def __init__(self, x, y, z=0, time=0):
        self.x = x
        self.y = y
        self.z = z
        self.time = time

SPATIALNETWORK_INSTANCE=None

class SpatialNetwork(Network):
    def __init__(self):
        super().__init__()
        self.positions = {}
        self.nodeCount = 0

    @staticmethod
    def initP():
        global SPATIALNETWORK_INSTANCE

        SPATIALNETWORK_INSTANCE = SpatialNetwork()

    @staticmethod
    def deInitP():
        global SPATIALNETWORK_INSTANCE

        SPATIALNETWORK_INSTANCE = None

    def addNode(self, nodeOrPos):
        if isinstance(nodeOrPos, Pos):
            pos = nodeOrPos
            node = f"Node{self.nodeCount}"
            self.nodeCount += 1
        elif isinstance(nodeOrPos, list) and len(nodeOrPos) == 2:
            pos = Pos(nodeOrPos[0], nodeOrPos[1])
            node = f"Node{self.nodeCount}"
            self.nodeCount += 1
        else:
            raise ValueError("nodeOrPos must be a Pos object or a 2-D point represented as [x, y].")

        self.positions[node] = (pos.x, pos.y, pos.z, pos.time)
        self.nxGraph.add_node(node, pos=(pos.x, pos.y))

    def addNodes(self, positions):
        for nodeOrPos in positions:
            if isinstance(nodeOrPos, Pos):
                pos = nodeOrPos
                node = f"Node{self.nodeCount}"
                self.nodeCount += 1
            elif isinstance(nodeOrPos, list) and len(nodeOrPos) == 2:
                pos = Pos(nodeOrPos[0], nodeOrPos[1])
                node = f"Node{self.nodeCount}"
                self.nodeCount += 1
            else:
                raise ValueError("nodeOrPos must be a Pos object or a 2-D point represented as [x, y].")

            self.positions[node] = (pos.x, pos.y, pos.z, pos.time)
            self.nxGraph.add_node(node, pos=(pos.x, pos.y))

    def addNamedNodesAndConnections(self, positions):
        for nodeOrPos in positions:
            pos_1 = Pos(nodeOrPos[1][0],nodeOrPos[1][1])
            pos_2 = Pos(nodeOrPos[2][0],nodeOrPos[2][1])
            node_1 = nodeOrPos[0][0]
            node_2 = nodeOrPos[0][1]

            if not (node_1 in self.positions):
                self.positions[node_1] = (pos_1.x, pos_1.y, pos_1.z, pos_1.time)
                self.nxGraph.add_node(node_1, pos=(pos_1.x, pos_1.y))
            if not (node_2 in self.positions):
                self.positions[node_2] = (pos_2.x, pos_2.y, pos_2.z, pos_2.time)
                self.nxGraph.add_node(node_2, pos=(pos_2.x, pos_2.y))

            self.addConnection(node_1,node_2)
            
    def connectNearestNeighbors(self):
        nodes = list(self.positions.keys())
        for i, node in enumerate(nodes):
            minDistance = float('inf')
            nearestNeighbor = None
            for j, otherNode in enumerate(nodes):
                if node != otherNode:
                    dist = self.euclideanDistance(self.positions[node], self.positions[otherNode])
                    if dist < minDistance:
                        minDistance = dist
                        nearestNeighbor = otherNode
            if nearestNeighbor:
                self.addConnection(node, nearestNeighbor)

    @staticmethod
    def euclideanDistance(pos1, pos2):
        return math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2 + (pos1[2] - pos2[2]) ** 2 + (pos1[3] - pos2[3]) ** 2)

    def visualizeNetwork(self):
        pos = nx.get_node_attributes(self.nxGraph, 'pos')

        # nodes
        nx.draw_networkx_nodes(self.nxGraph, pos, node_size=200)

        # edges
        nx.draw_networkx_edges(self.nxGraph, pos, edgelist=self.nxGraph.edges(), width=6)

        # labels
        nx.draw_networkx_labels(self.nxGraph, pos, font_size=10, font_family='sans-serif')

        plt.title("Spatial Network Graph")
        plt.show()

SOCIAL_NETWORK_INSTANCE=None
class SocialNetwork(Network):
    def __init__(self):
        super().__init__()
        self.entity_connections = defaultdict(dict)

    @staticmethod
    def inst():
        global SOCIAL_NETWORK_INSTANCE
        SOCIAL_NETWORK_INSTANCE = None
        SOCIAL_NETWORK_INSTANCE = SocialNetwork()

    @staticmethod
    def deInst():
        global SOCIAL_NETWORK_INSTANCE
        SOCIAL_NETWORK_INSTANCE = None

    def addEntityConnection(self, entity1, entity2, friendPoints=0, lastPos=None, lastSeen=None):
        if lastSeen is None:
            lastSeen = datetime.now()
        if lastPos is None:
            lastPos = [0, 0]

        self.addConnection(entity1, entity2)
        connection_properties = {
            'friendPoints': friendPoints,
            'lastSeen': lastSeen,
            'lastPos': lastPos
        }
        self.entity_connections[entity1][entity2] = connection_properties
        self.entity_connections[entity2][entity1] = connection_properties

    def updateConnection(self, entity1, entity2, friendPoints=0, lastPos=None, lastSeen=None):
        if lastSeen is None:
            lastSeen = datetime.now()
        if lastPos is None:
            lastPos = [0, 0]

        if not (entity1 in self.entity_connections):
            self.addEntityConnection(entity1, entity2)
        elif not (entity2 in self.entity_connections):
            self.addEntityConnection(entity2, entity1)

        connection_properties = {
            'friendPoints': friendPoints,
            'lastSeen': lastSeen,
            'lastPos': lastPos
        }
        self.entity_connections[entity1][entity2] = connection_properties
        self.entity_connections[entity2][entity1] = connection_properties

    def getEntityConnectionProperties(self, entity1, entity2):
        return self.entity_connections.get(entity1, {}).get(entity2, None)
    
    def sociallyConnected(self, entity1, entity2):
        return self.areConnected(entity1, entity2)
    
    def getSocialConnections(self, entity1):
        return list(self.entity_connections.get(entity1,{}).keys())
    
    def getNumberOfJumps(self, entity1, entity2):
        if entity1 == entity2:
            return 0

        visited = set()
        queue = deque([(entity1, 0)])
        visited.add(entity1)

        while queue:
            currentEntity, jumps = queue.popleft()

            for neighbor in self.graph[currentEntity]:
                if neighbor == entity2:
                    return jumps + 1
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, jumps + 1))

        return -1  # Return -1 if entities are not connected
    
# Usage example:
SocialNetwork.inst()
SOCIAL_NETWORK_INSTANCE.addEntityConnection('Alice', 'Bob', friendPoints=10)
SOCIAL_NETWORK_INSTANCE.addEntityConnection('Bob', 'Sam', friendPoints=10)
SOCIAL_NETWORK_INSTANCE.addEntityConnection('Jason', 'Sam', friendPoints=10)
props = SOCIAL_NETWORK_INSTANCE.getEntityConnectionProperties('Alice', 'Bob')
print([props,SOCIAL_NETWORK_INSTANCE.sociallyConnected('Alice', 'Sam'),SOCIAL_NETWORK_INSTANCE.getNumberOfJumps('Alice', 'Jason')])

'''
# Example usage:
if __name__ == "__main__":
    # ErdosNetwork example
    erdosNetwork = ErdosNetwork()
    
    # Add connections (edges) to the network
    erdosNetwork.addConnection('A', 'B')
    erdosNetwork.addConnection('A', 'C')
    erdosNetwork.addConnection('B', 'D')
    erdosNetwork.addConnection('C', 'E')
    erdosNetwork.addConnection('D', 'C')
    erdosNetwork.addConnection('E', 'A')
    erdosNetwork.addConnection('F', 'D')
    erdosNetwork.addConnection('G', 'H')
    erdosNetwork.addConnection('H', 'I')
    erdosNetwork.addConnection('I', 'J')
    erdosNetwork.addConnection('J', 'F')
    erdosNetwork.addConnection('G', 'E')
    erdosNetwork.addConnection('F', 'K')
    #erdosNetwork.addConnection('L', 'M')
    #erdosNetwork.addConnection('J', 'M')
    erdosNetwork.addConnection('O', 'P')
    erdosNetwork.addConnection('F', 'R')
    erdosNetwork.addConnection('L', 'Q')
    erdosNetwork.addConnection('J', 'M')
    erdosNetwork.addConnection('G', 'P')
    erdosNetwork.addConnection('X', 'Z')
    erdosNetwork.addConnection('J', 'Y')
    erdosNetwork.addConnection('Z', 'P')

    startNode = 'A'
    endNode = 'Z'
    print(f"Are nodes {startNode} and {endNode} connected? {erdosNetwork.areConnected(startNode, endNode)}")

    # Visualize the Erdos network
    erdosNetwork.visualizeNetwork()
    # SpatialNetwork example
    spatialNetwork = SpatialNetwork()

    # Add nodes with 4-D locations (time and z-axis default to 0)
    spatialNetwork.addNodes([[1322.55,7877.59],[1372.48,7707.29],[1820.12,7695.45],[1441.85,7660.31],[2108.63,7948.29],[1598.53,7613.33],[2488.94,8212.34],[1293.46,7686.79],[3546.43,8582.87],[4041.42,9199],[4166.94,9081.27],[4127.78,9131.72],[5152.65,9548.89],[5217.01,9975.29],[5284.04,10364.3],[6360.52,10998.9],[6350.31,10927.5],[5993.68,10968.5],[6076.11,11143.4],[4406.18,10388.5],[4317.76,10326.1],[4184.27,10216.9],[4037.32,10061.3],[3677.9,10169.1],[3806.84,10300.9],[6550.21,11065.2],[5187.25,10520.6],[4777.28,9454.25],[6486.37,11029.2],[5341.95,9921.35],[3767.02,8847.7],[3619.01,8789.51],[2777,8820.72],[1715.17,7798.32],[1219.82,7819.53],[5251.58,9759.24],[4517.94,9260.18],[4215.97,9075.23],[6293.53,10893.2],[2259.02,8063.3],[2187.22,8031.84],[1611.22,7756.51],[5159.81,9931.16],[5212.06,9657.33],[1385.98,8086.41],[1339.93,7447.73],[3717.71,8803.54],[2022.54,7726.03],[5214.57,10369.1],[2690.87,9109.79],[4881.83,10070.1],[4670.6,10172.8],[5063.16,10195.4],[2735.78,8888.24],[2692.37,9022.96],[3644.49,8846.57],[3713.28,8861.39],[4076.98,10280.5],[4381.98,10533],[4422.87,10484.9]])

    nodes=[]
    _i=1
    while _i < spatialNetwork.nodeCount:
        nodes.append(f"Node{_i}")
        _i+=1
    
    for _x in nodes:
        _other=random.choice(nodes)
        if _other != _x:
            spatialNetwork.addConnection(_x,_other)

    startNode=random.choice(nodes)
    endNode=random.choice(nodes)
    print(f"Are nodes {startNode} and {endNode} connected? {spatialNetwork.areConnected(startNode, endNode)}")

    # Visualize the spatial network
    spatialNetwork.visualizeNetwork()
'''