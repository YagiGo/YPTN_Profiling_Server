# draw the dependency tree base on the analysis json
# TODO: Change to DB access when ready
import os,json,csv
from collections import OrderedDict
import plotly
import plotly.plotly as py
import plotly.graph_objs as go
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from collections import OrderedDict
from igraph import *
from pymongo import MongoClient
import time, datetime
ANALYSIS_FILE_PATH = os.path.abspath(os.path.join(os.curdir, "graphs"))
PRIORITY_ANALYSIS_FILE_PATH = os.path.abspath(os.path.join(os.curdir, "priority_analysis"))
IMAGE_SAVE_PATH = os.path.abspath(os.path.join(os.curdir, "DAG_CUT_DEMO"))


class DBInteractModule:
    def __init__(self, DB_ADDRESS="localhost", DB_PORT=27017):
        self.DB_ADDR = DB_ADDRESS
        self.DB_PORT = DB_PORT
        self.client = MongoClient(self.DB_ADDR, self.DB_PORT)

    def addNode(self, dbName, collectionName, nodeObject):
        nodeDataCollectoin = self.client[dbName][collectionName]
        nodeDataCollectoin.insert_one(nodeObject)

    def addNodes(self, dbName, collectionName, nodeObjects):
        nodeDataCollection = self.client[dbName][collectionName]
        nodeDataCollection.insert(nodeObjects)

    def addEdges(self, dbName, collectionName, edgeObject):
        edgeDataCollection = self.client[dbName][collectionName]
        edgeDataCollection.insert_one(edgeObject)

    def addMany(self, dbName, collectionName, objects):
        nodeDataCollection = self.client[dbName][collectionName]

        if(collectionName in self.client[dbName].list_collection_names()):
            nodeDataCollection.drop()
        try:
            nodeDataCollection.insert(objects)
        except:
            print("ERROR: DATA INSERT ERROR")

    def findNode(self, dbName, collectionName, query):
        nodeCollection = self.client[dbName][collectionName]
        return nodeCollection.find_one(filter=query)

    def findNodes(self, dbName, collectionName, query):
        nodeCollection = self.client[dbName][collectionName]

class DependencyTreeNode:
    def __init__(self, activityID, detail):
        self.activityID = activityID
        self.ancestors = []
        self.children = []
        self.parent = None
        self.priority = -1
        self.detail = detail

    def addChild(self, childNode):
        self.children.append(childNode)

    def findAncestors(self, ancestorNode):
        if(ancestorNode not in self.ancestors):
            self.ancestors.append(ancestorNode)
        else:
            print("This guy has multiple parents")

class DependencyAnalysis:
    def __init__(self, url, testNo):
        self.url = url
        self.file_path = os.path.join(ANALYSIS_FILE_PATH,  "{}_{}.json".format(testNo, url))
        # self.file_path = os.path.join(ANALYSIS_FILE_PATH, url)
        self.profiled_data = self.readJsonaAsDitc()
        self.critical_path = self.getCriticalPath()
        self.dependedElements = self.getDependedElements()

    def showFilePath (self):
        print(self.file_path)

    def readJsonaAsDitc(self):
        with open(self.file_path, "r", encoding="utf-8") as json_f:
            return json.load(json_f)

    def getCriticalPath(self):
        criticalPathInfo = OrderedDict()
        for item in self.profiled_data:
            if "criticalPath" in item:
                criticalPathArr = item["criticalPath"]
        for index in range(len(criticalPathArr)):
            currTaskID = criticalPathArr[index]
            for item in self.profiled_data:
                if "objs" in item:
                    for obj in item["objs"]:
                        if("activityId" in obj and obj["activityId"] == currTaskID):
                            # print(obj)
                            criticalPathInfo[currTaskID] = obj
        return criticalPathInfo

    def getCriticalPathList(self):
        for item in self.profiled_data:
            if "criticalPath" in item:
                return item["criticalPath"]

    def getDependedElements(self):
        # Get a list that contains all the files that have dependency on others
        finalResutl = []
        for item in self.profiled_data:
            if "id" in item and item["id"] == "Deps":
                for dep in item["objs"]:
                    if dep["a1"] not in finalResutl:
                        finalResutl.append(dep["a1"])
                    if dep["a2"] not in finalResutl:
                        finalResutl.append(dep["a2"])
        return finalResutl

    def getDetailWithId(self, activityId):
        # get an activity about its detail based on the activity ID
        for item in self.profiled_data:
            if "objs" in item and item["id"] != "Deps":
                for obj in item["objs"]:
                    if obj["activityId"] == activityId:
                        # print(obj)
                        return obj

    def getDependencyTreeNodes(self):
        # TODO: NOT FINISHED, IMPLEMENT THIS!!
        # Dependency Resolver
        dependencyTreeNodes = []
        for activityId in self.dependedElements:
            # create a tree node
            node = DependencyTreeNode(activityId, self.getDetailWithId(activityId))
            for item in self.profiled_data:
                if "id" in item and item["id"] == "Deps":
                    for dep in item["objs"]:
                        if(dep["a1"] == activityId):
                            # child found
                            childActivityId = dep["a2"]
                            node.addChild(childActivityId)

                        if(dep["a2"] == activityId):
                            # parent found
                            ancestorActivityId = dep["a1"]
                            node.findAncestors(ancestorActivityId)
            dependencyTreeNodes.append(node)
        return dependencyTreeNodes

