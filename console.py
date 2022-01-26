import re


def choose_from_keyboard(choices, initial_choices=None):
    if initial_choices is None:
        initial_choices = choices[:]

    for i, choice in enumerate(choices):
        print("%d) %s" % (i + 1, choice))
    print("""
Type number n two select nth choice
to filter shown list: type `[REGEX_PATTERN]
to filter initial list: ~[REGEX_PATTERN]
""")
    input_string = input("Type choice or filter pattern with prefix: ")
    return_multiple = input_string.endswith('...')
    if return_multiple: input_string = input_string[:-3]

    if input_string == "": return None

    if not (input_string.startswith('`') or input_string.startswith('~')):
        try:
            num = int(input_string)
            return choices[num - (1 if num > 0 else 0)]
        except:
            input_string = '`' + input_string

    choose_from_initial = input_string.startswith("~")
    pattern = input_string[1:]
    choices_to_filter = initial_choices if choose_from_initial else choices

    filtered_choices = [choice for choice in choices_to_filter if re.findall(pattern, choice) != []]
    if len(filtered_choices) == 0:
        print('No entries matching `%s` pattern found' % (pattern))
        filtered_choices = choices
    if return_multiple:
        return filtered_choices
    return choose_from_keyboard(filtered_choices, initial_choices=initial_choices)
