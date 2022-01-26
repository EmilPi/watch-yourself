from collections import Counter
from glob import glob

from console import choose_from_keyboard
from utils_tokenization import untokenize


def nice_print_top_k(counter, k):
    most_common = counter.most_common(k)
    biggest_count = most_common[0][1]
    biggest_count_char_length = len(str(biggest_count))
    for value, count in most_common:
        if isinstance(value, (tuple, list)):
            value = ' '.join(value)
            value = untokenize(value)
        print(('%s' % count).rjust(biggest_count_char_length), ':', value)


if __name__ == '__main__':
    fpaths = glob('log_all_merged*_train.txt')
    fpath = choose_from_keyboard(fpaths)
    print(f'{fpath} chosen')

    lines = open(fpath, 'r', encoding='utf-8').read().splitlines()
    min_length, max_length = 30, 30
    token_group_lengths = range(min_length, max_length + 1)
    counters = [Counter() for _ in token_group_lengths]

    all_tokens = []
    for line in lines:
        all_tokens.extend(line.split(' '))
    for idx in range(len(all_tokens) - max_length):
        if idx % 10000 == 0:
            print(f'{idx} of {len(all_tokens)} counted.')
        token_of_max_length = tuple(all_tokens[idx:(idx + max_length)])
        for length in token_group_lengths:
            # if len(all_tokens) - idx < length:
            #     continue

            counters[length - min_length].update([token_of_max_length[:length]])

    for length, counter in enumerate(counters, min_length):
        print(f'LENGTH = {length}')
        nice_print_top_k(counter, 3 + max_length - length)
