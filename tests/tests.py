#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import unittest
import tk
import os
from typing import Optional
import shutil


def fmt_code_str(data: str):
    print("expected = (")
    lines = ['"' + line + '\\n"' for line in data.split("\n")]
    return "\n".join(lines[:-1]) + ")"


class TestA(unittest.TestCase):
    def test_success(self):
        unit_list = tk.Loader.parse_source("data/00/t.tio")
        self.assertEqual(len(unit_list), 3)
        solver = tk.Solver("data/00/solver_ok.c")
        tk.Execution.execute_solver(solver, unit_list)
        self.assertEqual(solver.result, tk.ExecutionResult.SUCCESS)
        self.assertEqual(3, len([unit for user, unit in zip(solver.user, unit_list) if user == unit.output]))

    def test_compilation_error(self):
        unit_list = tk.Loader.parse_source("data/00/t.tio")
        solver = tk.Solver("data/00/solver_comp.c")
        tk.Execution.execute_solver(solver, unit_list)
        self.assertEqual(solver.result, tk.ExecutionResult.COMPILATION_ERROR)
        self.assertTrue("error: unused variable ‘c’" in solver.error_msg)
        self.assertTrue("cc1: all warnings being treated as errors" in solver.error_msg)

    def test_execution_error(self):
        unit_list = tk.Loader.parse_source("data/00/t.tio")
        solver = tk.Solver("data/00/solver_exec.py")
        tk.Execution.execute_solver(solver, unit_list)
        self.assertEqual(solver.result, tk.ExecutionResult.EXECUTION_ERROR)
        error_msg = "45\n"
        self.assertEqual(solver.error_msg, error_msg)

    def test_wrong_error(self):
        unit_list = tk.Loader.parse_source("data/00/t.tio")
        self.assertEqual(len(unit_list), 3)
        solver = tk.Solver("data/00/solver_wrong.c")
        tk.Execution.execute_solver(solver, unit_list)
        self.assertEqual(solver.result, tk.ExecutionResult.WRONG_OUTPUT)
        self.assertEqual(2, len([unit for user, unit in zip(solver.user, unit_list) if user != unit.output]))


class TestB(unittest.TestCase):
    def test_load_tio(self):
        unit_list = tk.Loader.parse_source("data/02/t.tio")
        cases = list(map(lambda x: x.case, unit_list))
        self.assertEqual(cases, ["sem grade", "gr exclamação", "gr quarenta", "gr 100", "gr bugado", "gr vazio"])
        grades = list(map(lambda x: x.grade, unit_list))
        self.assertEqual(grades, [100, None, 40, 100, 100, None])

    def test_load_vpl(self):
        unit_list = tk.Loader.parse_source("data/02/t.vpl")
        cases = list(map(lambda x: x.case, unit_list))
        self.assertEqual(cases, ["00 sem grade", "01 gr exclamação", "02 gr quarenta", "03 gr 100"])
        grades = list(map(lambda x: x.grade, unit_list))
        self.assertEqual(grades, [100, None, 40, 100])


class TestPatternLoader(unittest.TestCase):
    def test_make(self):
        pattern_loader = tk.PatternLoader("@.in", "@.sol")
        file_list = ["1.in", "02.in", "a.in", "x.sol", "1.sol", "02.sol", "a.sol"]
        matches_list = pattern_loader.get_file_sources(file_list)
        self.assertListEqual(matches_list, [tk.FileSource("1", "1.in", "1.sol"), tk.FileSource("02", "02.in", "02.sol"),
                                            tk.FileSource("a", "a.in", "a.sol")])

    def test_make_out(self):
        pattern_loader = tk.PatternLoader("@.in", "out.@")
        file_list = ["1.in", "02.in", "a.in", "x.sol", "out.1", "out.02", "out.a"]
        matches_list = pattern_loader.get_file_sources(file_list)
        self.assertListEqual(matches_list, [tk.FileSource("1", "1.in", "out.1"), tk.FileSource("02", "02.in", "out.02"),
                                            tk.FileSource("a", "a.in", "out.a")])

    def test_make_2(self):
        pattern_loader = tk.PatternLoader("in.@", "out.@")
        file_list = ["in.1", "in.02", "in.a", "x.sol", "out.1", "out.02", "out.a"]
        matches_list = pattern_loader.get_file_sources(file_list)
        self.assertListEqual(matches_list, [tk.FileSource("1", "in.1", "out.1"), tk.FileSource("02", "in.02", "out.02"),
                                            tk.FileSource("a", "in.a", "out.a")])

    def test_unmatched(self):
        pattern_loader = tk.PatternLoader("@.in", "out.@")
        file_list = ["1.in", "02.in", "a.in", "x.sol", "out.1", "out.02", "out.a"]
        matches_list = sorted(pattern_loader.get_odd_files(file_list))
        self.assertListEqual(matches_list, ["x.sol"])

    def test_wrong_pattern_duplicated_wildcard(self):
        with self.assertRaises(Exception):
            tk.PatternLoader("@.in@", "@.sol")

    def test_wrong_pattern_duplicated_wildcard_output(self):
        with self.assertRaises(Exception):
            tk.PatternLoader("@.in", "@.sol@")

    def test_wrong_pattern_missing_wildcard_output(self):
        with self.assertRaises(Exception):
            tk.PatternLoader("@.in", ".sol")

    def test_wrong_pattern_missing_wildcard_input(self):
        with self.assertRaises(Exception):
            tk.PatternLoader(".in", "@.sol")


