import argparse
from pathlib import Path

import numpy as np

from features_text import get_window_titles, get_binary_names, \
    get_idle_sequences, get_times_spent_in_window_idle_seq_estimate, \
    get_watch_yourself_or_pc_off, \
    get_times_spent_in_window_change_detect_estimate, \
    get_seq_of_seq, get_tokenized_text, \
    get_delim, join_seq_to_dump_str
from utils_tokenization import replace_with_dict
from vars import ENTRY_DATETIME_FORMAT, DEFAULT_TRAIN_SPLIT


FEATURES_ALL = {
    'binary_names': (get_binary_names, (), {}),
    'window_titles': (get_window_titles, (), {}),
    'window_titles_tokenized': (
        (get_window_titles, (), {}),
        (get_tokenized_text, (), {})
    ),
    'idle_sequences': (get_idle_sequences, (), {}),
    'times_spent_in_window_change_detect_estimate': (get_times_spent_in_window_change_detect_estimate, (), {}),
    'times_spent_in_window_idle_seq_estimate': (get_times_spent_in_window_idle_seq_estimate, (), {}),
    'watch_yourself_or_pc_off': (get_watch_yourself_or_pc_off, (), {}),
    'idle_sequences_seq_5': (
        (get_idle_sequences, (), {}),
        (get_seq_of_seq, (), {'length': 5, })
    ),
    'times_spent_in_window_change_detect_estimate_seq_5': (
        (get_times_spent_in_window_change_detect_estimate, (), {}),
        (get_seq_of_seq, (), {'length': 5, })
    ),
    'times_spent_in_window_idle_seq_estimate_seq_5': (
        (get_times_spent_in_window_idle_seq_estimate, (), {}),
        (get_seq_of_seq, (), {'length': 5, })
    ),
    'window_titles_seq_5': (
        (get_window_titles, (), {}),
        (get_seq_of_seq, (), {'length': 5, })
    ),
    'window_titles_seq_6_include_last': (
        (get_window_titles, (), {}),
        (get_seq_of_seq, (), {'length': 6, 'include_last': True})
    ),
}

parser = argparse.ArgumentParser()
parser.add_argument("--train-split", default=DEFAULT_TRAIN_SPLIT,
                    type=float,
                    help="directory to save checkpoints and outputs")
parser.add_argument("--search-path", default='./',
                    help="where to search for log files")
# parser.add_argument("--tokenize-special", action="store_true",
#                     help="whether to tokenize special chars as words")
parser.add_argument("--features", nargs='+',
                    default=["window_titles"],
                    choices=list(FEATURES_ALL.keys()),
                    help="features to create from log files: can input multiple, space delimited")


def fix_datetime_format(datetime_str):
    if ':' in datetime_str:
        return datetime_str.replace(':', '_').replace('-', '_').replace(' ', '__')
    return datetime_str


def join_idle_times(activity_times):
    if activity_times == ['']: return activity_times
    try:
        activity_times_np = np.array([float(at) for at in activity_times])
        # idle time is logged if idle time > 2 times last idle time, e.g. at 1, 2.01, 4.03 etc seconds
        # sleep time is 1, so 0.1, 0.3 is not continuation
        # idle time logged is continuation if the number increase at least twice and more than by a second
        next_idle_time_is_continuation_of_this_idle_time = (
            # TODO - try to find out what is more realistic estimate for logging time
            np.diff(activity_times_np) > 1.001
            # let's say .001 is time of logging, although it is not true
        ) * (
            np.diff(activity_times_np) > activity_times_np[:-1]
        )

        activity_times_np[:-1][next_idle_time_is_continuation_of_this_idle_time] = np.nan
        activity_times_np = activity_times_np[np.logical_not(np.isnan(activity_times_np))]
        activity_times = ["%.3f" % at for at in activity_times_np]
    except Exception as e:
        print(e)

    return activity_times


def get_activity_times_summary(activity_times):
    # TODO
    return activity_times


def preprocess_text(fpath, fpath_out):
    text = open(fpath, encoding='utf-8').read()
    text_clean = clean_chars(text)
    lines = text_clean.splitlines()
    preprocessed_lines = preprocess_full(lines)
    text_preprocessed = '\n'.join(preprocessed_lines)
    open(fpath_out, 'w', encoding='utf-8').write(text_preprocessed)
    return preprocessed_lines


