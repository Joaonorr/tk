#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import platform
import sys
try:
    from termcolor import colored
    color_enabled = True
except ModuleNotFoundError:
    color_enabled = False
from enum import Enum
from typing import List, Tuple, Any, Optional
import os
import re
import shutil
import argparse
import subprocess
import tempfile
import io
from subprocess import PIPE


class Unit:
    def __init__(self, case: str = "", inp: str = "", outp: str = "", grade: Optional[int] = None, source: str = ""):
        self.source = source  # stores the source file of the unit
        self.case = case  # name
        self.input = inp  # input
        self.output = outp  # expected output
        self.grade = grade  # None represents proportional gr, 100 represents all
        self.index = 0
        self.duplicated: Optional[int] = None

    def to_vpl(self):
        text = "case=" + self.case + "\n"
        text += "input=" + self.input
        text += "output=\"" + self.output + "\"\n"
        if self.grade is None:
            text += "grade reduction=\n"
        else:
            text += "grade reduction=" + str(self.grade).zfill(3) + "%\n"

        return text

    def to_tio(self):
        text = ">>>>>>>>"
        if self.case != '':
            text += " " + self.case
        if self.grade is None:
            text += " !%"
        elif self.grade != 100:
            text += " " + str(self.grade) + "%"
        text += '\n' + self.input
        text += "========\n"
        text += self.output
        text += "<<<<<<<<\n"
        return text


class Symbol:
    opening = "=>"
    neutral = "(»)"  # u"\u2610"  # ☐
    mark_size = len(neutral)
    success = "(✓)"
    failure = "(✗)"
    wrong = "(ω)"
    compilation = "(ϲ)"
    execution = "(ϵ)"
    hbar = "─"
    vbar = "│"
    whitespace = u"\u2E31"  # interpunct
    newline = u"\u21B5"  # carriage return
    cfill = "_"


class Solver:
    def __init__(self, path):
        self.path: str = path
        self.filename: str = path.split(os.sep)[-1]
        self.user: List[Optional[str]] = []
        self.result: Execution.Result = Execution.Result.UNTESTED
        self.error_msg: str = ""

    def get_mark(self):
        return self._get_mark()

    def _get_mark(self):
        if self.result == Execution.Result.UNTESTED:
            return Symbol.neutral
        elif self.result == Execution.Result.SUCCESS:
            return Symbol.success
        elif self.result == Execution.Result.WRONG_OUTPUT:
            return Symbol.wrong
        elif self.result == Execution.Result.COMPILATION_ERROR:
            return Symbol.compilation
        elif self.result == Execution.Result.EXECUTION_ERROR:
            return Symbol.execution
        return Symbol.failure


class HSMod:

    class Case:
        def __init__(self, cmd="", _input="", _output=""):
            self.cmd = cmd
            self.input = _input
            self.output = _output

        def init_from_line(self, line: str) -> HSMod.Case:
            parts = line.split("==")
            # remove first word
            _input = parts[0].strip().split(" ")
            _cmd = _input[0]
            del _input[0]
            # remove empty words
            _input = [item for item in _input if item != ""]
            _input = "\n".join(_input)
            _output = parts[1].strip()
            self.cmd = _cmd
            self.input = _input + "\n"
            self.output = _output + "\n"
            return self

        def __eq__(self, test):
            return (self.cmd == test.cmd) and (test.input == self.input) and (test.output == self.output)

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
        def load_from_text(text: str) -> List[HSMod.Case]:
            text = HSMod.HFile.__extract_hs(text)
            lines = text.split("\n")
            lines = HSMod.HFile.__filter_lines(lines)
            return [HSMod.Case().init_from_line(line) for line in lines]

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
            elif HSMod.HMain.is_int(token):
                return "<- readLn :: IO Int"
            else:
                return "<- getLine"

        @staticmethod
        def format_main(test: HSMod.Case) -> str:
            out = "main = do\n"
            var = "a"
            tab = "    "
            print_cmd = tab + "print $ " + test.cmd
            lines = test.input.split("\n")
            lines = [line for line in lines if line != ""]
            for line in lines:
                out += tab + var + " " + HSMod.HMain._convert_token(line) + "\n"
                print_cmd += " " + var
                var = chr(ord(var) + 1)
            return out + print_cmd + "\n"

    @staticmethod
    def make_main(content: str) -> Optional[str]:
        hcase_list = HSMod.HFile.load_from_text(content)
        if hcase_list:
            return HSMod.HMain.format_main(hcase_list[-1])
        return None

    @staticmethod
    def load_htests(content: str, source: str) -> List[Unit]:
        hcase_list = HSMod.HFile.load_from_text(content)
        return [Unit("", hc.input, hc.output, 100, source) for hc in hcase_list]


class IOBuffer:
    tab = " " * 4

    def __init__(self):
        self.buffer = io.StringIO()

    def write(self, data: str, level: int = 0) -> str:
        shift = level * IOBuffer.tab
        _data = shift + ('\n' + shift).join(data.split('\n'))
        if data.endswith('\n') and len(shift) > 0:
            _data = _data[:-len(shift)]
        self.buffer.write(_data)
        return _data

    def getvalue(self) -> str:
        return self.buffer.getvalue()


class Logger:
    _buffer = IOBuffer()
    _level = 0
    _print_enabled = True

    _store_buffer = IOBuffer()
    _store = False

    @staticmethod
    def store():
        Logger._store = True
        Logger._store_buffer = IOBuffer()

    @staticmethod
    def recover():
        Logger._store = False
        return Logger._store_buffer.getvalue()

    @staticmethod
    def print_enable():
        Logger._print_enabled = True

    @staticmethod
    def print_disable():
        Logger._print_enabled = False

    @staticmethod
    def inc_level():
        Logger._level += 1

    @staticmethod
    def dec_level():
        if Logger._level > 0:
            Logger._level -= 1

    @staticmethod
    def _colorize(data: str):
        return data.replace(Symbol.failure, colored(Symbol.failure, 'red')).\
                    replace(Symbol.opening, colored(Symbol.opening, 'blue')). \
                    replace(Symbol.success, colored(Symbol.success, 'green')). \
                    replace(Symbol.wrong, colored(Symbol.wrong, 'yellow')). \
                    replace(Symbol.execution, colored(Symbol.execution, 'yellow')). \
                    replace(Symbol.compilation, colored(Symbol.compilation, 'yellow')). \
                    replace(Symbol.neutral, colored(Symbol.neutral, 'blue'))

    @staticmethod
    def write(data: str, level: Optional[int] = None, relative: Optional[int] = None):
        if level:
            Logger._level += level
        if relative:
            Logger._level += relative
        if Logger._store:
            data_formatted = Logger._store_buffer.write(data, Logger._level)
        else:
            data_formatted = Logger._buffer.write(data, Logger._level)
        if Logger._print_enabled and not Logger._store:
            if color_enabled:
                data_output = Logger._colorize(data_formatted)
            else:
                data_output = data_formatted
            print(data_output, end='', flush=True)
        if relative:
            Logger._level -= relative

    @staticmethod
    def clear():
        Logger._buffer = IOBuffer()

    @staticmethod
    def getvalue():
        return Logger._buffer.getvalue()