class TestLoadDir(unittest.TestCase):
    def test_load_dir(self):
        unit_list = tk.Loader.parse_dir("data/03/tdir")
        self.assertEqual(4, len(unit_list))

    def test_load_dir2(self):
        unit_list = tk.Loader.parse_dir("data/03/tdir2")
        self.assertEqual(0, len(unit_list))

    def test_load_dir3(self):
        unit_list = tk.Loader.parse_dir("data/03/tdir2 in.@ @.out")
        self.assertEqual(4, len(unit_list))


class TestLabelFactory(unittest.TestCase):
    def test_trim(self):
        label = tk.LabelFactory().label("   primos   teste   1   ").generate()
        self.assertEqual(label, "primos teste 1")

    def test_remove_old_index(self):
        label = tk.LabelFactory().label(" 003  primos   teste   1   ").generate()
        self.assertEqual(label, "primos teste 1")

    def test_remove_first_old_index(self):
        label = tk.LabelFactory().label(" 003 01 primos   teste   1   ").generate()
        self.assertEqual(label, "01 primos teste 1")

    def test_put_new_index(self):
        label = tk.LabelFactory().label(" 003  primos   teste   1   ").index(4).generate()
        self.assertEqual(label, "04 primos teste 1")


class TestUpdateReadme(unittest.TestCase):

    def gen_test(self, manip: tk.Param.Manip, cmd: Optional[str], expected_path: str):
        temp_dir = tk.Util.copy_to_temp("data/readme_update")
        shutil.copy(temp_dir + os.sep + "source.md", temp_dir + os.sep + "Readme.md")
        readme_path = temp_dir + "/Readme.md"
        if cmd:
            cmd = temp_dir + os.sep + cmd
        tk.Actions.update([readme_path], manip, cmd)
        with open(temp_dir + os.sep + expected_path) as f:
            expected = f.read()
        with open(readme_path) as f:
            generated = f.read()
        self.assertEqual(expected, generated)

    def test_update_filter(self):
        self.gen_test(tk.Param.Manip(False, False, False), None, "filtered.md")

    def test_update_numbers(self):
        self.gen_test(tk.Param.Manip(False, False, True), None, "numbered.md")

    def test_update_remove_labels(self):
        self.gen_test(tk.Param.Manip(True, False, False), None, "unlabeled.md")

    def test_update_remove_labels_number(self):
        self.gen_test(tk.Param.Manip(True, False, True), None, "rm_label_number.md")

    def test_update_change_solver(self):
        self.gen_test(tk.Param.Manip(False, False, False), "solver_wrong.c", "change_solver.md")


class TestUpdateReadme2(unittest.TestCase):

    def gen_test(self, manip: tk.Param.Manip, cmd: Optional[str], expected_path: str):
        temp_dir = tk.Util.copy_to_temp("data/readme_update_2")
        shutil.copy(temp_dir + os.sep + "source.md", temp_dir + os.sep + "Readme.md")
        readme_path = temp_dir + "/Readme.md"
        if cmd:
            cmd = temp_dir + os.sep + cmd
        tk.Actions.update([readme_path], manip, cmd)
        with open(temp_dir + os.sep + expected_path) as f:
            expected = f.read()
        with open(readme_path) as f:
            generated = f.read()
        self.assertEqual(expected, generated)

    def test_update_sorted(self):
        self.gen_test(tk.Param.Manip(False, True, False), None, "sorted.md")


