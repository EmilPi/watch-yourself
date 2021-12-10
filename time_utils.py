import time

from vars import ENTRY_DATETIME_FORMAT

moon_phase_in_earth_days = 29.53058770576
moon_phase_in_earth_seconds = moon_phase_in_earth_days * (24 * 60 * 60)
reference_date_time_string = '00_01_06__12_15_00'

t = time.time()
dateTimeOffsetSeconds = int(t - time.mktime(time.gmtime(t)))


def time_str2seconds_since_epoch(local_time_1_str, fmt=ENTRY_DATETIME_FORMAT):
    time_struct = time.strptime(local_time_1_str, fmt)
    seconds_since_epoch_plus_local = time.mktime(tuple(time_struct))
    return seconds_since_epoch_plus_local - dateTimeOffsetSeconds


reference_date_time_seconds_since_epoch = time_str2seconds_since_epoch(reference_date_time_string)


def get_moon_phase_part(date_time_str):
    seconds_since_epoch = time_str2seconds_since_epoch(date_time_str)
    seconds_relative_to_reference_date_time = seconds_since_epoch - reference_date_time_seconds_since_epoch
    current_moon_phase_seconds = seconds_relative_to_reference_date_time % moon_phase_in_earth_seconds
    if current_moon_phase_seconds < 0:
        current_moon_phase_seconds += moon_phase_in_earth_seconds
    return current_moon_phase_seconds / moon_phase_in_earth_seconds