class Loader:
    regex_tio = r"^ *>>>>>>>> *(.*?)\n(.*?)^ *======== *\n(.*?)^ *<<<<<<<< *\n?"
    regex_vpl = r"^ *[Cc]ase *= *([ \S]*) *\n *input *=(.*?)^ *output *=(.*?)^ *grade *reduction *= *(\S*) *\n?"

    @staticmethod
    def parse_cio(text, source, crude_mode=False):
        unit_list = []
        text = "\n" + text

        for test_case in text.split("\n#__case")[1:]:
            unit = Unit()
            unit.source = source
            unit.output = test_case
            unit_list.append(unit)

        for unit in unit_list:
            test = unit.output
            if "\n$end" in test:
                test = test.split("\n$end")[0] + "\n$end"

            lines = test.split("\n")
            tags = lines[0].strip().split(" ")
            if tags[-1].endswith("%"):
                unit.grade = int(tags[-1][0:-1])
                del tags[-1]
            else:
                unit.grade = None
            unit.case = " ".join(tags)
            unit.output = "\n".join(lines[1:])

        # concatenando testes contínuos
        for i in range(len(unit_list)):
            unit = unit_list[i]
            if "\n$end" not in unit.output:
                unit_list[i + 1].output = unit.output + '\n' + unit_list[i + 1].output
                unit.output = unit.output + "\n$end\n"

        for unit in unit_list:
            lines = unit.output.split('\n')
            unit.output = ""
            unit.input = ""
            # filtrando linhas vazias e comentarios
            for line in lines:
                if crude_mode:  #
                    unit.output += line + '\n'
                    if line == "" or line.startswith("$") or line.startswith("#"):
                        unit.input += line + '\n'
                else:
                    if line != "" and not line.startswith("#"):
                        unit.output += line + '\n'
                        if line.startswith("$"):
                            unit.input += line[1:] + '\n'
        for unit in unit_list:
            unit.fromCio = True

        return unit_list

    @staticmethod
    def parse_tio(text: str, source: str = "") -> List[Unit]:
        def parse_case_grade(value: str) -> Tuple[str, Optional[int]]:
            _grade: Optional[int] = 100
            if value.endswith("%"):
                _case = " ".join(value.split(" ")[:-1])
                gr = value.split(" ")[-1][:-1]
                if gr == '!' or gr == '':
                    _grade = None
                else:
                    try:
                        _grade = int(gr)
                    except ValueError:
                        pass
                return _case, _grade
            return value, 100

        matches = re.findall(Loader.regex_tio, text, re.MULTILINE | re.DOTALL)
        unit_list = []
        for m in matches:
            case, grade = parse_case_grade(m[0])
            unit_list.append(Unit(case, m[1], m[2], grade, source))
        return unit_list

    @staticmethod
    def parse_vpl(text: str, source: str = "") -> List[Unit]:
        matches = re.findall(Loader.regex_vpl, text, re.MULTILINE | re.DOTALL)

        def filter_quotes(x):
            return x[1:-2] if x.startswith('"') else x

        def filter_grade(x):
            return None if x == "" else int(x[:-1])

        return [Unit(m[0], m[1], filter_quotes(m[2]), filter_grade(m[3]), source) for m in matches]

    @staticmethod
    def parse_dir(folder) -> List[Unit]:
        input_pattern = "@.in"
        output_pattern = "@.sol"

        if " " in folder:
            parts = folder.split(" ")
            if len(parts) != 3:
                raise ValueError('Folder Pattern Wrong. Use something like "dir @.in @.sol"')
            folder = parts[0]
            input_pattern = parts[1]
            output_pattern = parts[2]

        pattern_loader = PatternLoader(input_pattern, output_pattern)
        files = os.listdir(folder)
        matches = pattern_loader.get_file_sources(files)

        unit_list: List[Unit] = []
        try:
            for m in matches:
                unit = Unit()
                unit.source = os.path.join(folder, m.label)
                unit.grade = 100
                with open(os.path.join(folder, m.input_file)) as f:
                    value = f.read()
                    unit.input = value + ("" if value.endswith("\n") else "\n")
                with open(os.path.join(folder, m.output_file)) as f:
                    value = f.read()
                    unit.output = value + ("" if value.endswith("\n") else "\n")
                unit_list.append(unit)
        except FileNotFoundError as e:
            Logger.write(str(e))
        return unit_list

    @staticmethod
    def parse_source(source: str) -> List[Unit]:
        if " " in source and os.path.isdir(source.split(" ")[0]):
            return Loader.parse_dir(source)
        if os.path.isfile(source):
            with open(source) as f:
                content = f.read()
            if source.endswith(".vpl"):
                return Loader.parse_vpl(content, source)
            elif source.endswith(".tio"):
                return Loader.parse_tio(content, source)
            elif source.endswith(".md"):
                tests = Loader.parse_tio(content, source)
                tests += Loader.parse_cio(content, source)
                tests += HSMod.load_htests(content, source)
                return tests
            else:
                Logger.write("warning: target format do not supported: " + source + '\n')  # make this a raise
        else:
            raise FileNotFoundError('warning: unable to find: ' + source)
        return []


