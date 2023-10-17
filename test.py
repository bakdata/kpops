import asyncio
import random as rnd
import networkx as nx


graph = nx.DiGraph()

graph.add_node(0)
graph.add_node(1)
graph.add_node(2)
graph.add_node(3)
graph.add_node(4)
graph.add_node(5)
graph.add_node(6)
graph.add_node(7)
graph.add_node(8)


graph.add_edge(0, 1)
graph.add_edge(1, 2)
graph.add_edge(1, 3)
graph.add_edge(2, 4)
graph.add_edge(2, 5)
graph.add_edge(5, 6)
graph.add_edge(5, 7)
graph.add_edge(7, 8)
graph.add_edge(6, 8)


async def test(node):
    print("Begin with task execution: ", node)
    if node == 4:
        await asyncio.sleep(10)
    print("End with task execution: ", node)


async def myself_and_others(myself, others):
    await myself
    await asyncio.gather(*others)


track = {}
initialization = {}


async def visit_node(node):
    my_and_mysubtasks = []
    for successor in graph.successors(node):
        tasks_node = await visit_node(successor)
        my_and_mysubtasks.append(tasks_node)

    my_subtasks = myself_and_others(initialization[node], my_and_mysubtasks)
    track[node] = my_subtasks

    return my_subtasks


async def begin():
    for node in graph:
        initialization[node] = test(node)
    result = await visit_node(0)
    await result
    print(track)
    print("x")

asyncio.run(begin())
