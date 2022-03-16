import difflib
import time

import jellyfish

from time_utils import get_moon_phase_part, time_str2seconds_since_epoch
from utils_text import is_browser_window_title_bad
from utils_tokenization import tokenize
from vars import ENTRY_DATETIME_FORMAT


def line_is_ok(line):
    if line == '':
        print('Warning: empty line.')
        return False
    return True


def get_titles_with_binary(lines):
    titles_with_binary = []
    for line_idx, line in enumerate(lines):
        try:
            if not line_is_ok(line):
                program_and_window_title = ''
            else:
                datetime_str, _ = line.split(' : ', 1)
                if '\t' in _:
                    program_and_window_title, __ = _.split('\t', 1)
                else:
                    program_and_window_title = _
        except Exception as e:
            raise e
        finally:
            print(line)
            exit(1)

        titles_with_binary.append(program_and_window_title)

    max_sample_len = max([len(l) for l in lines])
    sample_longest = [l for l in lines if len(l) == max_sample_len][0]
    print(
        f'one of the longest titles is\n\t{sample_longest[:32]}......{sample_longest[-64:]}\nwith length {max_sample_len}')

    return titles_with_binary


def get_basic_line_features(line, named=False):
    try:
        datatime_str, binary_title_idle_seq = line.split(' : ', 1)
        if ' __ ' in binary_title_idle_seq:
            binary_name, title_idle_seq = binary_title_idle_seq.split(' __ ', 1)
        else:
            binary_name, title_idle_seq = '', binary_title_idle_seq
        if '\t' in title_idle_seq:
            window_title, idle_seq = title_idle_seq.split('\t', 1)
        else:
            window_title, idle_seq = title_idle_seq, ''
    except Exception as e:
        print(line)
        print(repr(line))
        raise e
    if named:
        return {
            'datatime_str': datatime_str, 'binary_name': binary_name, 'window_title': window_title,
            'idle_seq': idle_seq,
        }
    return datatime_str, binary_name, window_title, idle_seq


def get_basic_features(lines, named=False):
    n_lines = len(lines)
    zeros = [0.] * n_lines
    datatime_strs = zeros[:]
    binary_names = zeros[:]
    window_titles = zeros[:]
    idle_sequences = zeros[:]
    for line_idx, line in enumerate(lines):
        basic_line_features = get_basic_line_features(line, named=True)
        datatime_strs[line_idx] = basic_line_features['datatime_str']
        binary_names[line_idx] = basic_line_features['binary_name']
        window_titles[line_idx] = basic_line_features['window_title']
        idle_sequences[line_idx] = basic_line_features['idle_seq']
    if named:
        return {
            'datatime_strs': datatime_strs, 'binary_names': binary_names, 'window_titles': window_titles,
            'idle_sequences': idle_sequences,
        }
    return datatime_strs, binary_names, window_titles, idle_sequences


def get_window_title(line):
    datatime_str, binary_title_idle_seq = line.split(' : ', 1)
    binary, title_idle_seq = binary_title_idle_seq.split(' __ ')[-1]
    window_title, idle_seq = title_idle_seq.split('\t', 1)
    return window_title


def get_idle_seq_num(idle_seq: str) -> [float]:
    if idle_seq == '': return []
    if idle_seq == ['']: return []
    return [float(_) for _ in idle_seq.split('\t')]