class DependencyTree:
    def __init__(self, dependencyTreeNodes, criticalPathNodes):
        self.dependencyTreeNodes = dependencyTreeNodes
        self.criticalPathNodes = criticalPathNodes
        self.dependencyTree = None

    def getNode(self, activityId):
        for node in self.dependencyTreeNodes:
            if(node.activityID == activityId):
                return node

    def trimTree(self):
        for treeNode in self.dependencyTreeNodes:
            if(len(treeNode.ancestors) > 1):
                # find the parent
                for ancestor in treeNode.ancestors:
                    for anotherAncestor in treeNode.ancestors:
                        anotherAncestorNode = self.getNode(anotherAncestor)
                        if ancestor != anotherAncestor and ancestor in anotherAncestorNode.children:
                            self.dependencyTreeNodes[self.dependencyTreeNodes.index(self.getNode(anotherAncestor))].children.remove(treeNode.activityID)
                            self.dependencyTreeNodes[self.dependencyTreeNodes.index(self.getNode(treeNode.activityID))].ancestors.remove(anotherAncestor)

    def prepareDrawingTree(self):
        # get edges and nodes ready for tree drawing
        # rearrange the nodes and edges with a level relation

        dependencyTree = self.dependencyTreeNodes
        nodes = []
        edges = []
        # use q as a queue
        # q = []
        # for treeNode in dependencyTree:
        #     if(len(treeNode.ancestors) == 0):
        #         q.append(treeNode.activityID)  # first the root
        # while len(q) != 0:
        #     # use a list to store the same level nodes
        #     tmp = []
        #     length = len(q)
        #     for i in range(length):
        #         r = q.pop()
        #         # get the node
        #         parentNode = self.getNode(r)
        #         for child in parentNode.children:
        #             q.append(child)
        #         tmp.append(r)
        #     nodes.append(tmp)
        for treeNode in dependencyTree:
            # parent -> thisNode
            nodes.append(treeNode.activityID)
            for ancestor in treeNode.ancestors:
                edges.append(tuple([ancestor, treeNode.activityID]))
            for child in treeNode.children:
                edges.append(tuple([treeNode.activityID, child]))
        # sort the nodes base on task and task no
        # Network->Scripting->Loading
        networkingTask = []
        loadingTask = []
        scriptingTask = []

        for task in nodes:
            taskName = task.split("_")[0]
            taskNo = task.split("_")[1]
            if(taskName == "Networking"):
                networkingTask.append(taskNo)
            if(taskName == "Loading"):
                loadingTask.append(taskNo)
            if(taskName == "Scripting"):
                scriptingTask.append(taskNo)
        networkingTask = sorted(networkingTask)
        loadingTask = sorted(loadingTask)
        scriptingTask = sorted(scriptingTask)
        nodes = []
        for index in range(len(networkingTask)):
            nodes.append("Networking" + "_" + str(networkingTask[index]))
        for index in range(len(loadingTask)):
            nodes.append("Loading" + "_" + str(loadingTask[index]))
        for index in range(len(scriptingTask)):
            nodes.append("Scripting" + "_" + str(scriptingTask[index]))

        return nodes, edges

    def showTheTree(self):
        for treeNode in self.dependencyTreeNodes:
            print("ActivityID:", treeNode.activityID)
            print("Ancestors:{}".format(treeNode.ancestors))
            print("Children:{}".format(treeNode.children))
            print("Detail:{}".format(str(treeNode.detail)))
            print("+=========================================================================+")

    def getOverallTimeConsumption(self, threshold):
        # Get the total time consumption for the node and its children/grandchildren
        overallTimeConsumption = 0
        allTreeNodeNames = [treeNode.activityID for treeNode in self.dependencyTreeNodes]
        # TODO: sort nodes based on priority/cost efficiency
        cut = []
        for treeNode in self.dependencyTreeNodes:
            if treeNode.activityID in allTreeNodeNames:
                startTime = treeNode.detail["startTime"]
                endTime = treeNode.detail["endTime"]
                timeConsumption = endTime - startTime
                if overallTimeConsumption >= threshold:
                    break
                else:
                    overallTimeConsumption += timeConsumption
                    cut.append(treeNode.activityID)
                    allTreeNodeNames.remove(treeNode.activityID)
                for child in treeNode.children:
                    childNode = self.getNode(child)
                    startTime = childNode.detail["startTime"]
                    endTime = childNode.detail["endTime"]
                    timeConsumption = endTime - startTime
                    if overallTimeConsumption >= threshold:
                        break
                    else:
                        print(child)
                        overallTimeConsumption += timeConsumption
                        cut.append(child)
                        print(allTreeNodeNames)
                        try:
                            allTreeNodeNames.remove(child)
                        except:
                            continue
        print("Overall Time Consumption:", overallTimeConsumption)
        print("DAG Cut:", cut)
        print("TASK NUMBER: ", len(cut))
        return cut


    def drawDependencyTree(self, currentSite, threshold):
        plotly.tools.set_credentials_file(username='sipuora', api_key='1CUcYmEgufGedLqAbMHB')
        # Draw the tree for Demo purpose
        nr_vertices = len(self.dependencyTreeNodes)  # how many nodes are there
        dependencyTree = self.dependencyTreeNodes
        DAGCut = self.getOverallTimeConsumption(threshold)
        DAGCut = [node[0] + "_" + node[node.index("_") +1 : ] for node in DAGCut]
        nodes_ori, edges = self.prepareDrawingTree()
        edges = [tuple([edge[0][0] + "_" + edge[0][edge[0].index("_") + 1 :], edge[1][0] + "_" + edge[1][edge[1].index("_") + 1 :]])for edge in edges]
        nodes_ori = [node[0] + "_" + node[node.index("_") + 1 :] for node in nodes_ori]
        print(len(nodes_ori))
        nodes = [node for node in nodes_ori if node not in DAGCut]

        print(len(nodes))
        print(edges)
        # G = Graph.Tree(nr_vertices, 2)  # 2 stands for children number

        # print(nodes, edges)
        v_label = list(map(lambda node: node.activityID, self.dependencyTreeNodes))
        # print(v_label)



        dmin=5
        # pos=nx.planar_layout(G)
        ncenter=0
        # for n in pos:
        #     x,y = pos[n]
        #     d = (x - 0.5) ** 2 + (y - 0.5) ** 2
        #     if d < dmin:
        #         ncenter = n
        #         dmin = d

        ###############################################################################
        # Add edges as disconnected lines in a single trace and nodes as a scatter trace
        # Need to create a layout when doing
        # separate calls to draw nodes and edges


        G = nx.DiGraph() # Create Directed Graphs
        G.add_nodes_from(nodes_ori)
        G.add_edges_from(edges)

        # modify gaps between nodes
        # df = pd.DataFrame(index=G.nodes(), columns=G.nodes())
        # for row, data in nx.shortest_path_length(G):
        #     for col, dist in data.items():
        #         df.loc[row, col] = dist
