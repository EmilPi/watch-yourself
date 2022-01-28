from collections import Counter
from glob import glob

from console import choose_from_keyboard
from utils_tokenization import untokenize


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


if __name__ == '__main__':
    fpaths = glob('log_all_merged*_train.txt')
    fpath = choose_from_keyboard(fpaths)
    print(f'{fpath} chosen')

    lines = open(fpath, 'r', encoding='utf-8').read().splitlines()
    # token_group_lengths = [14]
    token_group_lengths = [1, 2, 4, 8, 16, 32]
    # token_group_lengths = range(1, 32+1)
    min_length, max_length = min(token_group_lengths), max(token_group_lengths)
    counters_dict = {length: Counter() for length in token_group_lengths}

    counted_tokens_length = 0
    for line_idx, line in enumerate(lines):
        tokens = line.split(' ')
        expected_tokens_length = int(counted_tokens_length / (line_idx + 1.) * len(lines))
        for idx in range(len(tokens)):
            processed_tokens_length = counted_tokens_length + idx
            if processed_tokens_length % 10000 == 0:
                print(f'{processed_tokens_length} tokens of expected {expected_tokens_length} counted.')
            token_of_max_length = tuple(tokens[idx:(idx + max_length)])
            for length, counter in counters_dict.items():
                if length > len(tokens) - idx:
                    continue

                counter.update([token_of_max_length[:length]])
        counted_tokens_length += len(tokens)

    for length, counter in counters_dict.items():
        print(f'LENGTH = {length}')
        nice_print_top_k(counter,
                         10 + max_length - length,
                         restore_from_tokenized='tokenize' in fpath
                         )
    print('DONE.')