def get_time_features(lines, named=False):
    n_lines = len(lines)
    zeros = [0.] * n_lines

    times_spent_in_window_change_detect_estimate = zeros[:]
    times_spent_in_window_idle_seq_estimate = zeros[:]
    idle_sequences = zeros[:]
    detected_actions_num_estimate = zeros[:]
    times_of_day = zeros[:]
    week_days = zeros[:]
    moon_phases = zeros[:]
    watch_yourself_or_pc_off = zeros[:]

    seconds_since_epoch_last = None
    for line_idx, line in enumerate(lines):
        basic_line_features = get_basic_line_features(line)
        datetime_str = basic_line_features[0]
        time_struct = time.strptime(datetime_str, ENTRY_DATETIME_FORMAT)
        times_of_day[line_idx] = (time_struct.tm_hour * 3600 + time_struct.tm_min * 60 + time_struct.tm_sec) / 86400
        week_days[line_idx] = time_struct.tm_wday
        moon_phases[line_idx] = get_moon_phase_part(datetime_str)
        seconds_since_epoch = time_str2seconds_since_epoch(datetime_str)
        idle_seq = basic_line_features[-1]
        try:
            idle_seq_num = get_idle_seq_num(idle_seq)
        except ValueError as e:
            print(repr(line))
            print(line)
            print(get_basic_line_features(line, named=True))
            print(repr(idle_seq))
            raise e
        idle_sequences[line_idx] = idle_seq_num
        detected_actions_num_estimate[line_idx] = len(idle_seq_num)
        idle_seq_sum = sum(idle_seq_num)
        # TODO - try to evaluate this better by plotting elapsed time from window on time VS idle_seq_sum
        # When idle time is less than previous one
        # (which will be less than 1 second too when no screenshot/webcam photo is done, as it is check interval),
        # the logged time (idle time) is less than elapsed time
        # so we don't know, how much passed. Let's assume that on average .5 is lost
        times_spent_in_window_idle_seq_estimate[line_idx] = idle_seq_sum + .5 * (len(idle_seq_num) + 1)
        if line_idx > 0:
            times_spent_in_window_change_detect_estimate[line_idx - 1] = seconds_since_epoch - seconds_since_epoch_last
            # and let's add 90% to that evaluation of idle time seq
            if (times_spent_in_window_change_detect_estimate[line_idx - 1] > 30) \
                    and (times_spent_in_window_change_detect_estimate[line_idx - 1] >
                         times_spent_in_window_idle_seq_estimate[line_idx - 1] * 1.9):
                # then we think that watch-yourself was off (either manually turned off, or PC turned off)
                watch_yourself_or_pc_off[line_idx - 1] = True
            else:
                watch_yourself_or_pc_off[line_idx - 1] = False
        if line_idx == n_lines - 1:
            times_spent_in_window_change_detect_estimate[line_idx] = -1.
            watch_yourself_or_pc_off[line_idx] = True
        seconds_since_epoch_last = seconds_since_epoch

    if named:
        return {
            'times_spent_in_window_change_detect_estimate': times_spent_in_window_change_detect_estimate,
            'times_spent_in_window_idle_seq_estimate': times_spent_in_window_idle_seq_estimate,
            'watch_yourself_or_pc_off': watch_yourself_or_pc_off,
            'idle_sequences': idle_sequences, 'times_of_day': times_of_day,
            'week_days': week_days, 'moon_phases': moon_phases,
            'actions_num_estimate': detected_actions_num_estimate,
        }
    return times_spent_in_window_change_detect_estimate, times_spent_in_window_idle_seq_estimate, watch_yourself_or_pc_off, idle_sequences, times_of_day, week_days, moon_phases, detected_actions_num_estimate


def get_window_titles(lines, fpath=None):
    basic_features = get_basic_features(lines, named=True)
    window_titles = basic_features['window_titles']
    if fpath:
        open(fpath, 'w', encoding='utf-8').write('\n'.join(window_titles))
    return window_titles


def get_times_spent_in_window_change_detect_estimate(lines, fpath=None):
    time_features = get_time_features(lines, True)
    times_spent_in_window_change_detect_estimate = time_features['times_spent_in_window_change_detect_estimate']
    if fpath:
        try:
            open(fpath, 'w', encoding='utf-8').write(
                '\n'.join([str(round(t, 3)) for t in times_spent_in_window_change_detect_estimate]))
        except TypeError as e:
            print(times_spent_in_window_change_detect_estimate)
            raise e
    return times_spent_in_window_change_detect_estimate


def get_times_spent_in_window_idle_seq_estimate(lines, fpath=None):
    time_features = get_time_features(lines, True)
    times_spent_in_window_idle_seq_estimate = time_features['times_spent_in_window_idle_seq_estimate']
    if fpath:
        try:
            open(fpath, 'w', encoding='utf-8').write(
                '\n'.join([str(round(t, 3)) for t in times_spent_in_window_idle_seq_estimate]))
        except TypeError as e:
            print(times_spent_in_window_idle_seq_estimate)
            raise e
    return times_spent_in_window_idle_seq_estimate


def get_watch_yourself_or_pc_off(lines, fpath=None):
    time_features = get_time_features(lines, True)
    watch_yourself_or_pc_off = time_features['watch_yourself_or_pc_off']
    if fpath:
        try:
            open(fpath, 'w', encoding='utf-8').write('\n'.join([str(round(t, 3)) for t in watch_yourself_or_pc_off]))
        except TypeError as e:
            print(watch_yourself_or_pc_off)
            raise e
    return watch_yourself_or_pc_off


def get_actions_num_estimate(lines, fpath):
    time_features = get_time_features(lines, True)
    ret = time_features['actions_num_estimate']
    if fpath:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(str(_) for _ in ret))
    return ret