#
        # df = df.fillna(df.max().max() * 0.6)

        pos = nx.kamada_kawai_layout(G)
        # pos = {'L_1':[0.45323407, 0.38300876], 'S_8': [-0.1200502 ,  0.89004281], 'N_1': [ 0.92090981, -0.06400148], 'N_2':[0.71877908, 0.5896263 ], 'S_6': [-0.47512574,  0.07605371], 'N_3':[0.35466946, 0.78284009], 'N_5':[-0.85383971,  0.12130521], 'N_7':[-0.46770779,  0.76354273], 'S_7':[-0.75269343,  0.48778184], 'L_2':[ 0.41769869, -0.15407188], 'S_4':[-0.54087218, -0.51841815], 'S_0':[0.10216507, 0.38916522], 'S_2':[-0.21226628, -0.47335229], 'L_3':[ 0.14853618, -0.59285619], 'N_4': [-0.05602928, -1], 'S_3':[-0.65497334, -0.24656378], 'N_6':[-0.38828246,  0.44194564], 'N_0': [0.00702252, -0.17041745], 'S_5': [ 0.44685786, -0.6439212], 'L_4': [-0.29849128, -0.79035], 'S_1': [ 0.62130693, -0.39901267], 'L_0': [0.62915201, 0.1276528 ]}

        print(pos)
        nx.draw_networkx_nodes(G, pos, cmap=plt.get_cmap('jet'),
                               node_color='red', node_size=1200, nodelist=nodes)
        nx.draw_networkx_nodes(G, pos, cmap=plt.get_cmap('jet'),
                               node_color='green', node_size=1200, nodelist=DAGCut)
        nx.draw_networkx_labels(G, pos)
        nx.draw_networkx_edges(G, pos, edgelist=edges, width=3, arrowstyle='-|>')
        plt.title('Google Dependency Graph Cut Threshold={}ms'.format(threshold), fontsize='large', fontweight = 'bold')
        # save image
        filename = currentSite + " " + "threshold " + str(threshold)
        filePath = os.path.abspath(os.path.join(IMAGE_SAVE_PATH, filename))
        plt.savefig(filePath, format="png", dpi=1000)

        plt.show()

        ###############################################################################

        # trace info
        # edge_trace = go.Scatter(
        #     x=[],
        #     y=[],
        #     line=dict(width=0.5,color='#888'),
        #     hoverinfo='none',
        #     mode='lines'
        # )


        # for edge in G.edges():
        #     x0,y0 = G.node[edge[0]]['pos']
        #     x1,y1 = G.node[edge[1]]['pos']
        #     print(x0,y0)
        #     print(x1,y1)
        #     edge_trace['x'] += tuple([x0,x1,None])
        #     edge_trace['y'] += tuple([y0,y1,None])

        # node_trace = go.Scatter(
        #     x=[],
        #     y=[],
        #     text=[],
        #     mode='markers',
        #     hoverinfo='text',
        #     marker=dict(
        #         showscale=True,
        #         # colorscale options
        #         # 'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
        #         # 'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
        #         # 'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
        #         colorscale='YlGnBu',
        #         reversescale=True,
        #         color=[],
        #         size=10,
        #         colorbar=dict(
        #             thickness=15,
        #             title='Node Connections',
        #             xanchor='left',
        #             titleside='right'
        #         ),
        #         line=dict(width=2)))

        # for node in G.nodes():
        #     x, y = G.node[node]['pos']
        #     node_trace['x'] += tuple([x])
        #     node_trace['y'] += tuple([y])

        # Create node points
        # Color node points by the number of dependencies.

        # for node, adjacencies in enumerate(G.adjacency()):
        #     node_trace['marker']['color'] += tuple([len(adjacencies[1])])
        #     node_info = '# of connections: ' + str(len(adjacencies[1]))  # TODO:Change node_info here
        #     node_trace['text'] += tuple([node_info])

        # Create graph
        # fig = go.Figure(data=[edge_trace, node_trace],
        #                 layout=go.Layout(
        #                     title='<br>Network graph made with Python',
        #                     titlefont=dict(size=16),
        #                     showlegend=False,
        #                     hovermode='closest',
        #                     margin=dict(b=20, l=5, r=5, t=40),
        #                     annotations=[dict(
        #                         text="Python code: <a href='https://plot.ly/ipython-notebooks/network-graphs/'> https://plot.ly/ipython-notebooks/network-graphs/</a>",
        #                         showarrow=False,
        #                         xref="paper", yref="paper",
        #                         x=0.005, y=-0.002)],
        #                     xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        #                     yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