class Wdir:
    def __init__(self, folder: str):
        self.folder = folder
        self.solver_list: Optional[List[Solver]] = None
        self.source_list: List[str] = []
        self.pack_list: List[List[Unit]] = []
        self.unit_list: List[Unit] = []

    def sources(self, sources: List[str]) -> Wdir:
        self.source_list = sources
        return self

    def solvers(self, solvers: List[str]) -> Wdir:
        self.solver_list = [Solver(solver) for solver in solvers]
        return self

    def load_sources(self) -> Wdir:
        file_list: List[str] = os.listdir(self.folder)
        s_list = []
        for file in file_list:
            if file.startswith("."):
                continue
            elif file == "Readme.md":
                s_list.append(file)
            elif file.endswith(".tio"):
                s_list.append(file)
            elif file.endswith(".vpl"):
                s_list.append(file)
        self.source_list = [os.path.join(self.folder, file) for file in s_list]
        return self

    def load_solvers(self) -> Wdir:
        file_list: List[str] = os.listdir(self.folder)
        s_list = []
        for file in file_list:
            if file.lower().startswith("solver"):
                s_list.append(file)
        s_list = sorted(s_list)
        self.solver_list = [Solver(os.path.join(self.folder, file)) for file in s_list]
        return self

    def parse_sources(self) -> Wdir:
        loading_failures = 0
        for source in self.source_list:
            try:
                self.pack_list.append(Loader.parse_source(source))
            except FileNotFoundError as e:
                Logger.write(str(e) + "\n")
                loading_failures += 1
                pass
        if loading_failures > 0 and loading_failures == len(self.source_list):
            raise FileNotFoundError("failure: none source found")
        self.unit_list = sum(self.pack_list, [])
        self.__number_and_mark()
        return self

    def filter(self, index: Optional[int]) -> Wdir:
        if index:
            if 0 <= index < len(self.unit_list):
                self.unit_list = [self.unit_list[index]]
            else:
                raise ValueError("Index Number out of bounds: " + str(index))
        return self

    def __number_and_mark(self):
        new_list = []
        index = 0
        for unit in self.unit_list:
            unit.index = index
            index += 1
            search = [x for x in new_list if x.input == unit.input]
            if len(search) > 0:
                unit.duplicated = search[0].index
            new_list.append(unit)
        self.unit_list = new_list

    def manipulate(self, param: Param.Manip):
        # filtering marked duplicated
        self.unit_list = [unit for unit in self.unit_list if unit.duplicated is None]
        if param.to_sort:
            self.unit_list.sort(key=lambda v: len(v.input))
        if param.unlabel:
            for unit in self.unit_list:
                unit.case = ""
        if param.to_number:
            number = 00
            for unit in self.unit_list:
                unit.case = LabelFactory().label(unit.case).index(number).generate()
                number += 1

    def replace_input(self, solver: Solver):
        Execution.execute_solver(solver, self.unit_list)
        if solver.result == Execution.Result.COMPILATION_ERROR or solver.result == Execution.Result.EXECUTION_ERROR:
            msg = "  " + solver.get_mark() + " " + solver.path + " " + solver.filename + "\n" + solver.error_msg
            raise RuntimeError(msg)
        else:
            for unit, output in zip(self.unit_list, solver.user):
                unit.output = output

    def resume(self) -> List[str]:
        def resume_count() -> str:
            return str(len([x for x in self.unit_list if x.duplicated is None])).zfill(2)

        def resume_sources() -> str:
            out = []
            if len(self.pack_list) == 0:
                out.append(Symbol.failure)
            for i in range(len(self.pack_list)):
                nome: str = self.source_list[i].split(os.sep)[-1]
                out.append(nome + "(" + str(len(self.pack_list[i])).zfill(2) + ")")
            return ", ".join(out)

        def resume_solvers() -> str:
            if self.solver_list is None:
                return ""
            if len(self.solver_list) == 0:
                return Symbol.failure
            return ", ".join([solver.get_mark() + solver.filename for solver in self.solver_list])
        return [self.folder, resume_count(), resume_sources(), resume_solvers()]


class LabelFactory:
    def __init__(self):
        self._label = ""
        self._index = -1

    def index(self, value: int):
        try:
            self._index = int(value)
        except ValueError:
            raise ValueError("Index on label must be a integer")
        return self

    def label(self, value: str):
        self._label = value
        return self

    def generate(self):
        label = LabelFactory.trim_spaces(self._label)
        label = LabelFactory.remove_old_index(label)
        if self._index != -1:
            index = str(self._index).zfill(2)
            if label != "":
                return index + " " + label
            else:
                return index
        return label

    @staticmethod
    def trim_spaces(text):
        parts = text.split(" ")
        parts = [word for word in parts if word != '']
        return " ".join(parts)

    @staticmethod
    def remove_old_index(label):
        split_label = label.split(" ")
        if len(split_label) > 0:
            try:
                int(split_label[0])
                return " ".join(split_label[1:])
            except ValueError:
                return label


class Runner:
    class CompileError(Exception):
        pass

    class ExecutionError(Exception):
        pass

    @staticmethod
    def subprocess_run(cmd_list: List[str], input_data: str = "") -> Tuple[int, Any, Any]:
        p = subprocess.Popen(cmd_list, stdout=PIPE, stdin=PIPE, stderr=PIPE, universal_newlines=True)
        stdout, stderr = p.communicate(input=input_data)
        return p.returncode, stdout, stderr


class Compiler:
    @staticmethod
    def __prepare_c(solver: str) -> str:
        cmd = ["gcc", "-Wall", "-fsanitize=address", "-Wuninitialized", "-Wparentheses", "-Wreturn-type", "-Werror"]
        cmd += ["-fno-diagnostics-color", solver, "-o", solver + ".out", "-lm", "-lutil"]
        return_code, stdout, stderr = Runner.subprocess_run(cmd)
        if return_code != 0:
            raise Runner.CompileError(stdout + stderr)
        return solver + ".out"

    @staticmethod
    def __prepare_cpp(solver: str) -> str:
        cmd = ["g++", "-std=c++17", "-Werror", "-Wall", "-g", "-fsanitize=address", "-fsanitize=undefined"]
        cmd += ["-D_GLIBCXX_DEBUG"]
        cmd += [solver, "-o", solver + ".out"]
        return_code, stdout, stderr = Runner.subprocess_run(cmd)
        if return_code != 0:
            raise Runner.CompileError(stdout + stderr)
        return solver + ".out"

    @staticmethod
    def __prepare_hs(solver, keep_temp) -> str:
        solver_main = Compiler.__prepare_hs_append_main(solver)
        cmd = ["ghc", solver_main, "-o", solver + ".out"]
        return_code, stdout, stderr = Runner.subprocess_run(cmd)
        if return_code != 0:
            raise Runner.CompileError(stdout + stderr)
        if not keep_temp:
            os.remove(solver_main[:-3] + ".hi")
            os.remove(solver_main[:-3] + ".o")
            os.remove(solver_main)
        return solver + ".out"

    @staticmethod
    def __prepare_hs_append_main(solver) -> str:
        with open(solver) as f:
            content = f.read()
        if "\nmain " not in content:
            folder = os.sep.join(solver.split(os.sep)[:-1])
            readme = os.path.join(folder, "Readme.md")
            if os.path.isfile(readme):
                with open(readme) as f:
                    readme_content = f.read()
                main_content = HSMod.make_main(readme_content)
                if main_content:
                    solver = os.path.join(folder, ".__solver__.hs")
                    with open(solver, "w") as f:
                        f.write(content + "\n")
                        f.write(main_content)
        return solver

    @staticmethod
    def prepare_exec(solver: str, keep_temp: bool) -> Tuple[str, bool]:
        if os.sep not in solver and os.path.isfile("." + os.sep + solver):
            solver = "." + os.sep + solver
        if " " in solver:  # more than one parameter
            return solver, False
        elif solver.endswith(".py"):
            return "python3 " + solver, False
        elif solver.endswith(".js"):
            return "node " + solver, False
        elif solver.endswith(".c"):
            solver_cmd = Compiler.__prepare_c(solver)
            return solver_cmd, True
        elif solver.endswith(".cpp"):
            solver_cmd = Compiler.__prepare_cpp(solver)
            return solver_cmd, True
        elif solver.endswith(".hs"):
            solver_cmd = Compiler.__prepare_hs(solver, keep_temp)
            return solver_cmd, True
        else:
            return solver, False


