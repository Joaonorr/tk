#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import unittest
import tk
import os
from typing import Optional
from tk import PatternLoader as Pl
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
        self.assertEqual(solver.result, tk.Execution.Result.SUCCESS)
        self.assertEqual(3, len([unit for user, unit in zip(solver.user, unit_list) if user == unit.output]))

    def test_compilation_error(self):
        unit_list = tk.Loader.parse_source("data/00/t.tio")
        solver = tk.Solver("data/00/solver_comp.c")
        tk.Execution.execute_solver(solver, unit_list)
        self.assertEqual(solver.result, tk.Execution.Result.COMPILATION_ERROR)
        self.assertTrue("error: unused variable ‘c’" in solver.error_msg)
        self.assertTrue("cc1: all warnings being treated as errors" in solver.error_msg)

    def test_execution_error(self):
        unit_list = tk.Loader.parse_source("data/00/t.tio")
        solver = tk.Solver("data/00/solver_exec.py")
        tk.Execution.execute_solver(solver, unit_list)
        self.assertEqual(solver.result, tk.Execution.Result.EXECUTION_ERROR)
        error_msg = "45\n"
        self.assertEqual(solver.error_msg, error_msg)

    def test_wrong_error(self):
        unit_list = tk.Loader.parse_source("data/00/t.tio")
        self.assertEqual(len(unit_list), 3)
        solver = tk.Solver("data/00/solver_wrong.c")
        tk.Execution.execute_solver(solver, unit_list)
        self.assertEqual(solver.result, tk.Execution.Result.WRONG_OUTPUT)
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
        self.assertListEqual(matches_list, [Pl.FileSource("1", "1.in", "1.sol"), Pl.FileSource("02", "02.in", "02.sol"),
                                            Pl.FileSource("a", "a.in", "a.sol")])

    def test_make_out(self):
        pattern_loader = tk.PatternLoader("@.in", "out.@")
        file_list = ["1.in", "02.in", "a.in", "x.sol", "out.1", "out.02", "out.a"]
        matches_list = pattern_loader.get_file_sources(file_list)
        self.assertListEqual(matches_list, [Pl.FileSource("1", "1.in", "out.1"), Pl.FileSource("02", "02.in", "out.02"),
                                            Pl.FileSource("a", "a.in", "out.a")])

    def test_make_2(self):
        pattern_loader = tk.PatternLoader("in.@", "out.@")
        file_list = ["in.1", "in.02", "in.a", "x.sol", "out.1", "out.02", "out.a"]
        matches_list = pattern_loader.get_file_sources(file_list)
        self.assertListEqual(matches_list, [Pl.FileSource("1", "in.1", "out.1"), Pl.FileSource("02", "in.02", "out.02"),
                                            Pl.FileSource("a", "in.a", "out.a")])

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


class TestHS(unittest.TestCase):
    def setUp(self):
        self.data = """
```
a == b
```
a == b
```hs
--IN : Lista xs e um natural n
--OUT: N-ésimo termo de xs
outro lixo qualquer sem igual igual
elemento 2 [2,7,3,9] banana == 3
case 0 4.4 [1,2,3] 5 [2,7,3,9] == [1,3,4,5,6]
case 1 [1,2,3] 5 [2,7,3,9] == 1 [1,3,4,5,6]
```
```hs
soma 2.4 [2.4,7.3,3.1,9.9] 7banana == 3
```

"""

    def test_load(self):
        tests = tk.HSMod.HFile.load_from_text(self.data)
        self.assertEqual(tests[0], tk.HSMod.Case("elemento", "2\n[2,7,3,9]\nbanana\n", "3\n"))
        self.assertEqual(tests[1], tk.HSMod.Case("case", "0\n4.4\n[1,2,3]\n5\n[2,7,3,9]\n", "[1,3,4,5,6]\n"))
        self.assertEqual(tests[2], tk.HSMod.Case("case", "1\n[1,2,3]\n5\n[2,7,3,9]\n", "1 [1,3,4,5,6]\n"))
        self.assertEqual(tests[3], tk.HSMod.Case("soma", "2.4\n[2.4,7.3,3.1,9.9]\n7banana\n", "3\n"))


