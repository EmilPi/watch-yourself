import json
from collections import Counter
from math import log2

from log_preprocess import dump_features
from utils import json_load


def build_transition_graph(seq, graph=None):
    if not graph:
        graph = {}
    for t_idx in range(len(seq) - 1):
        seq_el = seq[t_idx]
        seq_el_next = seq[t_idx + 1]
        if seq_el not in graph:
            graph[seq_el] = {}

        if seq_el_next not in graph[seq_el]:
            graph[seq_el][seq_el_next] = 0
        graph[seq_el][seq_el_next] += 1

    if seq[-1] not in graph:
        graph[seq[-1]] = {}

    return graph


SETTINGS = json_load('settings.json')
BLACKLISTED_PAGES_PARTS = SETTINGS['BLACKLISTED_PAGES_PARTS']
BROWSERS_LIST = SETTINGS['BROWSERS_LIST']


# this is only an example!
def get_group(title):
    if 'JIRA' in title or 'Microsoft Teams' in title:
        return 1
    elif any([b.lower() in title.lower() for b in BLACKLISTED_PAGES_PARTS]):
        return 2
    elif 'Mozilla Firefox' in title or 'Google Chrome' in title:
        return 3
    elif 'VLC media player' in title:
        return 4
    elif ('emil@' in title) and ('Lenovo' in title):
        return 5
    else:
        return 0


if __name__ == '__main__':
    dump_features(['window_titles'], './')
    titles_seq = open('log_all_processed_window_titles.txt').read().splitlines()[:]
    titles_counter = Counter(titles_seq)
    titles_unique = list(titles_counter.keys())
    titles_idxs = [titles_unique.index(t) for t in titles_seq]
    print(f'Total titles = {len(titles_seq)}')
    print(f'Unique titles = {len(titles_unique)}')

    transition_graph = build_transition_graph(titles_idxs)
    # print(transition_graph)
    d3js_nodes = [{
        "id": title_idx,
        "group": get_group(titles_unique[title_idx]), "sentence": titles_unique[title_idx],
        "total_out": sum(transition_graph[title_idx].values())
    } for title_idx in transition_graph]
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