class Identifier:
    class Type(Enum):
        WDIR = "WORKING DIR"
        OBI = "OBI"
        MD = "MD"
        TIO = "TIO"
        VPL = "VPL"
        SOLVER = "SOLVER"

    @staticmethod
    def get_type(target: str) -> Type:
        parts = target.split(" ")
        if os.path.isdir(target):
            return Identifier.Type.WDIR
        elif len(parts) == 3 and "@" in parts[1] and "@" in parts[2]:
            return Identifier.Type.OBI
        elif target.endswith(".md"):
            return Identifier.Type.MD
        elif target.endswith(".tio"):
            return Identifier.Type.TIO
        elif target.endswith(".vpl"):
            return Identifier.Type.VPL
        else:
            return Identifier.Type.SOLVER

    @staticmethod
    def split_input_list(input_list: List[str]) -> Tuple[List[str], List[str], List[str]]:
        folders = [target for target in input_list if Identifier.get_type(target) == Identifier.Type.WDIR]
        others = [target for target in input_list if target not in folders]
        solvers = [target for target in others if Identifier.get_type(target) == Identifier.Type.SOLVER]
        sources = [target for target in others if target not in solvers]
        return solvers, sources, folders

    @staticmethod
    def mount_wdir_list(target_list: List[str], param: Param.Basic) -> List[Wdir]:
        wdir_list = []
        solvers, sources, folders = Identifier.split_input_list(target_list)
        if len(target_list) == 0:
            folders = ["."]
        if sources or solvers:
            wdir_list.append(Wdir(".").sources(sources).solvers(solvers).parse_sources().filter(param.index))
        if folders:
            wdir_list += [Wdir(f).load_solvers().load_sources().parse_sources().filter(param.index) for f in folders]
        return wdir_list


class Execution:
    class Result(Enum):
        UNTESTED = "UNTESTED"
        SUCCESS = "SUCCESS"
        WRONG_OUTPUT = "WRONG OUTPUT"
        COMPILATION_ERROR = "COMPILATION ERROR"
        EXECUTION_ERROR = "EXECUTION ERROR"

    @staticmethod
    def __process_input(exec_cmd: str, input_data: str) -> str:
        cmd = exec_cmd.split(" ")
        return_code, stdout, stderr = Runner.subprocess_run(cmd, input_data)
        if return_code != 0:
            raise Runner.ExecutionError(stdout + stderr)
        return stdout

    @staticmethod
    def __fill_user_answers(solver: Solver, unit_list: List[Unit], keep: bool = False) -> None:
        exec_cmd, is_temp_file = Compiler.prepare_exec(solver.path, keep)
        for i in range(len(unit_list)):
            solver.user.append(None)
        for i in range(len(unit_list)):
            solver.user[i] = Execution.__process_input(exec_cmd, unit_list[i].input)
        if is_temp_file and not keep:
            os.remove(exec_cmd)

    @staticmethod
    def __check_all_answers_right(solver: Solver, unit_list: List[Unit]) -> bool:
        return len([unit for unit, output in zip(unit_list, solver.user) if unit.output == output]) == len(unit_list)

    @staticmethod
    def execute_solver(solver: Solver, unit_list: List[Unit], keep: bool = False) -> None:
        try:
            Execution.__fill_user_answers(solver, unit_list, keep)
            if Execution.__check_all_answers_right(solver, unit_list):
                solver.result = Execution.Result.SUCCESS
            else:
                solver.result = Execution.Result.WRONG_OUTPUT
        except Runner.CompileError as e:
            solver.result = Execution.Result.COMPILATION_ERROR
            solver.error_msg = str(e)
        except Runner.ExecutionError as e:
            solver.result = Execution.Result.EXECUTION_ERROR
            solver.error_msg = str(e)


class Report:
    __term_width: Optional[int] = None

    @staticmethod
    def get_terminal_size():
        if Report.__term_width is None:
            term_width = shutil.get_terminal_size()[0]
            if term_width % 2 == 0:
                term_width -= 1
            Report.__term_width = term_width
        return Report.__term_width

    @staticmethod
    def centralize(text, sep=' ', left_border: Optional[str] = None, right_border: Optional[str] = None):
        if left_border is None:
            left_border = sep
        if right_border is None:
            right_border = sep
        term_width = Report.get_terminal_size()
        pad = sep if len(text) % 2 == 0 else ""
        tw = term_width - 2
        filler = sep * int(tw / 2 - len(text) / 2)
        return left_border + pad + filler + text + filler + right_border

    @staticmethod
    def max_just_calc(mat: List[List[str]]) -> List[int]:

#        ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')

        nl = len(mat)
        nc = len(mat[0]) if nl > 0 else 0
        max_list = [0] * nc
        for line in range(nl):
            for c in range(nc):
                data = mat[line][c]
