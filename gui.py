#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from enum import Enum
from typing import List, Tuple, Any, Optional
import os
import subprocess
import shutil
import io
from subprocess import PIPE
import configparser

class Color(Enum):
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
    def paint(text: str, color: Color, color2: Optional[Color] = None) -> str:
        return Colored.__map[color] + ("" if color2 is None else Colored.__map[color2]) + text + Colored.__map[Color.RESET]

    @staticmethod
    def green(text: str) -> str:
        return Colored.paint(text, Color.GREEN)
    
    @staticmethod
    def red(text: str) -> str:
        return Colored.paint(text, Color.RED)
    
    @staticmethod
    def magenta(text: str) -> str:
        return Colored.paint(text, Color.MAGENTA)
    
    @staticmethod
    def yellow(text: str) -> str:
        return Colored.paint(text, Color.YELLOW)
    
    @staticmethod
    def blue(text: str) -> str:
        return Colored.paint(text, Color.BLUE)

    @staticmethod
    def ljust(text: str, width: int) -> str:
        return text + ' ' * (width - Colored.len(text))

    @staticmethod
    def center(text: str, width: int, filler) -> str:
        return filler * ((width - Colored.len(text)) // 2) + text + filler * ((width - Colored.len(text) + 1) // 2)

    @staticmethod
    def remove_colors(text: str) -> str:
        for color in Colored.__map.values():
            text = text.replace(color, '')
        return text

    @staticmethod
    def len(text):
        return len(Colored.remove_colors(text))


class Report:
    __term_width: Optional[int] = None

    def __init__(self):
        pass

    @staticmethod
    def update_terminal_size():
        term_width = shutil.get_terminal_size().columns
        if term_width % 2 == 0:
            term_width -= 1
        Report.__term_width = term_width

    @staticmethod
    def get_terminal_size():
        if Report.__term_width is None:
            Report.update_terminal_size()

        return Report.__term_width

    @staticmethod
    def set_terminal_size(value: int):
        if value % 2 == 0:
            value -= 1
        Report.__term_width = value

    @staticmethod
    def centralize(text, sep=' ', left_border: Optional[str] = None, right_border: Optional[str] = None) -> str:
        if left_border is None:
            left_border = sep
        if right_border is None:
            right_border = sep
        term_width = Report.get_terminal_size()

        size = Colored.len(text)
        pad = sep if size % 2 == 0 else ""
        tw = term_width - 2
        filler = sep * int(tw / 2 - size / 2)
        return left_border + pad + filler + text + filler + right_border

class Choose:
    base = ["poo", "ed", "fup"]
    view = ["down", "side"]
    extensions  = ["c", "cpp", "js", "ts", "py", "java"]

    def validate(ui: List[str], data_list: List[str]) -> Optional[str]:
        if len(ui) == 2:
            opts = [opt for opt in data_list if ui[1] in opt]
            if len(opts) == 1:
                return opts[0]
        return None

    def validate_or_choose_one(initial: str, ui: List[str], data_list: List[str]) -> str:
        value = Choose.validate(ui, data_list)
        if value is not None:
            return value
        value = Choose.choose_one(data_list)
        if value is not None:
            return value
        return initial
        

    def choose_many(data_list) -> List[str]:
        data_list = sorted(data_list)
        if (len(data_list) == 0):
            print("Sem opções disponíveis")
            return []
        options = []
        for i, data in enumerate(data_list):
            options.append(f"{Colored.green(str(i))}={data}")
        print("Digite os índices separando por espaço\n" + ", ".join(options) + ": ", end = "")
        choices = input()
        try:
            values = [data_list[int(choice)] for choice in choices.split(" ")]
            print("Opções escolhidas: " + Colored.green("[" + ", ".join(values) + "]"))
            return values
        except:
            pass
        return []

    def choose_one(data_list: List[str]) -> Optional[str]:
        if len(data_list) == 0:
            print("Sem opções disponíveis")
            return None
        options = []
        for i, data in enumerate(data_list):
            options.append(f"{Colored.green(str(i))}={data}")
        print(", ".join(options), end = "")
        choice = ""
        print(": ", end="")
        choice = input()
        try:
            index = int(choice)
            if index >= 0 and index < len(data_list):
                print("Opção escolhida: " + Colored.green(data_list[index]))
                return data_list[index]
        except:
            pass
        print("Opção inválida")
        return None

    def choose_index(ui):
        if len(ui) == 2:
            try:
                return int(ui[1])
            except:
                pass
        print("Choose test index or -1 for all: ", end="")
        choice = input()
        try:
            return int(choice)
        except:
            pass
        return -1

class Config:
    default_config_file = ".tkgui.ini"
        
    def __init__(self):
        self.view: str = ""          # updown or sidebyside diff
        self.base: str = ""          # which base to use
        self.case: int = -1          # run all or a specific index case
        self.folder: str = ""        # which folder to use
        self.tests: List[str] = []   # files with test testcases
        self.solvers: List[str] = [] # files with solvers
        self.last_cmd = ""           # last command
        self.config_file: str = ""   # config file
        self.root = ""               # root folder

    def create_default_config(self):
        config = configparser.ConfigParser()
        config["DEFAULT"] = {
            "base": Choose.base[0],
            "view": Choose.view[0],
            "case": "-1",
            "folder": "/",
            "tests": "",
            "solvers": "",
            "last_cmd": ""
        }
        with open(self.config_file, "w") as f:
            config.write(f)

    @staticmethod
    def validate_config(config):
        if "DEFAULT" not in config:
            return False
        if "base" not in config["DEFAULT"] or config["DEFAULT"]["base"] not in Choose.base:
            return False
        if "view" not in config["DEFAULT"] or config["DEFAULT"]["view"] not in Choose.view:
            return False
        if "case" not in config["DEFAULT"]:
            return False
        if "folder" not in config["DEFAULT"]:
            return False
        if "tests" not in config["DEFAULT"]:
            return False
        if "solvers" not in config["DEFAULT"]:
            return False
        if "last_cmd" not in config["DEFAULT"]:
            return False
        try:
            int(config["DEFAULT"]["case"])
        except:
            return False
        return True

    def save(self):
        config = configparser.ConfigParser()
        config["DEFAULT"] = {
            "base": self.base,
            "view": self.view,
            "case": str(self.case),
            "folder": self.folder,
            "tests": ",".join(self.tests),
            "solvers": ",".join(self.solvers),
            "last_cmd": self.last_cmd
        }
        with open(self.config_file, "w") as f:
            config.write(f)

    def load(self):
        parser = configparser.ConfigParser()

        self.config_file = self.search_config()
        if self.config_file != "":
            print("Loading config file: " + self.config_file)
        else:
            self.config_file = Config.default_config_file
            print("Creating default config file")
            self.create_default_config()
        
        self.root = os.path.dirname(self.config_file)
        os.chdir(self.root)

        parser.read(self.config_file)
        
        if not Config.validate_config(parser):
            print("fail: config file not valid, recreating")
            self.create_default_config()
            parser.read(self.config_file)

        self.base = parser["DEFAULT"]["base"]
        self.view = parser["DEFAULT"]["view"]
        self.case = int(parser["DEFAULT"]["case"])
        self.folder = parser["DEFAULT"]["folder"]
        tests = parser["DEFAULT"]["tests"].split(",")
        self.tests = [] if tests == [""] else tests
        solvers = parser["DEFAULT"]["solvers"].split(",")
        self.solvers = [] if solvers == [""] else solvers
        self.last_cmd = parser["DEFAULT"]["last_cmd"]

    
    def search_config(self) -> str:
        # recursively search for config file in parent directories
        path = os.getcwd()
        filename = Config.default_config_file
        while True:
            configfile = os.path.join(path, filename)
            if os.path.exists(configfile):
                return configfile
            if path == "/":
                return ""
            path = os.path.dirname(path)

    def __str__(self):
        return  "b.ase: " + self.base + "\n" + \
                "v.iew: " + self.view + "\n" + \
                "i.ndex: " + str(self.case) + "\n" + \
                "f.older: " + self.folder + "\n" + \
                "t.ests: " + str(self.tests) + "\n" + \
                "s.olvers: " + str(self.solvers) + "\n" + \
                "config_file: " + self.config_file + "\n"

class GuiActions:

    @staticmethod
    def print_help():
        print("Digite a letra ou o comando e aperte enter.")
        print("")
        print("b ou base: define a base de dados entre as disciplinas fup, ed e poo.")
        print("v ou view: alterna entre mostrar a visualização de erros up_down ou side_by_site.")
        print("c ou case: define o index do caso de teste a ser executado ou -1 para todos.")
        print("")
        print("d ou down: faz o download do problema utilizando o label e a extensão.")
        print("e ou exec: roda o problema esperando a entrada do usuário.")
        print("r ou run : avalia o código do problema contra os casos de testes escolhidos.")
        print("")
        print("h ou help: mostra esse help.")
        print("q ou quit: termina o programa.")
        print("Na linha de execução já aparece o último comando entre (), para reexecutar basta apertar enter.")

    @staticmethod
    def tests(config):
        if config.folder == "/":
            print("fail: selecione um folder primeiro")
            return
        files = os.listdir(config.folder)
        tests = [f for f in files if f.endswith(".tio") or f.endswith(".vpl")]
        config.tests = Choose.choose_many(tests)


    @staticmethod
    def solver(config):
        if config.folder == "/":
            print("fail: selecione um folder primeiro")
            return
        files = os.listdir(config.folder)
        solvers = []
        for ext in Choose.extensions:
            solvers += [f for f in files if f.endswith("." + ext)]
        config.solvers = Choose.choose_many(solvers)

    @staticmethod
    def run(config):
        if config.folder == "/":
            print("fail: selecione um folder primeiro")
            return
        cmd = ["tk", "run"]
        cmd += config.tests
        cmd += config.solvers
        if config.case != -1:
            cmd += ["-i", str(config.case)]
        if config.view == "side":
            cmd += ["-v"]
        print(Colored.green("$ " + " ".join(cmd)))
        os.chdir(config.folder)
        subprocess.run(cmd)
        os.chdir(config.root)

    @staticmethod
    def exec(config):
        if config.folder == "/":
            print("fail: selecione um folder primeiro")
            return
        cmd = ["tk", "exec"]
        cmd += config.solvers
        print(Colored.green("$ " + " ".join(cmd)))
        # imprime _ até o final da linha
        
        
        os.chdir(config.folder)
        subprocess.run(cmd)
        os.chdir(os.path.dirname(config.config_file))

    @staticmethod
    def down(ui_list, config: Config):
        
        def is_number(text):
            try:
                int(text)
                return True
            except:
                return False

        cmd = ["tk", "down"]
        cmd += [config.base]

        label = ""
        if len(ui_list) > 1 and len(ui_list[1]) == 3 and is_number(ui_list[1]):
            label = ui_list[1]
        else:
            print("label: ", end="")
            label = input()
        cmd += [label]
        
        ext = ""
        if len(ui_list) > 2 and ui_list[2] in Choose.extensions:
            ext += ui_list[2]
        else:
            print("ext: ", end="")
            ext = input()
        cmd += [ext]
        
        print("$ " + " ".join(cmd))
        os.chdir(os.path.dirname(config.config_file))
        subprocess.run(cmd)


    @staticmethod
    def list(config):
        if config.folder == "/":
            print("fail: selecione um folder primeiro")
            return
        files = os.listdir(config.folder)
        folders = [f for f in files if os.path.isdir(os.path.join(config.folder, f))]
        readme = [f for f in files if f == "Readme.md"]
        tests = [f for f in files if f.endswith(".tio") or f.endswith(".vpl")]
        solvers = []
        for ext in Choose.extensions:
            solvers += [f for f in files if f.endswith("." + ext)]
        output = []
        for f in folders:
            output.append(Colored.blue(f))
        for f in readme:
            output.append(Colored.red(f))
        for f in tests:
            output.append(Colored.yellow(f))
        for f in solvers:
            output.append(Colored.green(f))
        print("  ".join(output))


    @staticmethod
    def load_folder(ui_list, config):
        folders = ["/"] + [f for f in os.listdir() if os.path.isdir(f)]
        if len(folders) == 0:
            print("Não há pastas para serem carregadas")
        else:        
            config.folder = Choose.validate_or_choose_one(config.folder, ui_list, folders)
            folder = config.folder
            config.tests = []
            config.solvers = []
            if folder == "/":
                return
            for ext in ["tio", "vpl"]:
                config.tests += [f for f in os.listdir(folder) if f.endswith("." + ext)]

            for ext in Choose.extensions:
                config.solvers += [f for f in os.listdir(folder) if f.endswith("." + ext)]
        

    @staticmethod
    def print_header(config):
        base = Colored.yellow(config.base.ljust(4))
        case = str(config.case)
        if case == "-1":
            case = "all"
        case = Colored.yellow(case.ljust(4))
        view = Colored.yellow(config.view.ljust(4))
        last = Colored.blue(config.last_cmd)
        
        folder = config.folder
        tests = "[" + ", ".join(config.tests) + "]"
        solvers = "[" + ", ".join(config.solvers) + "]"
        max_len = max(len(folder), len(tests), len(solvers))

        width = Report.get_terminal_size()
        total = 42
        used = 15
        mode = "side"
        avaliable = width - total - used
        needed = max_len

        length = min(avaliable, needed)
        if (width <= 70) and (total + max_len + used > width):
            mode = "down"
            length = total - used
        # length = total - 13
        cut = length - 4
        if len(folder) > length:
            folder = folder[:cut] + "..."
        if len(tests) > length:
            tests = tests[:cut] + "...]"
        if len(solvers) > length:
            solvers = solvers[:cut] + "...]"

        # larg = (max_len, length)
        folder = Colored.magenta(folder.ljust(length))
        tests = Colored.yellow(tests.ljust(length))
        solvers = Colored.green(solvers.ljust(length))

        def icon(name):
            return Colored.blue(name)

        a = "╭─{}───────{}╮ ╭──{}───────╮ ╭──{}───────╮ ".format("─", "─" * 4, "─", "─")
        b = "│ {} b·ase:{}╰╮╰╮ {} d·own ╰╮╰╮ {} l·ist ╰╮".format(icon("⚙"), base, icon("￬"), icon("⏿"))
        c = "│ {} v·iew:{} │ │ {} e·xec  │ │ {} h·elp  │".format(icon("🗘"), view, icon("▶"), icon("?"))
        d = "│ {} c·ase:{}╭╯╭╯ {} r·un  ╭╯╭╯ {} q·uit ╭╯".format(icon("⇶"), case, icon("✓"), icon("⏻"))
        e = "╰─{}───────{}╯ ╰──{}───────╯ ╰──{}───────╯ ".format("─", "─" * 4, "─", "─")

        f = "╭──{}─────────{}─╮".format("─", "─" * length)
        g = "╰╮ {} f·older:{} │".format(icon("🗀"), folder)
        h = " │ {} t·ests :{} │".format(icon("⇉"), tests)
        i = "╭╯ {} s·olver:{} │".format(icon("⚒"), solvers)
        j = "╰──{}─────────{}─╯".format("─", "─" * length)

        menu = ""
        if mode == "side":
            menu += a + f + "\n" + b + g + "\n" + c + h + "\n" + d + i + "\n" + e + j + "\n"
        else:
            menu += a + "\n" + b + "\n" + c + "\n" + d + "\n" + e + "\n" 
            menu += f + "\n" + g + "\n" + h + "\n" + i + "\n" + j + "\n"
        menu += "[" + last + "] "

        output = io.StringIO()
        for i in range(0, len(menu) - 1):
            if menu[i + 1] == "·":
                output.write(Colored.red(menu[i]))
            else:
                output.write(menu[i])
        output.write(menu[-1])
        menu = output.getvalue()

        print(menu, end="")


def gui_main(_args):
    config = Config()
    config.load()
    while True: 
        Report.update_terminal_size()
        GuiActions.print_header(config)

        line = input()
        if line == "":
            line = config.last_cmd

        ui_list = line.split(" ")
        cmd = ui_list[0]

        if cmd == "q" or cmd == "quit":
            break
        elif cmd == "h" or cmd == "help":
            GuiActions.print_help()
        elif cmd == "b" or cmd == "base":
            config.base = Choose.validate_or_choose_one(config.base, ui_list, Choose.base)
        elif cmd == "v" or cmd == "view":
            config.view = Choose.validate_or_choose_one(config.view, ui_list, Choose.view)
        elif cmd == "c" or cmd == "case":
            config.case = Choose.choose_index(ui_list)
        elif cmd == "d" or cmd == "down":
            GuiActions.down(ui_list, config)
        elif cmd == "e" or cmd == "exec":
            GuiActions.exec(config)
        elif cmd == "r" or cmd == "run":
            GuiActions.run(config)
        elif cmd == "l" or cmd == "list":
            GuiActions.list(config)
        elif cmd == "f" or cmd == "folder":
            GuiActions.load_folder(ui_list, config)
        elif cmd == "t" or cmd == "tests":
            GuiActions.tests(config)
        elif cmd == "s" or cmd == "solver":
            GuiActions.solver(config)
        else:
            print("Invalid command")
        print("\nPressione ENTER para continuar...", end="")
        input()
        print("")
        config.last_cmd = cmd
        config.save()
    config.save()

if __name__ == "__main__":
    gui_main("")