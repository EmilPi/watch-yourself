from collections import Counter
from glob import glob

from console import choose_from_keyboard

if __name__ == '__main__':
    fpaths = glob('log_all_merged*_train.txt')
    fpath = choose_from_keyboard(fpaths)
    print(f'{fpath} chosen')

    lines = open(fpath, 'r', encoding='utf-8').read().splitlines()
    token_group_lengths = range(1, 10 + 1)
    counters = [Counter() for _ in token_group_lengths]

    all_tokens = []
    for line in lines:
        all_tokens.extend(line.split(' '))
    for idx in range(len(all_tokens)):
        if idx % 10000 == 0:
            print(f'{idx} of {len(all_tokens)} counted.')
        for length in token_group_lengths:
            if len(all_tokens) - idx < length:
                continue

            counters[length - 1].update([tuple(all_tokens[idx:(idx + length)])])

    for length, counter in enumerate(counters, 1):
        print(counter.most_common(12 - length), f'length = {length}')