def get_binary_names(lines, fpath=None):
    basic_features = get_basic_features(lines, named=True)
    binary_names = basic_features['binary_names']
    if fpath:
        open(fpath, 'w', encoding='utf-8').write('\n'.join(binary_names))
    return binary_names


def get_idle_sequences(lines, fpath=None):
    basic_features = get_basic_features(lines, named=True)
    idle_sequences = basic_features['idle_sequences']
    if fpath:
        open(fpath, 'w', encoding='utf-8').write('\n'.join(idle_sequences))
    return idle_sequences


def get_delim(length):
    return f'\n~~~~SEQ OF LEN {length} DELIM~~~~\n'


def join_seq_to_dump_str(seq):
    if isinstance(seq[0], str):
        return '\n'.join(seq)
    if isinstance(seq[0], (int, float, bool)):
        return '\t'.join([str(v) for v in seq])
    if isinstance(seq[0], (list, tuple)):
        return join_seq_to_dump_str([
            join_seq_to_dump_str(_seq) for _seq in seq
        ])
    raise TypeError(f"Cannot join seq of type", type(seq))


def get_seq_of_seq(lines, fpath=None, **kwargs):
    # #length of titles before current title
    length = kwargs.get('length', 1)
    last_included = int(kwargs.get('last_included', False))
    empty_val = {
        int: -1,
        float: -1.,
        bool: None,
        str: ''
    }[type(lines[0])]
    empty_seq = [empty_val] * length
    n_lines = len(lines)
    seq_of_seq = [None] * n_lines
    for line_idx, line in enumerate(lines):
        if line_idx == 0:
            seq_of_seq[0] = empty_seq[:]
            if last_included:
                seq_of_seq[0][-1] = line
        elif line_idx < length:
            seq_of_seq[line_idx] = empty_seq[:]
            seq_of_seq[line_idx][-line_idx:] = lines[
                                               last_included:
                                               (line_idx + last_included)
                                               ]
        else:
            seq_of_seq[line_idx] = lines[
                                   (line_idx - length + last_included):
                                   (line_idx + last_included)
                                   ]

    if fpath:
        delim = get_delim(length)
        open(fpath, 'w', encoding='utf-8').write(delim.join(
            [join_seq_to_dump_str(seq) for seq in seq_of_seq]
        ))
    return seq_of_seq


def get_tokenized_text(lines, fpath=None, **kwargs):
    tokenized_lines = tokenize(lines)
    if fpath:
        open(fpath, 'w', encoding='utf-8').write('\n'.join(
            [line for line in tokenized_lines]
        ))
    return tokenized_lines


def _sequence_matcher_ratio(sequence1, sequence2):
    return difflib.SequenceMatcher(None, sequence1, sequence2)


def get_metric_change(lines, function=None, **kwargs):
    unknown_value = kwargs.get('unknown_value', -1.)  # TODO should be out of range of metric output
    n_windows_before_to_compare = kwargs.get('compare_offset', 1)
    ret = [unknown_value] * len(lines)
    for i in range(len(lines) - n_windows_before_to_compare):
        line = lines[i + n_windows_before_to_compare]
        line_before = lines[i]
        ret[i + n_windows_before_to_compare] = function(line, line_before)
    return ret


def get_metric_change_sequence_matcher(lines, fpath=None, **kwargs):
    ret = get_metric_change(lines, function=_sequence_matcher_ratio, **kwargs)
    if fpath:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(str(_) for _ in ret))
    return ret


def get_metric_change_hamming_distance(lines, fpath=None, **kwargs):
    ret = get_metric_change(lines, function=jellyfish.hamming_distance, **kwargs)
    if fpath:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(str(_) for _ in ret))
    return ret


def get_window_goodness(lines, fpath=None, **kwargs):
    ret = [int(is_browser_window_title_bad(line)) for line in lines]
    if fpath:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(str(_) for _ in ret))
    return ret


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
    'actions_num_estimate': (get_actions_num_estimate, (), {}),
    'window_titles_seq_5': (
        (get_window_titles, (), {}),
        (get_seq_of_seq, (), {'length': 5, })
    ),
    'window_titles_seq_6_include_last': (
        (get_window_titles, (), {}),
        (get_seq_of_seq, (), {'length': 6, 'include_last': True})
    ),
    'window_titles_goodness': (get_window_goodness, (), {}),
    'metric_change_sequence_match': (
        (get_window_titles, (), {}),
        (get_metric_change_sequence_matcher, (), {})
    ),
    'metric_change_hamming_distance': (
        (get_window_titles, (), {}),
        (get_metric_change_hamming_distance, (), {})
    ),
}