class TestActions(unittest.TestCase):
    def test_list_folders(self):
        tk.Logger.print_disable()
        output = tk.Actions.list(["data/00", "data/01"], tk.Param.Basic())
        self.assertEqual(output, [("data/00", 7), ("data/01", 4)])

    def test_list_file(self):
        tk.Logger.print_disable()
        output = tk.Actions.list(["data/00", "data/00/t.tio", "data/00/t.vpl"], tk.Param.Basic())
        self.assertEqual(output, [(".", 5), ("data/00", 7)])

    def test_execute_wrong(self):
        tk.Logger.print_disable()
        out = tk.Actions.execute(["data/00/t.tio", "data/00/solver_wrong.c"], tk.Param.Basic())
        self.assertEqual(out, [(".", 3, [("solver_wrong.c", 1)])])

    def test_execute_right(self):
        out = tk.Actions.execute(["data/00/t.tio", "data/00/solver_ok.c"], tk.Param.Basic())
        self.assertEqual(out, [('.', 3, [('solver_ok.c', 3)])])

    def test_execute_half_wrong(self):
        tk.Logger.print_disable()
        out = tk.Actions.execute(["data/half_right/t.tio", "data/half_right/solver_half.c"], tk.Param.Basic())
        self.assertEqual(out, [('.', 5, [('solver_half.c', 2)])])

    def test_execute_many(self):
        tk.Logger.print_disable()
        out = tk.Actions.execute(["data/00"], tk.Param.Basic())
        expected = [('data/00',  7, [('solver_comp.c', 0), ('solver_exec.py', 0), ('solver_ok.c', 7),
                                     ('solver_seg.out', 0), ('solver_wrong.c', 3)])]

        self.assertEqual(out, expected)


class TestWdir(unittest.TestCase):
    def test_load(self):
        wdir = tk.Wdir("data/00").sources(["data/00/t.tio"]).parse_sources()
        self.assertEqual(len(wdir.unit_list), 3)

    def test_load2(self):
        wdir = tk.Wdir("data/00").sources(["data/00/t.tio"]).parse_sources().filter(1)
        self.assertEqual(len(wdir.unit_list), 1)

    def test_load3(self):
        wdir = tk.Wdir("data/00").load_sources().parse_sources()
        self.assertEqual(len(wdir.unit_list), 7)

    def test_load4(self):
        wdir = tk.Wdir("data/00").load_sources().parse_sources().filter(1)
        self.assertEqual(len(wdir.unit_list), 1)


class TestBrief(unittest.TestCase):
    def test_list_brief(self):
        tk.Symbol.setAsc2Only(True)
        tk.Logger.store()
        param = tk.Param.Basic(None, True, False)
        tk.Actions.list(["data/00"], param)
        output = tk.Logger.recover()
        expected = "=>data/00 (03) [t.vpl(02), t.tio(03), t2.vpl(02)] " \
                   "[(.)solver_comp.c, (.)solver_exec.py, (.)solver_ok.c, "\
                   "(.)solver_seg.out, (.)solver_wrong.c] (.)\n"
        self.assertEqual(output, expected)


class TestCio(unittest.TestCase):
    def test_build_error(self):
        fdir = "data/teste_cio/"
        dest = fdir + "_t1.tio"
        source = [fdir + "missing.tio"]
        tk.Logger.store()
        created = tk.Actions.build(dest, source, tk.Param.Manip(), True)
        msg = tk.Logger.recover()
        file_created = os.path.isfile(dest)
        self.assertEqual(created, False)
        self.assertEqual(file_created, False)
        if file_created:
            os.remove(dest)
        expected = "    warning: unable to find: data/teste_cio/missing.tio\n" +\
                   "    failure: none source found\n"
        self.assertEqual(msg, expected)

    def test_build_error_2(self):
        fdir = "data/teste_cio/"
        dest = fdir + "_t1.tio"
        expected = fdir + "t1.tio"
        source = [fdir + "missing.tio", fdir + "R1.md"]
        tk.Logger.store()
        manip = tk.Param.Manip()
        created = tk.Actions.build(dest, source, manip, True)
        msg = tk.Logger.recover()
        expected_msg = "    warning: unable to find: data/teste_cio/missing.tio\n"
        self.assertEqual(msg, expected_msg)

        file_created = os.path.isfile(dest)
        with open(dest) as f:
            dest_content = f.read()
        with open(expected) as f:
            expected_content = f.read()
        self.assertEqual(created, True)
        self.assertEqual(file_created, True)
        self.assertEqual(dest_content, expected_content)
        if file_created:
            os.remove(dest)

    def test_build_from_cio_1(self):
        fdir = "data/teste_cio/"
        dest = fdir + "_t1.tio"
        source = [fdir + "R1.md"]
        expected = fdir + "t1.tio"
        tk.Actions.build(dest, source, tk.Param.Manip(), True)
        with open(dest) as f:
            dest_content = f.read()
        os.remove(dest)
        with open(expected) as f:
            expected_content = f.read()
        self.assertEqual(dest_content, expected_content)

    def test_build_from_cio_2(self):
        fdir = "data/teste_cio/"
        dest = fdir + "_t2.tio"
        source = [fdir + "R2.md"]
        expected = fdir + "t2.tio"
        tk.Actions.build(dest, source, tk.Param.Manip(), True)
        with open(dest) as f:
            dest_content = f.read()
        os.remove(dest)
        with open(expected) as f:
            expected_content = f.read()
        self.assertEqual(dest_content, expected_content)


