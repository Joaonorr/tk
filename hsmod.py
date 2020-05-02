#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import re
import os
from typing import Dict, List, Tuple, Union  # , Any, Callable


class HCase:
    def __init__(self, cmd, input, vpl_tests):
        self.cmd = cmd
        self.input = input
        self.output = vpl_tests

    @staticmethod
    def load_from_line(line: str):
        parts = line.split("==")
        # remove first word

        _input = parts[0].strip().split(" ")
        _cmd = _input[0]
        del _input[0]
        # remove empty words
        _input = [item for item in _input if item != ""]
        _input = "\n".join(_input)
        _output = parts[1].strip()
        return HCase(_cmd, _input, _output)

    def to_tio(self):
        return ">>>>>>>>\n" + self.input + "\n========\n" + self.output + "\n<<<<<<<<"

    def to_vpl(self):
        return "case=\ninput=" + self.input + "\noutput=\"" + self.output + "\n\"\n"

    def __eq__(self, test):
        return (self.cmd == test.cmd) and (test.input == self.input) and (test.user == self.output)


class HFile:
    @staticmethod
    def __filter_lines(lines: List[str]) -> List[str]:
        lines = [line.strip() for line in lines]
        lines = [line for line in lines if not line.startswith("--")]
        lines = [line for line in lines if not line.startswith("```")]
        lines = [line for line in lines if "==" in line]
        return lines

    @staticmethod
    def __extract_hs(text: str) -> str:
        regex = r"```hs(.*?)\n```"
        match_list = re.findall(regex, text, re.MULTILINE | re.DOTALL)
        return "\n".join(match_list)

    @staticmethod
    def load_from_text(text: str) -> List[HCase]:
        text = HFile.__extract_hs(text)
        lines = text.split("\n")
        lines = HFile.__filter_lines(lines)
        tests = []
        for line in lines:
            tests.append(HCase.load_from_line(line))
        return tests


class HMain:
    @staticmethod
    def is_int(token):
        try:
            int(token)
            return True
        except ValueError:
            return False

    @staticmethod
    def _convert_token(token: str) -> str:
        if token.startswith("["):
            return "<- readLn :: IO [Int]"
        elif HMain.is_int(token):
            return "<- readLn :: IO Int"
        else:
            return "<- getLine"

    @staticmethod
    def format_main(test: HCase) -> str:
        out = "main = do\n"
        var = "a"
        tab = "    "
        print_cmd = tab + "print $ " + test.cmd
        lines = test.input.split("\n")
        for line in lines:
            out += tab + var + " " + HMain._convert_token(line) + "\n"
            print_cmd += " " + var
            var = chr(ord(var) + 1)
        return out + print_cmd + "\n"


def read_from_file(path: str):
    with open(path, "r") as f:
        return f.read()


def add_main(readme, readme_file, main_str):
    regex = r"<!--MAIN_BEGIN-->(.*)<!--MAIN_END-->"
    found = re.search(regex, readme, re.MULTILINE | re.DOTALL)
    subst = "<!--MAIN_BEGIN-->\\n### Main\\n```hs\\n" + main_str + "\\n```\\n<!--MAIN_END-->"
    if found:
        result = re.sub(regex, subst, readme, 0, re.MULTILINE | re.DOTALL)
        if result != readme:
            print("changed, replacing Main")
            with open(readme_file, "w") as f:
                f.write(result)
    else:
        print("Not found, adding Main")
        add = "\n\n<!--MAIN_BEGIN-->\n### Main\n```hs\n" + main_str + "\n```\n<!--MAIN_END-->\n"
        with open(readme_file, "w") as f:
            f.write(readme + add)


def process_folder(folder: str, args):
    readme_path = os.path.join(folder, "Readme.md")
    readme = read_from_file(readme_path)

    tests = HFile.load_from_text(readme)
    print(folder, ", tests found: ", len(tests))
    if len(tests) == 0:
        print("  🞩 fail: none tests found")
        exit(1)
    main_str = HMain.format_main(tests[-1])

    if args.update:
        add_main(readme, readme_path, main_str)

    if args.vpl:
        vpl_path = os.path.join(folder, args.vpl)
        vpl_tests = ""
        for test in tests:
            vpl_tests += test.to_vpl() + "\n" + "\n"
        with open(vpl_path, "w") as f:
            print("  ✓ " + vpl_path)
            f.write(vpl_tests)

    if args.tio:
        tio_path = os.path.join(folder, args.tio)
        tio_tests = ""
        for test in tests:
            tio_tests += test.to_tio() + "\n" + "\n"
        with open(tio_path, "w") as f:
            print("  ✓ " + tio_path)
            f.write(tio_tests)

    if args.main:
        main_path = os.path.join(folder, args.main)
        with open(main_path, "w") as f:
            print("  ✓ " + main_path)
            f.write(main_str)


def main():
    parser = argparse.ArgumentParser(prog='hs.py', description="gerador haskell to vpl",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('folders', type=str, nargs='*', help='diretório de trabalho')
    parser.add_argument('--vpl', '-v', action='store', type=str, help="arquivo para salvar o vpl")
    parser.add_argument('--tio', '-t', action='store', type=str, help="arquivo para salvar o tio")
    parser.add_argument('--main', '-m', action='store', type=str, help="arquivo para salvar a main")
    parser.add_argument("--update", action='store_true', help="Update main inside Readme.md")
    args = parser.parse_args()

    folders = ["."]
    if len(args.folders) != 0:
        folders = args.folders

    for folder in folders:
        if os.path.isdir(folder):
            process_folder(folder, args)


if __name__ == '__main__':
    main()


