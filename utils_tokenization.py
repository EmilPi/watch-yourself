import argparse
import re

parser = argparse.ArgumentParser()
parser.add_argument('--tokenize', metavar='DIR',
                    help='file path to tokenize')
parser.add_argument('--untokenize', metavar='DIR',
                    help='file path to untokenize')
parser.add_argument('--test',
                    help='test on a given file')
SPECIAL_TOKENS = {
    '-': '<dsh>',
    '_': '<und>',
    '/': '<slsh>',
    '|': '<vslsh>',
    '\\': '<bslsh>',
    '.': '<dot>',
    ',': '<cm>',
    '(': '<lbr>',
    ')': '<rbr>',
    '[': '<lsbr>',
    ']': '<rsbr>',
    '@': '<mail>',
    ';': '<scl>',
    ':': '<cl>',
    '*': '<star>',
}
AFTER_TOKENS = ('  ', ' <sp> ')
UNSPECIAL_TOKENS = {v: k for k, v in SPECIAL_TOKENS.items()}


def replace_with_dict(text, tokens_dict, pad=' ', unpad=''):
    for k, v in tokens_dict.items():
        text = text.replace(unpad + k + unpad, pad + v + pad)
    return text


def tokenize(text):
    if isinstance(text, (tuple, list)):
        return [tokenize(_) for _ in text]
    text = text.replace(' ', '<sp>')
    text = replace_with_dict(text, SPECIAL_TOKENS, pad=' ', unpad='')
    text = text.replace('<sp>', ' <sp> ')
    text = re.sub(' +', ' ', text)
    # text = text.replace('>  <', '> <')
    # text = text.replace('  <', ' <')
    # text = text.replace('>  ', '> ')
    return text


def untokenize(text):
    if isinstance(text, (tuple, list)):
        return [untokenize(_) for _ in text]
    text = ''.join(text.split(' '))
    text = replace_with_dict(text, UNSPECIAL_TOKENS, pad='', unpad='')
    text = text.replace('<sp>', ' ')
    # text = text.replace('> ', '>  ')
    # text = text.replace(' <', '  <')
    # text = text.replace(' <sp> ', ' ')
    # text = text.replace(' <sp>', ' ')
    # text = text.replace('<sp> ', ' ')
    return text


if __name__ == '__main__':
    args = parser.parse_args()

    if args.tokenize:
        with open(args.tokenize, encoding='utf-8') as f:
            text = f.read()
            text = tokenize(text)
        with open(args.tokenize, 'w', encoding='utf-8') as f:
            f.write(text)
    if args.untokenize:
        with open(args.untokenize, encoding='utf-8') as f:
            text = f.read()
            text = untokenize(text)
        with open(args.untokenize, 'w', encoding='utf-8') as f:
            f.write(text)
    if args.test:
        with open(args.test, encoding='utf-8') as f:
            text = f.read()
        if len(text)<2000: print(text)
        text1 = tokenize(text)
        if len(text1) < 2000: print(text1)
        text2 = untokenize(text1)
        if len(text2) < 2000: print(text2)
        didx = 20
        for idx in range(max(len(text), len(text2))):
            ch1, ch2 = text[idx], text2[idx]
            if ch1 != ch2:
                print(f'{idx}: text  part is "...{text[max(0, idx - didx):idx + didx]}..."')
                print(f'{idx}: text2 part is "...{text2[max(0, idx - didx):idx + didx]}..."')
                raise ValueError("text not the same after tokenizing and untokenizing.")