#                data = ansi_escape.sub('', data)
                max_list[c] = max(max_list[c], len(data))
        return max_list

    @staticmethod
    def left_just(mat: List[List[str]]) -> List[List[str]]:
        max_list = Report.max_just_calc(mat)
        output = []
        for line in mat:
            out = []
            for i in range(len(line)):
                if i == 0:
                    out.append(line[i].center(max_list[i], Symbol.cfill))
                else:
                    out.append(line[i].center(max_list[i], Symbol.cfill))
            output.append(out)
        return output

    @staticmethod
    def format_header(user: Optional[str], unit: Unit, source_fill: int = 0, case_fill: int = 0):
        front = ""
        grade = str(unit.grade).zfill(3) if unit.grade else "---"
        if not user:
            front += Symbol.neutral
        elif user == unit.output:
            front += Symbol.success
        else:
            front += Symbol.failure
        front += "[" + str(unit.index).zfill(2) + "] GR:" + grade
        line = front + " " + unit.source.ljust(source_fill) + " (" + unit.case.ljust(case_fill) + ")"
        gr = "      " if unit.duplicated is None else " [" + str(unit.duplicated).zfill(2) + "] "
        return line + gr

    @staticmethod
    def calc_filler(unit_list: List[Unit]) -> List[int]:
        mat = [[x.source, x.case] for x in unit_list]
        max_list = Report.max_just_calc(mat)
        return max_list

    @staticmethod
    def format_header_list(solver: Optional[Solver], unit_list: List[Unit], filler: List[int]) -> str:
        user_list = solver.user if solver else [None] * len(unit_list)
        out = [Report.format_header(output, unit, filler[0], filler[1]) for output, unit in zip(user_list, unit_list)]
        return '\n'.join(out)

    @staticmethod
    def render_white(text: Optional[str]) -> Optional[str]:
        if text is None:
            return None
        text = text.replace(' ', Symbol.whitespace)
        text = text.replace('\n', Symbol.newline + '\n')
        return text

    @staticmethod
    def side_by_side(text_a, text_b, sep=" "):
        term_width = Report.get_terminal_size()
        middle = int(term_width / 2)
        ta = text_a.split("\n")
        tb = text_b.split("\n")
        size = max(len(ta), len(tb)) - 1
        data = [list(" " * term_width) for _x in range(size)]

        for line in range(size):
            if line < len(ta) and line < len(tb) and ta[line] == tb[line]:
                data[line][middle] = sep
            else:
                data[line][middle] = "≠"

        for line in range(len(ta)):
            for col in range(len(ta[line])):
                if ta[line][col] != ' ' and col < middle - 1:
                    data[line][col + 1] = ta[line][col]

        for line in range(len(tb)):
            for col in range(len(tb[line])):
                if tb[line][col] != ' ' and col < middle - 1:
                    data[line][col + middle + 2] = tb[line][col]

        return "\n".join(["".join(line) for line in data])

    @staticmethod
    def show_unit_list(solver: Optional[Solver], unit_list: List[Unit], is_raw: bool) -> str:
        output = io.StringIO()
        user_lists = solver.user if solver else [None] * len(unit_list)
        for user, unit in zip(user_lists, unit_list):
            output.write(Report.__show_unit(user, unit, is_raw))
        if is_raw or not solver:
            output.write(Report.centralize(Symbol.hbar, Symbol.hbar) + "\n")
        else:
            output.write(Report.centralize("   ", Symbol.hbar, " ", " ") + "\n")
        return output.getvalue()

    @staticmethod
    def __show_unit(user: Optional[str], unit: Unit, is_raw: bool = False) -> str:

        def mount_side_title(left, right, filler=" ", middle=" "):
            half = int(Report.get_terminal_size() / 2)
            line = " " + left.center(half - 2, filler) + " "
            line += middle
            line += " " + right.center(half - 2, filler) + " "
            return line

        output = io.StringIO()
        str_input = Report.render_white(unit.input) if not is_raw else unit.input
        str_output = Report.render_white(unit.output) if not is_raw else unit.output
        str_user = Report.render_white(user) if not is_raw else user

        title = " ".join(Report.format_header(user, unit).split(" ")[1:])

        dotted = "-"
        vertical_separator = Symbol.vbar

        if is_raw or not str_user:
            output.write(Report.centralize(Symbol.hbar, Symbol.hbar) + "\n")
            output.write(Report.centralize(title) + "\n")
            output.write(Report.centralize("PROGRAM INPUT", dotted) + "\n")
            output.write(str_input)
            output.write(Report.centralize("EXPECTED OUTPUT", dotted) + "\n")
            output.write(str_output)
            if str_user:
                output.write(Report.centralize("USER OUTPUT", dotted) + "\n")
                output.write(str_user)
        else:
            output.write(Report.centralize("   ", Symbol.hbar, " ", " ") + "\n")
            output.write(mount_side_title(title, title, " ", vertical_separator) + "\n")
            output.write(mount_side_title(" INPUT ", " INPUT ", dotted, vertical_separator) + "\n")
            output.write(Report.side_by_side(str_input, str_input, vertical_separator) + "\n")
            output.write(mount_side_title(" EXPECTED OUTPUT ", " USER OUTPUT ", dotted, vertical_separator) + "\n")
            output.write(Report.side_by_side(str_output, str_user, vertical_separator) + "\n")

        return output.getvalue()

    @staticmethod
    def qtd_tests_ratio(unit_list: List[Unit]) -> str:
        unique_qtd = len([x for x in unit_list if x.duplicated is None])
        return "[" + str(unique_qtd).zfill(2) + "/" + str(len(unit_list)).zfill(2) + "]"

    @staticmethod
    def format_resume(line: List[Optional[str]]) -> str:
        out = Symbol.opening
        if line[0]:
            out += line[0]
        if line[1]:
            out += " (" + line[1] + ")"
        if line[2]:
            out += " [" + line[2] + "]"
        if line[3]:
            out += " [" + line[3] + "]"
        return out


class PatternLoader:
    class FileSource:
        def __init__(self, label, input_file, output_file):
            self.label = label
            self.input_file = input_file
            self.output_file = output_file

        def __eq__(self, other):
            return self.label == other.label and self.input_file == other.input_file and \
                   self.output_file == other.output_file

    def __init__(self, input_pattern: str, output_pattern: str):
        if input_pattern == "" or input_pattern == "@":
            input_pattern = "@.in"
        if output_pattern == "" or output_pattern == "@":
            output_pattern = "@.sol"
        self.input_pattern = input_pattern
        self.output_pattern = output_pattern
        self._check_pattern()

    def _check_pattern(self):
        self.__check_double_wildcard()
        self.__check_missing_wildcard()

    def __check_double_wildcard(self):
        if self.input_pattern.count("@") > 1 or self.output_pattern.count("@") > 1:
            raise ValueError("  fail: the wildcard @ should be used only once per pattern")

    def __check_missing_wildcard(self):
        if "@" in self.input_pattern and "@" not in self.output_pattern:
            raise ValueError("  fail: is input_pattern has the wildcard @, the input_patter should have too")
        if "@" not in self.input_pattern and "@" in self.output_pattern:
            raise ValueError("  fail: is output_pattern has the wildcard @, the input_pattern should have too")

    def make_file_source(self, label):
        return PatternLoader.FileSource(label, self.input_pattern.replace("@", label),
                                        self.output_pattern.replace("@", label))

    def get_file_sources(self, filename_list: List[str]) -> List[FileSource]:
        input_re = self.input_pattern.replace(".", "\\.")
        input_re = input_re.replace("@", "(.*)")
        file_source_list = []
        for filename in filename_list:
            match = re.findall(input_re, filename)
            if not match:
                continue
            label = match[0]
            file_source = self.make_file_source(label)
            if file_source.output_file not in filename_list:
                Logger.write("fail: file " + file_source.output_file + " not found\n")
            else:
                file_source_list.append(file_source)
        return file_source_list

    def get_odd_files(self, filename_list) -> List[str]:
        matched = []
        sources = self.get_file_sources(filename_list)
        for source in sources:
            matched.append(source.input_file)
            matched.append(source.output_file)
        unmatched = [file for file in filename_list if file not in matched]
        return unmatched