class TestDiff(unittest.TestCase):
    def test_diff_c(self):
        tk.Report.set_terminal_size(100)
        tk.Logger.store()
        tk.Actions.execute(["data/teste_diff_1"], tk.Param.Basic())
        output = tk.Logger.recover()
        expected = (
            "=>data/teste_diff_1 (03) [t.tio(03)] [(W)solver_wrong.c] (X)\n"
            "    (W)=>data/teste_diff_1/solver_wrong.c WRONG_OUTPUT\n"
            "        (S)[00] GR:100 data/teste_diff_1/t.tio (teste 01)      \n"
            "        (X)[01] GR:100 data/teste_diff_1/t.tio (teste 02)      \n"
            "        (X)[02] GR:100 data/teste_diff_1/t.tio (teste 03)      \n"
            "                                      MODE: FIRST FAILURE ONLY                                     \n"
            " ───────────────────────────────────────────────   ─────────────────────────────────────────────── \n"
            " GR:100 data/teste_diff_1/t.tio (teste 02)       │ GR:100 data/teste_diff_1/t.tio (teste 02)       \n"
            " -------------------- INPUT -------------------- │ -------------------- INPUT -------------------- \n"
            " 0↵                                              │ 0↵                                              \n"
            " 5↵                                              │ 5↵                                              \n"
            " --------------- EXPECTED OUTPUT --------------- │ ----------------- USER OUTPUT ----------------- \n"
            " 5↵                                              │ 5↵                                              \n"
            " -5↵                                             ≠                                                 \n"
            " ───────────────────────────────────────────────   ─────────────────────────────────────────────── \n")
        self.assertEqual(output, expected)

    def test_diff_all_raw(self):
        tk.Symbol.setAsc2Only(True)
        tk.Report.set_terminal_size(100)
        tk.Logger.store()
        param = tk.Param.Basic(None, False, True)
        param.set_diff_mode(tk.Param.DiffMode.ALL)
        tk.Actions.execute(["data/teste_diff_1"], param)
        output = tk.Logger.recover()
        expected = (
            "=>data/teste_diff_1 (03) [t.tio(03)] [(W)solver_wrong.c] (X)\n"
            "    (W)=>data/teste_diff_1/solver_wrong.c WRONG_OUTPUT\n"
            "        (S)[00] GR:100 data/teste_diff_1/t.tio (teste 01)      \n"
            "        (X)[01] GR:100 data/teste_diff_1/t.tio (teste 02)      \n"
            "        (X)[02] GR:100 data/teste_diff_1/t.tio (teste 03)      \n"
            "                                         MODE: ALL FAILURES                                        \n"
            "───────────────────────────────────────────────────────────────────────────────────────────────────\n"
            "                          GR:100 data/teste_diff_1/t.tio (teste 02)                                \n"
            "-------------------------------------------PROGRAM INPUT-------------------------------------------\n"
            "0\n"
            "5\n"
            "------------------------------------------EXPECTED OUTPUT------------------------------------------\n"
            "5\n"
            "-5\n"
            "--------------------------------------------USER OUTPUT--------------------------------------------\n"
            "5\n"
            "───────────────────────────────────────────────────────────────────────────────────────────────────\n"
            "                          GR:100 data/teste_diff_1/t.tio (teste 03)                                \n"
            "-------------------------------------------PROGRAM INPUT-------------------------------------------\n"
            "0\n"
            "3\n"
            "------------------------------------------EXPECTED OUTPUT------------------------------------------\n"
            "3\n"
            "-3\n"
            "--------------------------------------------USER OUTPUT--------------------------------------------\n"
            "3\n"
            "───────────────────────────────────────────────────────────────────────────────────────────────────\n")
        self.assertEqual(output, expected)




if __name__ == '__main__':
    unittest.main()
