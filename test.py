import networkx as nx


graph = nx.DiGraph()

graph.add_node(1)
graph.add_node(2)
graph.add_node(3)
graph.add_node(4)

graph.add_edge(1, 2)
graph.add_edge(1, 3)
graph.add_edge(2, 4)
graph.add_edge(3, 4)

l = list(nx.topological_sort(graph))
print(l)
print(list(nx.bfs_layers(graph,l[0])))