#
        # py.iplot(fig, filename='networkx')

        # lay = G.layout('rt')
        # position = {k : lay[k] for k in range(nr_vertices)}
        # print(position)
        # Y = [lay[k][1] for k in range(nr_vertices)]
        # M = max(Y)
#
        # es = EdgeSeq(G) # sequence of edges
        # E = edges # list of edges
        # L = len(position)
        # Xn = [position[k][0] for k in range(L)]
        # Yn = [2 * M - position[k][1] for k in range(L)]
        # Xe = []
        # Ye = []
#
        # for edge in E:
        #     Xe += [position[nodes.index(edge[0])][0], position[nodes.index(edge[1])][0], None]
        #     Ye += [2 * M - position[nodes.index(edge[0])][1], 2 * M - position[nodes.index(edge[1])][1], None]
##
        # labels = v_label  # TODO: change the label later
        # details_text = list(map(lambda node: str(node.detail), self.dependencyTreeNodes))
##
        # # create Plotly Traces
        # lines = go.Scatter(x=Xe,
        #                    y=Ye,
        #                    mode='lines',
        #                    line=dict(color='rgb(210,210,210)', width=1),
        #                    hoverinfo='none'
        #                    )
        # dots = go.Scatter(x=Xn,
        #                   y=Yn,
        #                   mode='markers',
        #                   name='',
        #                   marker=dict(symbol='dot',
        #                               size=70,
        #                               color='#6175c1',  # '#DB4551',
        #                               line=dict(color='rgb(50,50,50)', width=1)
        #                               ),
        #                   text="None",
        #                   hoverinfo='text',
        #                   opacity=2.8
        #                   )
