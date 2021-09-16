import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--search-path", default='./',
                    help="where to search for log files")
parser.add_argument("--dry-run", action="store_true",
                    help="Don't modify files.")


def deduplicate(fpaths, dry_run=True):
    n_fpaths = len(fpaths)
    lines_sets = [set(open(fpath, encoding='utf-8').read().splitlines()) for fpath in fpaths]
    for idx in range(n_fpaths):
        lines_set = lines_sets[idx]
        for idx_other in range(idx + 1, n_fpaths):
            if idx == idx_other: continue

            intersection = lines_set.intersection(lines_sets[idx_other])
            if len(intersection):
                if len(intersection) == 1 and next(iter(intersection)) == '':
                    continue
                else:
                    iter_intersection = iter(intersection)
                    _ = next(iter_intersection)  # to show next line, first can be ""
                    print(f'{fpaths[idx]} and {fpaths[idx_other]} have '
                          f'{len(intersection)} common lines, like \n\t{next(iter_intersection)}\n!!!')
            else:
                continue

            fpath1, fpath2 = fpaths[idx], fpaths[idx_other]
            while True:
                choice = input(f'Choose file to clean up:\n1: {fpath1},\n2: {fpath2}\n? _ ')
                if choice in ['1', '2']:
                    break
            file_to_clean_up = (choice == '1') and fpath1 or fpath2
            file_to_leave_as_is = (choice != '1') and fpath1 or fpath2
            cleanup(file_to_clean_up, file_to_leave_as_is, dry_run=dry_run)


def cleanup(file_to_clean_up, file_to_leave_as_is, dry_run=True):
    with open(file_to_clean_up, encoding='utf-8') as f:
        lines_to_clean_up = f.read().splitlines()
    lines_to_leave_as_is = open(file_to_leave_as_is, encoding='utf-8').read().splitlines()
    num_lines_cleaned_up = 0
    lines_cleaned_up = [""] * len(lines_to_clean_up)
    for _, l in enumerate(lines_to_clean_up):
        if _ % 100 == 0: print('\r', _, end=' lines checked ...')
        if l in lines_to_leave_as_is: continue
        lines_cleaned_up[num_lines_cleaned_up] = l
        num_lines_cleaned_up += 1
        if num_lines_cleaned_up % 100 == 0:
            print(f'\r{num_lines_cleaned_up} clean lines filtered out of'
                  f' {len(lines_to_clean_up)} total', end='.')

    lines_cleaned_up = lines_cleaned_up[:num_lines_cleaned_up]
    print(f'{len(lines_cleaned_up)} of {len(lines_to_clean_up)} lines left after cleanup.')
    if dry_run:
        print('not doing anything due to dry_run=True.')
        exit()
    with open(file_to_clean_up, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines_cleaned_up))
    print(f'overwritten file {file_to_clean_up} .')


if __name__ == '__main__':
    args = parser.parse_args()
    all_log_files_fpaths = [str(_) for _ in list(Path(args.search_path).rglob('log_all.txt'))]
    deduplicate(all_log_files_fpaths, dry_run=args.dry_run)
