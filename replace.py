#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from enum import Enum
from typing import List, Dict, Tuple, Any, Optional
import os
import re
import shutil
import argparse
import subprocess
import tempfile
import io
from subprocess import PIPE


class Replacer:
    @staticmethod
    def get_borders(regex, text, options) -> List[str]:
        out = []
        last = 0
        for m in re.finditer(regex, text, options):
            out.append(text[last:m.span()[0]])
            last = m.span()[1]
        out.append(text[last:])
        return out

    @staticmethod
    def merge_tests(borders, tests):
        out = []
        for i in range(len(borders)):
            out.append(borders[i])
            if i < len(tests):
                out.append(tests[i])

def main():
    text = """asbd
    (adfsadf)[asdfsadfasdf]
    a
    b
    (x
    y)[c d]e
    f
    g(a c
    b)[
    z
    w
    ]asdf
    asdfa
    """

    regex = r"\((.*?)\)\[(.*?)\]"

    out = Replacer.get_borders(regex, text, re.MULTILINE | re.DOTALL)
    print(out)

if __name__ == "__main__":
    main()