#
        # # create annotations
        # if len(v_label) != L:
        #     raise ValueError('The lists pos and text must have the same len')
        # annotations = go.Annotations()
        # for k in range(L):
        #     annotations.append(
        #         go.Annotation(
        #             text=labels[k],  # or replace labels with a different list for the text within the circle
        #             x=position[k][0], y=2 * M - position[k][1],
        #             xref='x1', yref='y1',
        #             font=dict(color='rgb(250,250,250)', size=10),
        #             showarrow=False))
        # axis = dict(showline=False,  # hide axis line, grid, ticklabels and  title
        #             zeroline=False,
        #             showgrid=False,
        #             showticklabels=False,
        #             )
        # layout = dict(title='Dependency Tree',
        #               annotations=annotations,
        #               font=dict(size=12),
        #               showlegend=False,
        #               xaxis=go.XAxis(axis),
        #               yaxis=go.YAxis(axis),
        #               margin=dict(l=40, r=40, b=85, t=100),
        #               hovermode='closest',
        #               plot_bgcolor='rgb(248,248,248)'
        #               )
        # data = go.Data([lines, dots])
        # fig = dict(data=data, layout=layout)
        # fig['layout'].update(annotations=annotations)
        # py.iplot(fig, filename='Tree-Reingold-Tilf')

def sortDependencyOut(url, testNo, threshold, drawTree=False):
    """
    sort the dependency tree out,
    :param url: webpage to analyze
    :param testNo: Number of test conducted
    :param thresholds: loading time threshold, for DAG cut.
    :return: true if the data is saved successfully, false the otherwise
    """
    AnalysisNode = DependencyAnalysis(url=url, testNo=testNo)
    DBInteract = DBInteractModule()

    NODE_DB_NAME = "YPTN-DEPENDENCY-Nodes"
    EDGE_DB_NAME = "YPTN-DEPENDENCY-Edges"
    CRITICAL_PATH_DB_NAME = "YPTN-CRITICALPATH-Nodes"
    CUT_DB_NAME = "YPTN-DAGCUT"

    # Get critical path nodes and dependency nodes for later use
    criticalPathList = AnalysisNode.getCriticalPathList()
    dependencyTreeNodes = AnalysisNode.getDependencyTreeNodes()

    WebpageDependencyTree = DependencyTree(dependencyTreeNodes, criticalPathList)
    # trim the tree to get rid of loops
    WebpageDependencyTree.trimTree()
    # get all the nodes and edges
    nodes, edges = WebpageDependencyTree.prepareDrawingTree()
    # get the DAG cut
    DAGCut = WebpageDependencyTree.getOverallTimeConsumption(threshold=threshold)

    # save the nodes with details
    nodeObjects = []
    for nodeId in nodes:
        # print(nodeId)
        nodeDetail = AnalysisNode.getDetailWithId(nodeId)
        # print(nodeDetail)
        nodeObjects.append(nodeDetail)
    DBInteract.addMany(dbName=NODE_DB_NAME, collectionName=url, objects=nodeObjects)

    # save the edges with details
    edgeObjects =[]
    for edge in edges:
        parent = edge[0]
        child = edge[1]
        print(parent, child)
        parentDetail = AnalysisNode.getDetailWithId(parent)
        childDetail = AnalysisNode.getDetailWithId(child)
        print(parentDetail)
        print(childDetail)
        edgeObject = {
            "parentId": parent,
            "childId": child,
            "parentDetail": parentDetail,
            "childDetail": childDetail
        }
        edgeObjects.append(edgeObject)
    DBInteract.addMany(dbName=EDGE_DB_NAME, collectionName=url, objects=edgeObjects)

    # save the critical path nodes with detail
    criticalPathObjects = []
    for criticalPathNode in criticalPathList:
        criticalPathNodeDetail = AnalysisNode.getDetailWithId(criticalPathNode)
        criticalPathObjects.append(criticalPathNodeDetail)
    DBInteract.addMany(dbName=CRITICAL_PATH_DB_NAME, collectionName=url, objects=criticalPathObjects)

    # save the DAG cut nodes with detail
    DAGCutObjects = []
    for DAGCutNode in DAGCut:
        DAGCutNodeDetail = AnalysisNode.getDetailWithId(DAGCutNode)
        DAGCutObjects.append(DAGCutNodeDetail)

    DBInteract.addMany(dbName=CUT_DB_NAME, collectionName=url, objects=DAGCutObjects)

    # draw the graph?
    if(drawTree):
        WebpageDependencyTree.drawDependencyTree(currentSite=url, threshold=threshold)

