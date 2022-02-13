import json
from collections import Counter

from math import log2


def build_transition_graph(titles, graph=None):
    if not graph:
        graph = {}
    for t_idx in range(len(titles)):
        title = titles[t_idx]
        if t_idx == len(titles) - 1:
            break
        if title not in graph:
            graph[title] = {}
        title_next = titles[t_idx + 1]

        if title_next not in graph[title]:
            graph[title][title_next] = 0
        graph[title][title_next] += 1

    return graph


if __name__ == '__main__':
    titles_seq = open('log_all_processed_window_titles.txt').read().splitlines()
    titles_counter = Counter(titles_seq)
    titles_unique = list(titles_counter.keys())
    titles_idxs = [titles_unique.index(t) for t in titles_seq]
    print(f'Total titles = {len(titles_seq)}')
    print(f'Unique titles = {len(titles_unique)}')

    transition_graph = build_transition_graph(titles_idxs)
    # print(transition_graph)
    d3js_nodes = [{"id": "%d" % title_idx, "group": 1, "sentence": titles_seq[title_idx]}
                  for title_idx in transition_graph]
    d3js_links = []
    for source_node in transition_graph:
        for target_node in transition_graph[source_node]:
            d3js_links.append({
                "source": source_node,
                "target": target_node,
                "value": "%d" % round(1 + log2(transition_graph[source_node][target_node]))
            })

    json.dump({
        "nodes": d3js_nodes,
        "links": d3js_links
    }, open("transitions_graph.json", "w", encoding="utf-8"),
        ensure_ascii=False,
        indent=2
    )
