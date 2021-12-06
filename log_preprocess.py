import argparse
import numpy as np
from pathlib import Path
from utils_tokenization import tokenize

parser = argparse.ArgumentParser()
parser.add_argument("--train-split", default=.9,
                    type=float,
                    help="directory to save checkpoints and outputs")
parser.add_argument("--search-path", default='./',
                    help="where to search for log files")
parser.add_argument("--tokenize-special", action="store_true",
                    help="whether to tokenize special chars as words")


def fix_datetime_format(datetime_str):
    if ':' in datetime_str:
        return datetime_str.replace(':', '_').replace(' ', '__')
    return datetime_str


def join_idle_times(activity_times):
    if activity_times == ['']: return activity_times
    try:
        activity_times_np = np.array([float(at) for at in activity_times])
        # idle time is logged if idle time > 2 times last idle time, e.g. at 1, 2.01, 4.03 etc seconds
        # sleep time is 1, so 0.1, 0.3 is not continuation
        # idle time logged is continuation if the number increase at least twice and more than by a second
        next_idle_time_is_continuation_of_this_idle_time = (
            np.diff(activity_times_np) > 1.001  # let's say .001 is time of logging, although it is not true
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




# TODO - check lines starting with idle times (on Windows) and join IF THEY ARE THE SAME WINDOW
def preprocess_full(lines, out_fname='log_preprocessed.txt'):
    new_lines = [""] * len(lines)
    new_lines_num = 0
    max_line_len = -1
    longest_line_idx = -1
    for line in lines:
        if line == '':
            continue
        if not line.startswith('21'):
            print(line)
            exit(1)
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
            if new_line != line:
                print(f'{repr(line)}\n\tchanged to\n{repr(new_line)}')
            if len(new_line) > max_line_len:
                max_line_len = len(new_line)
                longest_line_idx = new_lines_num
            new_lines[new_lines_num] = new_line
            new_lines_num += 1
        except Exception as e:
            print(line, e)
            exit(1)
    print(f'longest line is\t"{new_lines[longest_line_idx][:128]}......." with length {max_line_len}')
    new_lines = new_lines[:new_lines_num]
    print(f'maximum line length {max([len(l) for l in new_lines])}')
    open(out_fname, 'w', encoding='utf-8').write('\n'.join(new_lines) + '\n')
    return new_lines


def preprocess_titles_only(lines, dir='./'):
    if dir.endswith('/') or dir.endswith('\\'):
        dir = dir[:-1]
    n_lines = len(lines)
    lines_train, lines_valid = [], []
    for line_idx, line in enumerate(lines):
        if line == '':
            n_lines -= 1
            continue
        if not line.startswith('21'):
            print(line)
            exit(1)
        try:
            datetime_str, _ = line.split(' : ', 1)
            if '\t' in _:
                program_and_window_title, __ = _.split('\t', 1)
            else:
                program_and_window_title = _
        except Exception as e:
            print(line, e)
            exit(1)

        if line_idx < args.train_split * n_lines:
            lines_train.append(program_and_window_title)
        else:
            lines_valid.append(program_and_window_title)

    max_train_sample_len = max([len(l) for l in lines_train])
    max_valid_sample_len = max([len(l) for l in lines_valid])
    train_sample_longest = [l for l in lines_train if len(l) == max_train_sample_len][0]
    valid_sample_longest = [l for l in lines_valid if len(l) == max_valid_sample_len][0]
    print(f'one of the longest train titles is\n\t{train_sample_longest[:32]}......{train_sample_longest[-64:]}\nwith length {max_train_sample_len}')
    print(f'one of the longest valid titles is\n\t{valid_sample_longest[:32]}......{valid_sample_longest[-64:]}\nwith length {max_valid_sample_len}')

    dump_train_and_valid_sets(dir, lines_train, lines_valid)

    return lines_train, lines_valid


def dump_train_and_valid_sets(dir, lines_train, lines_valid):
    print(f'{dir}, n_train={len(lines_train)}, n_valid={len(lines_valid)}')
    with open(f'{dir}/train.txt', 'w', encoding='utf-8') as ft:
        ft.write('\n'.join(lines_train))
    with open(f'{dir}/valid.txt', 'w', encoding='utf-8') as fv:
        fv.write('\n'.join(lines_valid))


def get_folder(fpath):
    return fpath.replace('\\', '/').rsplit('/', 1)[0]


def get_fpath_with_postfix(fpath, postfix):
    # check if fpath ends with .<3-letter-ext>
    if len(fpath) > 4 and fpath[-4] == '.' and fpath.find('.', -3) == -1:
        tokens = fpath.rsplit('.', 1)
        return tokens[0] + postfix + '.' + tokens[1]
    return fpath + postfix


# ATTENTION! USE WITH IN EVALUATION TOO!
# Can we use Byte-Pair-Encoding here?
def clean_chars(text):
    return text.replace(' ', ' ')


def split(all_log_files_fpaths, _tokenize=False):
    n_entries = 0
    for fpath in all_log_files_fpaths:
        print(f'processing {fpath} ...')
        text = open(fpath, encoding='utf-8').read()
        text_clean = clean_chars(text)
        lines = text_clean.splitlines()
        preprocessed_lines = preprocess_full(lines, get_fpath_with_postfix(fpath, '_processed'))
        n_entries += len(lines)
        lines_train, lines_valid = preprocess_titles_only(preprocessed_lines, dir=get_folder(fpath))
        if _tokenize:
            lines_train = tokenize(lines_train)
            lines_valid = tokenize(lines_valid)
        all_files_lines_train.extend(lines_train)
        all_files_lines_valid.extend(lines_valid)
    dump_train_and_valid_sets('./', all_files_lines_train, all_files_lines_valid)
    print(n_entries, 'entries total.')


if __name__ == '__main__':
    args = parser.parse_args()
    all_files_lines = []
    all_files_lines_train = []
    all_files_lines_valid = []

    all_log_files_fpaths = [str(_) for _ in list(Path(args.search_path).rglob('log_all.txt'))]
    split(all_log_files_fpaths, _tokenize=args.tokenize_special)