class Writer:
    @staticmethod
    def to_vpl(unit: Unit):
        text = "case=" + unit.case + "\n"
        text += "input=" + unit.input
        text += "output=\"" + unit.output + "\"\n"
        if unit.grade:
            text += "grade reduction=" + str(unit.grade) + "%"
        return text

    @staticmethod
    def to_tio(unit: Unit):
        text = ">>>>>>>>"
        if unit.case != '':
            text += " " + unit.case
        if not unit.grade:
            text += " " + "!%"
        elif unit.grade != "100":
            text += " " + str(unit.grade) + "%"
        text += '\n' + unit.input
        text += "========\n"
        text += unit.output
        text += "<<<<<<<<"
        return text + '\n'

    @staticmethod
    def save_dir_files(folder: str, pattern_loader: PatternLoader, label: str, unit: Unit) -> None:
        file_source = pattern_loader.make_file_source(label)
        with open(os.path.join(folder, file_source.input_file), "w") as f:
            f.write(unit.input)
        with open(os.path.join(folder, file_source.output_file), "w") as f:
            f.write(unit.output)

    @staticmethod
    def save_target(target: str, unit_list: List[Unit], force: bool = False):
        def ask_overwrite(file):
            Logger.inc_level()
            Logger.write("file " + file + " found. Overwrite? (y/n) ")
            resp = input()
            Logger.inc_level()
            if resp.lower() == 'y':
                Logger.write("overwrite allowed\n")
                return True
            Logger.write("overwrite denied\n")
            Logger.dec_level()
            Logger.dec_level()
            return False

        def save_dir(_target, _unit_list):
            folder, ipat, opat = _target.split(" ")
            if os.path.isdir(folder) or os.path.isfile(folder):
                raise FileExistsError("fail: build dir now allowed to overwrite file or directory")
            else:
                os.mkdir(folder)
                pattern_loader = PatternLoader(ipat, opat)
                number = 0
                for unit in _unit_list:
                    Writer.save_dir_files(folder, pattern_loader, str(number).zfill(2), unit)
                    number += 1

        def save_file(_target, _unit_list):
            exists = os.path.isfile(_target)
            if not exists or (exists and (force or ask_overwrite(_target))):
                with open(_target, "w") as f:
                    if _target.endswith(".tio"):
                        f.write("\n".join([Writer.to_tio(unit) for unit in _unit_list]))
                    else:
                        f.write("\n".join([Writer.to_vpl(unit) for unit in _unit_list]))
                    if not force:
                        Logger.write("file " + _target + " wrote\n")

        target_type = Identifier.get_type(target)
        if target_type == Identifier.Type.OBI:
            save_dir(target, unit_list)
        elif target_type == Identifier.Type.TIO or target_type == Identifier.Type.VPL:
            save_file(target, unit_list)
        else:
            Logger.write("fail: target " + target + " do not supported for build operation\n")


class Replacer:
    @staticmethod
    def _get_borders(regex, text, options) -> List[str]:
        out = []
        last = 0
        for m in re.finditer(regex, text, options):
            out.append(text[last:m.span()[0]])
            last = m.span()[1]
        out.append(text[last:])
        return out

    @staticmethod
    def _merge_tests(borders, tests):
        out = []
        for i in range(len(borders)):
            out.append(borders[i])
            if i < len(tests):
                out.append(tests[i])
        return out

    @staticmethod
    def insert_tests(regex: str, text: str, options: int, tests: List[str]) -> str:
        borders = Replacer._get_borders(regex, text, options)
        return "".join(Replacer._merge_tests(borders, tests))


class Util:
    @staticmethod
    def copy_to_temp(folder):
        temp_dir = tempfile.mkdtemp()
        for file in os.listdir(folder):
            if os.path.isfile(os.path.join(folder, file)):
                shutil.copyfile(os.path.join(folder, file), os.path.join(temp_dir, file))
        return temp_dir


class Param:
    class DiffMode(Enum):
        FIRST = "MODE: SHOW FIRST FAILURE ONLY"
        NONE = "MODE: SHOW NONE FAILURES"
        ALL = "MODE: SHOW ALL FAILURES"

    class Basic:
        def __init__(self, index: Optional[int] = None, is_brief: bool = False, is_raw: bool = False):
            self.index = index
            self.is_brief = is_brief
            self.is_raw = is_raw
            self.keep = False
            self.display = False
            self.diff_mode = Param.DiffMode.FIRST

        def set_keep(self, value) -> Param.Basic:
            self.keep = value
            return self

        def set_display(self, value) -> Param.Basic:
            self.display = value
            return self

        def set_diff_mode(self, value: Param.DiffMode) -> Param.Basic:
            self.diff_mode = value
            return self

    class Manip:
        def __init__(self, unlabel: bool = False, to_sort: bool = False, to_number: bool = False):
            self.unlabel = unlabel
            self.to_sort = to_sort
            self.to_number = to_number