class Test2HS(unittest.TestCase):

    def test_hmain_0(self):
        main_gen = tk.HSMod.HMain.format_main(tk.HSMod.Case("elemento", "2\n[2,7,3,9]\nbanana\n", "3\n"))
        main_str = """main = do
    a <- readLn :: IO Int
    b <- readLn :: IO [Int]
    c <- getLine
    print $ elemento a b c
"""
        self.assertEqual(main_gen, main_str)


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
        tk.Logger.store()
        param = tk.Param.Basic(None, True, False)
        tk.Actions.list(["data/00"], param)
        output = tk.Logger.recover()
        expected = "=>data/00 (03) [t.vpl(02), t.tio(03), t2.vpl(02)] " \
                   "[(»)solver_comp.c, (»)solver_exec.py, (»)solver_ok.c, "\
                   "(»)solver_seg.out, (»)solver_wrong.c] (»)\n"
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
            "=>data/teste_diff_1 (03) [t.tio(03)] [(ω)solver_wrong.c] (✗)\n"
            "    (ω)=>data/teste_diff_1/solver_wrong.c WRONG_OUTPUT\n"
            "        (✓)[00] GR:100 data/teste_diff_1/t.tio (teste 01)      \n"
            "        (✗)[01] GR:100 data/teste_diff_1/t.tio (teste 02)      \n"
            "        (✗)[02] GR:100 data/teste_diff_1/t.tio (teste 03)      \n"
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
        tk.Report.set_terminal_size(100)
        tk.Logger.store()
        param = tk.Param.Basic(None, False, True)
        param.set_diff_mode(tk.Param.DiffMode.ALL)
        tk.Actions.execute(["data/teste_diff_1"], param)
        output = tk.Logger.recover()
        expected = (
            "=>data/teste_diff_1 (03) [t.tio(03)] [(ω)solver_wrong.c] (✗)\n"
            "    (ω)=>data/teste_diff_1/solver_wrong.c WRONG_OUTPUT\n"
            "        (✓)[00] GR:100 data/teste_diff_1/t.tio (teste 01)      \n"
            "        (✗)[01] GR:100 data/teste_diff_1/t.tio (teste 02)      \n"
            "        (✗)[02] GR:100 data/teste_diff_1/t.tio (teste 03)      \n"
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

    def test_diff_hs(self):
        tk.Report.set_terminal_size(100)
        tk.Logger.store()
        tk.Actions.execute(["data/teste_diff_2"], tk.Param.Basic())
        output = tk.Logger.recover()
        expected = (
            "=>data/teste_diff_2 (03) [Readme.md(03)] [(ω)solver.hs] (✗)\n"
            "    (ω)=>data/teste_diff_2/solver.hs WRONG_OUTPUT\n"
            "        (✓)[00] GR:100 data/teste_diff_2/Readme.md ()      \n"
            "        (✓)[01] GR:100 data/teste_diff_2/Readme.md ()      \n"
            "        (✗)[02] GR:100 data/teste_diff_2/Readme.md ()      \n"
            "                                      MODE: FIRST FAILURE ONLY                                     \n"
            " ───────────────────────────────────────────────   ─────────────────────────────────────────────── \n"
            "   GR:100 data/teste_diff_2/Readme.md ()         │   GR:100 data/teste_diff_2/Readme.md ()         \n"
            " -------------------- INPUT -------------------- │ -------------------- INPUT -------------------- \n"
            " 1↵                                              │ 1↵                                              \n"
            " -1↵                                             │ -1↵                                             \n"
            " --------------- EXPECTED OUTPUT --------------- │ ----------------- USER OUTPUT ----------------- \n"
            " -2↵                                             ≠ 0↵                                              \n"
            " ───────────────────────────────────────────────   ─────────────────────────────────────────────── \n")
        self.assertEqual(output, expected)


if __name__ == '__main__':
    unittest.main()