# TODO - check lines starting with idle times (on Windows) and join IF THEY ARE THE SAME WINDOW
def preprocess_full(lines, out_fname='log_preprocessed.txt'):
    new_lines = [""] * len(lines)
    new_lines_num = 0
    changed_lines_num = 0
    max_line_len = -1
    longest_line_idx = -1
    prev_line = None
    for line in lines:
        if line == '':
            continue
        if not (
                (len(line) >= (len(ENTRY_DATETIME_FORMAT) + len(' : ')))
                and line.startswith('2')
                and line[1] in '123456789'
        ):
            print('')
            print('PREVIOUS LINE:')
            print(prev_line)
            print('LINE:')
            print(line)
            print(f'WARNING: unexpected line start (should start with a date in {ENTRY_DATETIME_FORMAT} format)')
            print('WARNING: appending to last window title!')
            line = prev_line + ' <br> ' + line
            new_lines_num -= 1
            if line_changed:
                changed_lines_num -= 1
        try:
            datetime_str, _ = line.split(' : ', 1)
            if '\t' in _:
                program_and_window_title, activity_times_str = _.split('\t', 1)
            else:
                program_and_window_title, activity_times_str = _, ''
            datetime_str = fix_datetime_format(datetime_str)
            activity_times = activity_times_str.split('\t')
            activity_times = join_idle_times(activity_times)
            activity_times_summary = get_activity_times_summary(activity_times)
            activity_times_summary_str = '\t'.join(activity_times_summary)
            if activity_times_summary_str:
                activity_times_summary_str = '\t' + activity_times_summary_str
            new_line = f'{datetime_str} : {program_and_window_title}{activity_times_summary_str}'
            line_changed = new_line != line
            changed_lines_num += line_changed
            # print(f'{repr(line)}\n\tchanged to\n{repr(new_line)}')
            if len(new_line) > max_line_len:
                max_line_len = len(new_line)
                longest_line_idx = new_lines_num
            new_lines[new_lines_num] = new_line
            new_lines_num += 1
            if new_lines_num % 100 == 0:
                print(f'\rnew lines {new_lines_num}, changed lines {changed_lines_num}', end='...     ')
        except Exception as e:
            print(line, e)
            exit(1)
        prev_line = line
    print(f'longest line is\t"{new_lines[longest_line_idx][:128]}......." with length {max_line_len}')
    new_lines = new_lines[:new_lines_num]
    print(f'maximum line length {max([len(l) for l in new_lines])}')
    open(out_fname, 'w', encoding='utf-8').write('\n'.join(new_lines) + '\n')
    return new_lines


def get_folder(fpath):
    return fpath.replace('\\', '/').rsplit('/', 1)[0]


def get_fpath_with_postfix(fpath, postfix):
    # check if fpath ends with .<3-letter-ext>
    if len(fpath) > 4 and fpath[-4] == '.' and fpath.find('.', -3) == -1:
        tokens = fpath.rsplit('.', 1)
        return tokens[0] + postfix + '.' + tokens[1]
    return fpath + postfix


# ATTENTION! USE IN MODEL EVALUATION TOO!
# Can we use Byte-Pair-Encoding here?
NON_STANDART_CHARS_VIEW = {
    ' ': ' ',
    '\u2028': ' ',
    '\u200b': ' ',  # TODO - check if we don't glue some two words with this replacement
}


def clean_chars(text):
    return replace_with_dict(text, NON_STANDART_CHARS_VIEW)


def read_lines(fpath):
    return open(fpath, encoding='utf-8').read().splitlines()


def get_range_rel2len(array, range):
    return array[int(range[0] * len(array)):int(range[1] * len(array))]


SET_SPLITS = [
    ('train', [0, 0.9],),
    ('valid', [0.9, 0.99],),
    ('test', [0.99, 1.],),
]

def get_set_splits(train_split):
    valid_split = (1. - train_split) * train_split
    return [
        ('train', [0, train_split]),
        ('valid', [train_split, train_split + valid_split]),
        ('test', [train_split + valid_split, 1.]),
    ]


def dump_features(features_to_get, search_path, set_splits=SET_SPLITS):
    FEATURES = {k: FEATURES_ALL[k] for k in features_to_get}
    all_lines_partitioned = dict.fromkeys(FEATURES.keys())
    for feature_name in FEATURES:
        all_lines_partitioned[feature_name] = {}
        for dataset_part_name, _ in set_splits:
            all_lines_partitioned[feature_name][dataset_part_name] = []
    all_log_files_fpaths = [str(_) for _ in list(Path(search_path).rglob('log_all.txt'))]
    for fpath in all_log_files_fpaths:
        print(f'processing {fpath} ...')
        fpath_preprocessed = get_fpath_with_postfix(fpath, '_processed')
        preprocessed_lines = preprocess_text(fpath, fpath_preprocessed)
        for feature_name, feature_fun_chain in FEATURES.items():
            output_data = preprocessed_lines
            if not isinstance(feature_fun_chain[0], tuple):
                feature_fun_chain = (feature_fun_chain,)
            for chain_idx, feature_data in enumerate(feature_fun_chain):
                feature_fun, feature_args, feature_kwargs = feature_data
                last_in_chain = chain_idx == len(feature_fun_chain) - 1
                if last_in_chain:
                    feature_kwargs['fpath'] = get_fpath_with_postfix(fpath_preprocessed, '_' + feature_name)
                output_data = feature_fun(output_data, **feature_kwargs)
            feature_lines = output_data
            for dataset_part_name, part_range in set_splits:
                all_lines_partitioned[feature_name][dataset_part_name].extend(
                    get_range_rel2len(feature_lines, part_range)
                )
    for feature_name, feature_fun_chain in FEATURES.items():
        if not isinstance(feature_fun_chain[0], tuple):
            feature_fun_chain = (feature_fun_chain,)

        if isinstance(all_lines_partitioned[feature_name]['train'][0], (list, tuple)):
            sample_dump_fun = join_seq_to_dump_str
            delim = get_delim(feature_fun_chain[-1][-1]['length'])
        elif isinstance(all_lines_partitioned[feature_name]['train'][0], (int, float)):
            sample_dump_fun = str
            delim = '\n'
        else:
            sample_dump_fun = lambda x: x
            delim = '\n'
        for dataset_part_name, _ in set_splits:
            dump_fpath = f'log_all_merged_{feature_name}_{dataset_part_name}.txt'
            open(dump_fpath, 'w', encoding='utf-8').write(delim.join(
                [sample_dump_fun(sample) for
                 sample in
                 all_lines_partitioned[feature_name][dataset_part_name]]
            ))


if __name__ == '__main__':
    args = parser.parse_args()
    set_splits = get_set_splits(args.train_split)

    dump_features(args.features, args.search_path, set_splits)