class ActionExecute:
    @staticmethod
    def execute(target_list: List[str], param: Param.Basic) -> List[Tuple[str, int, List[Tuple[str, int]]]]:
        wdir_list = Identifier.mount_wdir_list(target_list, param)
        resume_list = [wdir.resume() for wdir in wdir_list]
        sizes = Report.max_just_calc(resume_list)
        for resume, wdir in zip(resume_list, wdir_list):
            ActionExecute.print_resume_begin(resume, sizes)
            ActionExecute.print_solvers(wdir, sizes[3], False)
            if not param.is_brief:
                for solver in wdir.solver_list:
                    errors = ActionExecute.report_failure(solver, wdir.unit_list)
                    if errors != "":
                        Logger.write(errors, relative=1)
                    diffs = ActionExecute.report_diffs(solver, wdir.unit_list, param)
                    if diffs != "":
                        Logger.write(diffs)
                    if solver.result != Execution.Result.SUCCESS and param.diff_mode == Param.DiffMode.FIRST:
                        break
        return ActionExecute.calc_passed(wdir_list)

    @staticmethod
    def print_resume_begin(resume: List[str], sizes: List[int]):
        _resume = [resume[0].ljust(sizes[0], Symbol.cfill), resume[1].center(sizes[1], Symbol.cfill), resume[2].center(sizes[2], Symbol.cfill), None]
        Logger.write(Report.format_resume(_resume))

    @staticmethod
    def print_solver_i(solver_list: List[Solver], i: int, total_size: int, acc: int):
        if i == 0:
            filled_size = len(", ".join([Symbol.success + solver.filename for solver in solver_list]))
            _acc = (total_size - filled_size) / 2
            acc = int(_acc)
            Logger.write(" [" + Symbol.cfill * acc)
        solver = solver_list[i]
        Logger.write(solver.get_mark() + solver.filename)
        acc += len(solver.get_mark() + solver.filename)
        if i != len(solver_list) - 1:
            Logger.write(", ")
            acc += 2
        if i == len(solver_list) - 1:
            if solver_list[0].result == Execution.Result.UNTESTED:
                final_mark = Symbol.neutral
            else:
                passed = len([solver for solver in solver_list if solver.result == Execution.Result.SUCCESS])
                final_mark = Symbol.success if passed == len(solver_list) else Symbol.failure
            Logger.write((total_size - acc) * Symbol.cfill + "] " + final_mark + "\n")
        return acc

    @staticmethod
    def print_solvers(wdir: Wdir, total_size: int, only_show: bool = False):
        acc = 0
        if len(wdir.solver_list) == 0:
            Logger.write(" [" + Symbol.failure.center(total_size, Symbol.cfill) + "] " + Symbol.failure + "\n")
            return
        for i, solver in enumerate(wdir.solver_list):
            if not only_show:
                Execution.execute_solver(solver, wdir.unit_list)
            acc = ActionExecute.print_solver_i(wdir.solver_list, i, total_size, acc)

    @staticmethod
    def report_failure(solver: Solver, unit_list: List[Unit]) -> str:
        if solver.result == Execution.Result.SUCCESS:
            return ""
        output = IOBuffer()
        if solver.result == Execution.Result.WRONG_OUTPUT:
            output.write(solver.get_mark() + Symbol.opening + solver.path + " " + solver.result.name + '\n')
            output.write(Report.format_header_list(solver, unit_list, Report.calc_filler(unit_list)) + '\n', 1)
        else:
            output.write(solver.get_mark() + Symbol.opening + solver.path + " " + solver.result.name + "\n")
            output.write(solver.error_msg + "\n", 1)
        return output.getvalue()

    @staticmethod
    def report_diffs(solver: Solver, unit_list: List[Unit], param: Param.Basic) -> str:
        if solver.result != Execution.Result.WRONG_OUTPUT:
            return ""
        output = IOBuffer()
        if param.diff_mode != Param.DiffMode.NONE:
            unit_list = [unit for user, unit in zip(solver.user, unit_list) if user != unit.output]
            if param.diff_mode == Param.DiffMode.FIRST:
                unit_list = [unit_list[0]]
                output.write(Report.centralize("MODE: FIRST FAILURE ONLY") + "\n")
            else:
                output.write(Report.centralize("MODE: ALL FAILURES") + "\n")

            output.write(Report.show_unit_list(solver, unit_list, param.is_raw))
        return output.getvalue()

    @staticmethod
    def calc_passed(wdir_list: List[Wdir]) -> List[Tuple[str, int, List[Tuple[str, int]]]]:
        output: List[Tuple[str, int, List[Tuple[str, int]]]] = []
        for wdir in wdir_list:
            wdir_out: List[Tuple[str, int]] = []
            for solver in wdir.solver_list:
                passed = len([unit for user, unit in zip(solver.user, wdir.unit_list) if user == unit.output])
                wdir_out.append((solver.filename, passed))
            output += [(wdir.folder, len(wdir.unit_list), wdir_out)]
        return output


class ActionList:

    @staticmethod
    def list(target_list: List[str], param: Param.Basic) -> List[Tuple[str, int]]:
        wdir_list = Identifier.mount_wdir_list(target_list, param)
        resume_list = [wdir.resume() for wdir in wdir_list]
        sizes = Report.max_just_calc(resume_list)
        headers_filler = ActionList.calc_filler(wdir_list)
        for resume, wdir in zip(resume_list, wdir_list):
            ActionExecute.print_resume_begin(resume, sizes)
            ActionExecute.print_solvers(wdir, sizes[3], True)
            #        wdir_list = Identifier.mount_wdir_list(target_list, param)
            #        resume_list = ActionList.format_resume(wdir_list)
            #        for wdir, resume in zip(wdir_list, resume_list):
#            Logger.write(resume + "\n")
            if not param.is_brief:
                if wdir.unit_list:
                    Logger.write(Report.format_header_list(None, wdir.unit_list, headers_filler) + '\n', relative=1)
                if param.display:
                    Logger.write(Report.show_unit_list(None, wdir.unit_list, param.is_raw), 0)
        return [(wdir.folder, len(wdir.unit_list)) for wdir in wdir_list]

    @staticmethod
    def calc_filler(wdir_list: List[Wdir]) -> List[int]:
        all_unit_lists = []
        for wdir in wdir_list:
            all_unit_lists += wdir.unit_list
        return Report.calc_filler(all_unit_lists)

    @staticmethod
    def format_resume(wdir_list: List[Wdir]) -> List[str]:
        mat = [wdir.resume() for wdir in wdir_list]
        mat = Report.left_just(mat)
        return [Report.format_resume(line) for line in mat]


