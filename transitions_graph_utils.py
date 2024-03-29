import http.server
import json
import re
import socketserver
from collections import Counter
from math import log2

from log_preprocess import dump_features
from utils_text import is_browser_window_title
from vars import BLACKLISTED_WINDOWS_TITLES_PARTS, BROWSERS_WINDOWS_TITLES_STRINGS, WINDOWS_GROUPS


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


def is_browser_entry_point(title):
    for browser in BROWSERS_WINDOWS_TITLES_STRINGS:
        if title.lower() == browser.lower():
            return True
        for prefix in ['New Tab', 'Новая вкладка']:
            for delim in ['—', '-']:
                if title.lower() == f'{prefix} {delim} {browser}'.lower():
                    return True
    return False


def is_windows_switching(title):
    return title in ['Task Switching', 'Task View', '']


def get_filter(title):
    return is_browser_entry_point(title) \
           or is_windows_switching(title)


# this is only an example!
def get_group(title):
    base_group_idx = 1

    if title == RARE_TITLE_REPLACEMENT:
        return base_group_idx * 100
    base_group_idx += 1

    if any([b.lower() in title.lower() for b in BLACKLISTED_WINDOWS_TITLES_PARTS]):
        return base_group_idx * 100
    base_group_idx += 1

    for group in WINDOWS_GROUPS.values():
        if any([string.lower() in title.lower() for string in group['strings']]) \
                or any([re.search(pattern.lower(), title.lower()) for pattern in group['patterns']]):
            return base_group_idx * 100
        base_group_idx += 1

    if is_browser_window_title(title):
        return 4

    return 0


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs): super().__init__(*args, directory='./', **kwargs)


NODE_LIMIT = 400
RARE_TITLE_REPLACEMENT = '<SOME~RARE~TITLE>'
DONT_PLOT_RARE = True
PATH = '.'
if __name__ == '__main__':
    dump_features(['window_titles'], f'{PATH}/')
    titles_seq = open(f'{PATH}/log_all_processed_window_titles.txt', encoding='utf-8').read().splitlines()
    # filtering some titles which only serve for going somehere (like when you click Atl+Tab to switch between windows)
    titles_seq = [t for t in titles_seq if not get_filter(t)]
    titles_counter = Counter(titles_seq)
    titles_unique = list(titles_counter.keys())
    titles_unique_rare_joined = titles_counter.most_common(NODE_LIMIT - 1)
    print(f'Total titles = {len(titles_seq)}')
    print(f'Unique titles = {len(titles_unique)}')
    if len(titles_unique) < NODE_LIMIT:
        titles_unique_rare_joined = titles_unique
    else:
        titles_unique_rare_joined = [title for title, count in titles_counter.most_common(NODE_LIMIT - 1)] \
                                    + [RARE_TITLE_REPLACEMENT]
        titles_seq = [t if t in titles_unique_rare_joined else titles_unique_rare_joined[-1]
                      for t in titles_seq]

    titles_idxs = [titles_unique_rare_joined.index(t) for t in titles_seq]
    transition_graph = build_transition_graph(titles_idxs)
    # print(transition_graph)
    d3js_nodes = [{
        "id": title_idx,
        "group": get_group(titles_unique_rare_joined[title_idx]),
        "sentence": titles_unique_rare_joined[title_idx],
        "total_out": sum(transition_graph[title_idx].values())
    } for title_idx in transition_graph if (title_idx != len(titles_unique_rare_joined) - 1 or not DONT_PLOT_RARE)]
    d3js_links = []
    for source_title_idx in transition_graph:
        if source_title_idx == len(transition_graph) - 1 and DONT_PLOT_RARE:
            continue
        for target_title_idx in transition_graph[source_title_idx]:
            if target_title_idx == len(transition_graph) - 1 and DONT_PLOT_RARE:
                continue
            d3js_links.append({
                "source": source_title_idx,
                "target": target_title_idx,
                "value": 1 + log2(1 + transition_graph[source_title_idx][target_title_idx])
            })

    json.dump({
        "nodes": d3js_nodes,
        "links": d3js_links
    }, open("transitions_graph.json", "w", encoding="utf-8"),
        ensure_ascii=False,
        indent=2
    )

    PORT = 8000
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("serving at port", PORT)
        html_file_name = 'transitions_graph_view.html'
        print(f'open http://localhost:{PORT}/{html_file_name} in browser;'
              f' press Ctrl+C in this terminal to stop serving.')
        httpd.serve_forever()