def sigmoid(x):
  return 1 / (1 + math.exp(-x))

def analyzeProfile(url, csvFileTitle):
    profile = DependencyAnalysis(url=url, testNo=0).profiled_data
    defaultWeight = {
        'text/css':256,
        'image':128,
        'application/javascript':64,
        'text/javascript':64,
        'others':32
    }
    analysisRes = []
    for record in profile:
        if('id' in record):
            try:
                objs = record['objs']
                for obj in objs:
                    oneRes = []
                    try:
                        if(obj['activityId'].startswith('Networking')):
                            fileType = obj['mimeType']
                            timeCost = float(obj['endTime']) - float(obj['startTime'])
                            # print("Networking Type", fileType)
                            # print("Time Cost", str(timeCost))
                            if(obj['mimeType'].startswith('image')):
                                priority = round(defaultWeight['image'] / math.pow(timeCost, 1/3))
                                if(priority > defaultWeight['image']):
                                    priority = defaultWeight['image']
                            else:
                                try:
                                    priority = round(defaultWeight[fileType] / math.pow(timeCost, 1/3))
                                    if(priority > defaultWeight[fileType]):
                                        priority = defaultWeight[fileType]
                                except(KeyError):
                                    priority = round(defaultWeight['others'] / math.pow(timeCost, 1/3))
                                    if(priority > defaultWeight['others']):
                                        priority = defaultWeight['others']

                            # print("Priority:", str(round(priority)))
                            oneRes.append(fileType)
                            oneRes.append(timeCost)
                            oneRes.append(priority)
                            # print(oneRes)
                            analysisRes.append(oneRes)
                    except(KeyError):
                        # print(obj)
                        print("{:%Y-%m-%d %H:%M:%S} ignore dependency analysis".format(datetime.datetime.now()))
            except(KeyError):
                # print(record)
                print("{:%Y-%m-%d %H:%M:%S} ignore TCP connection analysis".format(datetime.datetime.now()))
            # print(analysisRes)
            with open(csvFileTitle, 'w') as csvFile:
                writer = csv.writer(csvFile)
                writer.writerow(['FileType', 'TimeCost', 'Priority'])
                writer.writerows(analysisRes)

if __name__ == "__main__":
    # GoogleAnalysis = DependencyAnalysis(url="www.google.com", testNo="0")
    # # GoogleAnalysis.showFilePath()
    # # print(GoogleAnalysis.getCriticalPath())
    # # GoogleAnalysis.getDependedElements()
    # # print(GoogleAnalysis.getDependencyTree())
    # # GoogleAnalysis.drawDependencyTree()
    # # dependencyTree = GoogleAnalysis.getDependencyTree()
    # # print(dependencyTree)
    # dependencyTreeNodes = GoogleAnalysis.getDependencyTreeNodes()
    # criticalPathNodes = GoogleAnalysis.getCriticalPathList()
    # dependencyTree = DependencyTree(dependencyTreeNodes, criticalPathNodes)
    # dependencyTree.trimTree()
    # dependencyTree.showTheTree()
    # thresholds = [0,50,100,150,200,250,300,350,400,450,500]
    # for threshold in thresholds:
    #     dependencyTree.drawDependencyTree(currentSite="Google", threshold=threshold)

    # sortDependencyOut(url="www.github.com", testNo="0", threshold=1000, drawTree=True)
    profileNames = os.listdir(os.path.join(ANALYSIS_FILE_PATH))
    # print(profileNames)
    priorityType = "priorityRoot3"
    for profile in profileNames:
        url = profile.split('.json')[0].split('_')[1]
        analyzeProfile(url=url,
                       csvFileTitle=os.path.join(PRIORITY_ANALYSIS_FILE_PATH,
                                                 "{}_{}_{}.csv".format(url, priorityType, str(round(time.time())))))