class Actions:
    @staticmethod
    def compile(solver: str, keep: bool):
        result = False
        Logger.inc_level()
        try:
            executable, is_temp = Compiler.prepare_exec(solver, keep)
            if is_temp:
                Logger.write("executable ready as " + executable + '\n')
                result = True
            else:
                Logger.write(solver + " cannot be compiled\n")
        except Runner.CompileError as e:
            Logger.write("compilation error\n")
            Logger.write(str(e) + '\n')
        Logger.dec_level()
        return result

    @staticmethod
    def list(target_list: List[str], param: Param.Basic) -> List[Tuple[str, int]]:
        return ActionList.list(target_list, param)

    @staticmethod
    def execute(target_list: List[str], param: Param.Basic) -> List[Tuple[str, int, List[Tuple[str, int]]]]:
        return ActionExecute.execute(target_list, param)

    @staticmethod
    def build(target_out: str, source_list: List[str], param: Param.Manip, to_force: bool) -> bool:
        try:
            Logger.inc_level()
            wdir = Wdir(".").sources(source_list).parse_sources()
            wdir.manipulate(param)
            Writer.save_target(target_out, wdir.unit_list, to_force)
            Logger.dec_level()
        except FileNotFoundError as e:
            Logger.write(str(e) + "\n")
            Logger.dec_level()
            return False
        return True

    @staticmethod
    def update(target_list: List[str], param: Param.Manip, solver: Optional[str]) -> bool:
        for target in target_list:
            wdir = Wdir(".").sources([target]).parse_sources()
            wdir.manipulate(param)
            if solver:
                wdir.replace_input(Solver(solver))
            if not target.endswith(".md"):
                Writer.save_target(target, wdir.unit_list, True)
            else:
                with open(target) as f:
                    text = f.read()
                str_tests = [unit.to_tio() for unit in wdir.unit_list]
                output = Replacer.insert_tests(Loader.regex_tio, text, re.MULTILINE | re.DOTALL, str_tests)
                with open(target, "w") as f:
                    f.write(output)
        return True


class Main:
    @staticmethod
    def execute(args):
        param = Param.Basic(args.index, args.brief, args.raw)
        if args.all:
            param.set_diff_mode(Param.DiffMode.ALL)
        elif args.none:
            param.set_diff_mode(Param.DiffMode.NONE)
        if Actions.execute(args.target_list, param):
            return 0
        return 1

    @staticmethod
    def compile(args):
        if Actions.compile(args.cmd, args.keep):
            return 0
        return 1

    @staticmethod
    def list(args):
        Actions.list(args.target_list, Param.Basic(args.index, args.brief, args.raw).set_display(args.display))
        return 0

    @staticmethod
    def build(args):
        Actions.build(args.target, args.target_list, Param.Manip(args.unlabel, args.sort, args.number), args.force)
        return 0

    @staticmethod
    def update(args):
        Actions.update(args.target_list, Param.Manip(args.unlabel, args.sort, args.number), args.cmd)
        return 0

    @staticmethod
    def tkupdate(args):
        tdir = tempfile.mkdtemp()
        installer = os.path.join(tdir, "installer.sh")
        cmd = ["wget", "https://raw.githubusercontent.com/senapk/tk/master/tools/install_linux.sh", "-O", installer]
        code, data, error = Runner.subprocess_run(cmd)
        if code != 0:
            print(error)
            exit(1)
        cmd = ["sh", installer]
        code, out, err = Runner.subprocess_run(cmd)
        if code == 0:
            print(out)
        else:
            print(err)
        return 0

    @staticmethod
    def main():
        parent_basic = argparse.ArgumentParser(add_help=False)
        parent_basic.add_argument('--brief', '-b', action='store_true', help="show less information.")
        parent_basic.add_argument('--raw', '-r', action='store_true', help="raw mode, disable  whitespaces rendering.")
        parent_basic.add_argument('--index', '-i', metavar="I", type=int, help='run a specific index.')

        parent_manip = argparse.ArgumentParser(add_help=False)
        parent_manip.add_argument('--unlabel', '-u', action='store_true', help='remove all labels.')
        parent_manip.add_argument('--number', '-n', action='store_true', help='number labels.')
        parent_manip.add_argument('--sort', '-s', action='store_true', help="sort test cases by input size.")

        desc = ("Roda, Converte e Contrói testes de entrada e saída.\n"
                "Use \"./tk comando -h\" para obter informações do comando específico.\n\n"
                "Exemplos:\n"
                "    ./tk list t.vpl                        # lista os testes\n"
                "    ./tk list t.vpl -d                     # mostra os testes\n"
                "    ./tk list t.vpl -t 5                   # mostra o teste 5\n"
                "    ./tk compile main.c                    # apenas compila o arquivo main.c para main.c.out\n"
                "    ./tk run solver.c t.tio                # roda o comando e verifica utilizando o arquivo t.tio\n"
                "    ./tk run solver.exe t.vpl              # roda o comando e verifica utilizando o arquivo t.vpl\n"
                )

        parser = argparse.ArgumentParser(prog='tk', formatter_class=argparse.RawDescriptionHelpFormatter, description=desc,)
        subparsers = parser.add_subparsers(title='subcommands', help='help for subcommand.')

        # list
        parser_s = subparsers.add_parser('list', parents=[parent_basic], help='show case packs or folders.')
        parser_s.add_argument('target_list', metavar='T', type=str, nargs='*', help='targets.')
        parser_s.add_argument('--display', '-d', action="store_true", help='display full test description.')
        parser_s.set_defaults(func=Main.list)

        # run
        parser_r = subparsers.add_parser('run', parents=[parent_basic], help='run you solver.')
        parser_r.add_argument('target_list', metavar='T', type=str, nargs='*', help='solvers, test cases or folders.')
        parser_r.add_argument('--all', '-a', action='store_true', help="show all failures.")
        parser_r.add_argument('--none', '-n', action='store_true', help="show none failures.")
        parser_r.set_defaults(func=Main.execute)

        # build
        parser_b = subparsers.add_parser('build', parents=[parent_manip], help='build a test target.')
        parser_b.add_argument('target', metavar='T_OUT', type=str, help='target to be build.')
        parser_b.add_argument('target_list', metavar='T', type=str, nargs='+', help='input test targets.')
        parser_b.add_argument('--force', '-f', action='store_true', help='enable overwrite.')
        parser_b.set_defaults(func=Main.build)

        # update
        parser_b = subparsers.add_parser('update', parents=[parent_manip], help='update a test target.')
        parser_b.add_argument('target_list', metavar='T', type=str, nargs='+', help='input test targets.')
        parser_b.add_argument('--cmd', '-c', type=str, help="solver file or command to update outputs.")
        parser_b.set_defaults(func=Main.update)

        # compile
        parser_c = subparsers.add_parser('compile', help='compile you solver.')
        parser_c.add_argument('cmd', type=str, help="solver cmd to compile.")
        parser_c.add_argument('--keep', '-k', action='store_true', help="keep all compilation files.")
        parser_c.set_defaults(func=Main.compile)

        parser_tkupdate = subparsers.add_parser('tkupdate', help='update tk script(linux only).')
        parser_tkupdate.set_defaults(func=Main.tkupdate)

        args = parser.parse_args()
        if len(sys.argv) == 1:
            Actions.execute([""], Param.Basic())
        else:
            try:
                args.func(args)
            except ValueError as e:
                Logger.write(str(e) + '\n')


if __name__ == '__main__':
    Main.main()
