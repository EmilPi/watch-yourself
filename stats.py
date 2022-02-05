import time
from collections import Counter
from glob import glob
from sys import argv

from console import choose_from_keyboard
from utils_tokenization import untokenize, replace_with_dict


def nice_print_top_k(counter, k, restore_from_tokenized=False):
    most_common = counter.most_common(k)
    biggest_count = most_common[0][1]
    biggest_count_char_length = len(str(biggest_count))
    for value, count in most_common:
        if isinstance(value, (tuple, list)):
            value = ' '.join(value)
            if restore_from_tokenized:
                value = untokenize(value)
        print(('%s' % count).rjust(biggest_count_char_length), ':', value)


def print_token_sequences_frequency(fpath,
                                    token_group_lengths=(1, 2, 4, 8, 16, 32)):
    if isinstance(token_group_lengths, int):
        token_group_lengths = (token_group_lengths,)
    lines = open(fpath, 'r', encoding='utf-8').read().splitlines()
    counters_dict = get_token_sequences_counts(lines, token_group_lengths)

    for length, counter in counters_dict.items():
        print(f'LENGTH = {length}')
        nice_print_top_k(counter,
                         10 + max(token_group_lengths) - length,
                         restore_from_tokenized='tokenize' in fpath
                         )
    print('DONE.')


def get_token_sequences_counts(lines, token_group_lengths):
    if isinstance(token_group_lengths, int):
        token_group_lengths = [token_group_lengths]
    min_length, max_length = min(token_group_lengths), max(token_group_lengths)
    counters_dict = {length: Counter() for length in token_group_lengths}
    # TODO - count with newline tokens (will capture two-line sequences)
    counted_tokens_length = 0
    for line_idx, line in enumerate(lines):
        tokens = line.split(' ')
        expected_tokens_length = int(counted_tokens_length / (line_idx + 1.) * len(lines))
        for idx in range(len(tokens)):
            processed_tokens_length = counted_tokens_length + idx
            if DEBUG and processed_tokens_length % 10000 == 0:
                print(f'\r{processed_tokens_length} tokens of expected {expected_tokens_length} counted.', end='...')
            token_of_max_length = tuple(tokens[idx:(idx + max_length)])
            for length, counter in counters_dict.items():
                if length > len(tokens) - idx:
                    continue

                counter.update([token_of_max_length[:length]])
        counted_tokens_length += len(tokens)

    if DEBUG:
        print('')
    return counters_dict


def replace_infrequent_tokens(fpath=None,
                              tokenized_sentences=None,
                              ignore_least_frequent_tokens_part=.5,
                              token_to_replace_with='<unk>'):
    if fpath is not None and tokenized_sentences is None:
        tokenized_text = open(fpath, 'r', encoding='utf-8').read()
        tokenized_sentences = tokenized_text.splitlines()
    else:
        tokenized_text = '\n'.join(tokenized_sentences)
    tokens_counter = get_token_sequences_counts(tokenized_sentences, 1)
    single_tokens_counter = tokens_counter[1]

    total_tokens = sum([count for token_tuple, count in single_tokens_counter.most_common()])
    total_unique_tokens = len(single_tokens_counter)
    number_of_unique_tokens_to_leave = int((1. - ignore_least_frequent_tokens_part) * total_unique_tokens)
    print(f'Leaving {number_of_unique_tokens_to_leave}'
          f' most frequent unique of {total_unique_tokens}'
          f' unique tokens of total {total_tokens} tokens.')
    replace_dict = {}
    for token_idx, token_data_tuple in enumerate(single_tokens_counter.most_common()):
        if token_idx < number_of_unique_tokens_to_leave:
            continue

        token_tuple, _ = token_data_tuple
        token = token_tuple[0]
        replace_dict[token] = token_to_replace_with

    tokenized_text = replace_with_dict(tokenized_text, replace_dict, pad=' ', unpad=' ')

    return tokenized_text.splitlines()


def build_inclusion_graph(tokenized_sentences=None, fpath=None, ignore_least_frequent_tokens_part = .5):
    if fpath is not None and tokenized_sentences is None:
        tokenized_text = open(fpath, 'r', encoding='utf-8').read()
        tokenized_sentences = tokenized_text.splitlines()

    total_sentences = len(tokenized_sentences)
    if DEBUG:
        num_of_sentences = 10000
        print(f'Processing only {num_of_sentences} of {total_sentences} sentences.')
        tokenized_sentences = tokenized_sentences[:num_of_sentences]
    else:
        num_of_sentences = total_sentences

    t1 = time.time()
    tokenized_sentences = replace_infrequent_tokens(tokenized_sentences=tokenized_sentences,
                                                    ignore_least_frequent_tokens_part=ignore_least_frequent_tokens_part)

    print(f'Replaced {ignore_least_frequent_tokens_part * 100}% least frequent tokens'
          f' in {num_of_sentences} sentences in {"%.3f" % (time.time() - t1)} seconds.')

    sentences_counter = Counter(tokenized_sentences)
    graph = dict()

    for sentence, count in sentences_counter.items():
        _update_graph(graph, sentence)

    return graph


def _update_graph(graph, sentence, parent_sentence=None):
    if graph.get(sentence):
        if parent_sentence:
            if parent_sentence in graph[sentence]:
                return
            else:
                graph[sentence].add(parent_sentence)
    else:
        if parent_sentence:
            graph[sentence] = {parent_sentence}
        else:
            graph[sentence] = set()

    if ' ' not in sentence:
        return

    left_part, _ = sentence.rsplit(' ', 1)
    _, right_part = sentence.split(' ', 1)
    for part in (left_part, right_part):
        _update_graph(graph, part, sentence)


def print_graph(G, only_with_number_of_children_less_than=1):
    No = 0
    for phrase in G:
        num_of_children = len(G.get(phrase)) if G.get(phrase) else 0
        if num_of_children <= only_with_number_of_children_less_than:
            No += 1
            print('No', No)
            print(phrase)
            if num_of_children > 1:
                for child in G[phrase]:
                    print('    ---', child)
            print('----')


DEBUG = 'debug' in argv


if __name__ == '__main__':
    fpaths = glob('log_all_merged*tokenized*_train.txt')
    fpath = choose_from_keyboard(fpaths) if len(fpaths) > 1 else fpaths[0]
    print(f'{fpath} chosen')

    inclusion_graph = build_inclusion_graph(fpath=fpath, ignore_least_frequent_tokens_part=.25)
    print(f'GRAPH length is {len(inclusion_graph)}')

    print_graph(inclusion_graph, only_with_number_of_children_less_than=2)
