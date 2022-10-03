#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unicodedata
import enum


class Color(enum.Enum):
    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4
    MAGENTA = 5
    CYAN = 6
    WHITE = 7
    RESET = 8
    BOLD = 9
    ULINE = 10

class Colored:
    __map = {
        Color.RED     : '\u001b[31m',
        Color.GREEN   : '\u001b[32m',
        Color.YELLOW  : '\u001b[33m',
        Color.BLUE    : '\u001b[34m',
        Color.MAGENTA : '\u001b[35m',
        Color.CYAN    : '\u001b[36m',
        Color.WHITE   : '\u001b[37m',
        Color.RESET   : '\u001b[0m',
        Color.BOLD    : '\u001b[1m',
        Color.ULINE   : '\u001b[4m'
    }
    

    @staticmethod
    def __call__(text: str, color: Color) -> str:
        return Colored.__map[color] + text + Colored.__map[Color.RESET]

    @staticmethod
    def clean(text):
        for color in Colored.__map.values():
            text = text.replace(color, '')
        return text


    # RED     = '\u001b[31m'
    # GREEN   = '\u001b[32m'
    # YELLOW  = '\u001b[33m'
    # BLUE    = '\u001b[34m'
    # MAGENTA = '\u001b[35m'
    # CYAN    = '\u001b[36m'
    # RESET   = '\u001b[0m'
    # BOLD    = '\u001b[1m'
    # ULINE   = '\u001b[4m'


# def ulen(text: str) -> int:
    
#     return sum(1 for ch in text if unicodedata.combining(ch) == 0)

# def ulen_test():
#     print(ulen('ovo'))
#     print(ulen('≠✓»'))
#     print(ulen(Color.colored('≠✓»', Color.GREEN)))

# if __name__ == '__main__':
#     # ovoverde = Color.colored('ovo', Color.GREEN)
#     # print(ovoverde)
#     # print(len(ovoverde))
#     # ovolimpo = Color.clear(ovoverde)
#     # print(ovolimpo)
#     # print(len(ovolimpo))
#     # # ulen_test()

x = Colored()('ovo', Color.GREEN)
for i, c in enumerate(x):
    print(i, c)