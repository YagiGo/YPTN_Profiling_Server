# draw the dependency tree base on the analysis json
# TODO: Change to DB access when ready
import os,json
from collections import OrderedDict
import plotly
import plotly.plotly as py
import plotly.graph_objs as go
import matplotlib.pyplot as plt
import networkx as nx
from collections import OrderedDict
from igraph import *
ANALYSIS_FILE_PATH = os.path.abspath(os.path.join(os.curdir, "desktop_livetest"))

class DependencyTreeNode:
    def __init__(self, activityID, detail):
        self.activityID = activityID
        self.ancestors = []
        self.children = []
        self.parent = None
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
        self.file_path = os.path.join(ANALYSIS_FILE_PATH, self.url, "run_0", "analysis", "{}_{}.json".format(testNo, url))
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
            if "objs" in item:
                for obj in item["objs"]:
                    if obj["activityId"] == activityId:
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
    def __init__(self, dependencyTreeNodes):
        self.dependencyTreeNodes = dependencyTreeNodes
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
            print("ActivityID:%s", treeNode.activityID)
            print("Ancestors:{}".format(treeNode.ancestors))
            print("Children:{}".format(treeNode.children))
            print("+=========================================================================+")



    def drawDependencyTree(self):
        plotly.tools.set_credentials_file(username='sipuora', api_key='1CUcYmEgufGedLqAbMHB')
        # Draw the tree for Demo purpose
        nr_vertices = len(self.dependencyTreeNodes)  # how many nodes are there
        dependencyTree = self.dependencyTreeNodes
        nodes, edges = self.prepareDrawingTree()
        G = Graph.Tree(nr_vertices, 2)  # 2 stands for children number

        # print(nodes, edges)
        v_label = list(map(lambda node: node.activityID, self.dependencyTreeNodes))
        # print(v_label)

        # G = nx.DiGraph() # Create Directed Graphs
        # G.add_nodes_from(nodes)
        # G.add_edges_from(edges)

        dmin=5
        # pos=nx.planar_layout(G)
        # pos = nx.get_node_attributes(G, 'pos')
        ncenter=0
        # for n in pos:
        #     x,y = pos[n]
        #     d = (x - 0.5) ** 2 + (y - 0.5) ** 2
        #     if d < dmin:
        #         ncenter = n
        #         dmin = d
        # Add edges as disconnected lines in a single trace and nodes as a scatter trace
        # Need to create a layout when doing
        # separate calls to draw nodes and edges
        # nx.draw_networkx_nodes(G, pos, cmap=plt.get_cmap('jet'),
        #                        node_color='red', node_size=500)
        # nx.draw_networkx_labels(G, pos)
        # nx.draw_networkx_edges(G, pos, edgelist=edges, arrows=False)
        # plt.show()
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

        lay = G.layout('rt')
        position = {k : lay[k] for k in range(nr_vertices)}
        print(position)
        Y = [lay[k][1] for k in range(nr_vertices)]
        M = max(Y)

        es = EdgeSeq(G) # sequence of edges
        E = edges # list of edges
        L = len(position)
        Xn = [position[k][0] for k in range(L)]
        Yn = [2 * M - position[k][1] for k in range(L)]
        Xe = []
        Ye = []

        for edge in E:
            Xe += [position[nodes.index(edge[0])][0], position[nodes.index(edge[1])][0], None]
            Ye += [2 * M - position[nodes.index(edge[0])][1], 2 * M - position[nodes.index(edge[1])][1], None]
#
        labels = v_label  # TODO: change the label later
        details_text = list(map(lambda node: str(node.detail), self.dependencyTreeNodes))
#
        # create Plotly Traces
        lines = go.Scatter(x=Xe,
                           y=Ye,
                           mode='lines',
                           line=dict(color='rgb(210,210,210)', width=1),
                           hoverinfo='none'
                           )
        dots = go.Scatter(x=Xn,
                          y=Yn,
                          mode='markers',
                          name='',
                          marker=dict(symbol='dot',
                                      size=70,
                                      color='#6175c1',  # '#DB4551',
                                      line=dict(color='rgb(50,50,50)', width=1)
                                      ),
                          text="None",
                          hoverinfo='text',
                          opacity=2.8
                          )

        # create annotations
        if len(v_label) != L:
            raise ValueError('The lists pos and text must have the same len')
        annotations = go.Annotations()
        for k in range(L):
            annotations.append(
                go.Annotation(
                    text=labels[k],  # or replace labels with a different list for the text within the circle
                    x=position[k][0], y=2 * M - position[k][1],
                    xref='x1', yref='y1',
                    font=dict(color='rgb(250,250,250)', size=10),
                    showarrow=False))
        axis = dict(showline=False,  # hide axis line, grid, ticklabels and  title
                    zeroline=False,
                    showgrid=False,
                    showticklabels=False,
                    )
        layout = dict(title='Dependency Tree',
                      annotations=annotations,
                      font=dict(size=12),
                      showlegend=False,
                      xaxis=go.XAxis(axis),
                      yaxis=go.YAxis(axis),
                      margin=dict(l=40, r=40, b=85, t=100),
                      hovermode='closest',
                      plot_bgcolor='rgb(248,248,248)'
                      )
        data = go.Data([lines, dots])
        fig = dict(data=data, layout=layout)
        fig['layout'].update(annotations=annotations)
        py.iplot(fig, filename='Tree-Reingold-Tilf')


GoogleAnalysis = DependencyAnalysis(url="www.google.com", testNo="0")

if __name__ == "__main__":
    # GoogleAnalysis.showFilePath()
    # print(GoogleAnalysis.getCriticalPath())
    # GoogleAnalysis.getDependedElements()
    # print(GoogleAnalysis.getDependencyTree())
    # GoogleAnalysis.drawDependencyTree()
    # dependencyTree = GoogleAnalysis.getDependencyTree()
    # print(dependencyTree)
    dependencyTreeNodes = GoogleAnalysis.getDependencyTreeNodes()
    dependencyTree = DependencyTree(dependencyTreeNodes)
    dependencyTree.trimTree()
    dependencyTree.showTheTree()
    dependencyTree.drawDependencyTree()