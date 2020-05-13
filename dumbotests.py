import unittest

from lark import Lark
from dumbo_interpreter import DumboInterpreter, Context

GRAMMAR = ""

def interpret(input):
        tree = Lark(GRAMMAR, start='programme', parser="lalr", propagate_positions=True).parse(input)
        return DumboInterpreter(Context()).visit(tree, display=True)

class Test(unittest.TestCase):
    def test_print_string(self):
        pgm = "{{print 'Hello World';}}"
        self.assertEqual("Hello World", interpret(pgm))

    def test_empty_block(self):
        pgm = "{{}}"
        self.assertEqual("", interpret(pgm))

    def test_assign(self):
        pgm = "{{int a := 1; print a;}}"
        self.assertEqual("1", interpret(pgm))

    def test_print_boolean_false(self):
        pgm = "{{int b := false; print! b;}}"
        self.assertEqual("false", interpret(pgm))

    def test_print_boolean_true(self):
        pgm = "{{int b := true; print! b;}}"
        self.assertEqual("true", interpret(pgm))

    def test_greater_than(self):
        pgm = "{{int b := 1 < 0; print! b;}}"
        self.assertEqual("false", interpret(pgm))

    def test_if_true(self):
        pgm = "{{str a := 'ok'; if 1 > 2 do str a := 'aie aie aie'; endif; print a;}}"
        self.assertEqual("ok", interpret(pgm))

    def test_if_false(self):
        pgm = "{{str a := 'ok'; if 1 < 2 do str a := 'aie aie aie'; endif; print a;}}"
        self.assertEqual("aie aie aie", interpret(pgm))

    def test_txt(self):
        pgm = "<html></html>"
        self.assertEqual("<html></html>", interpret(pgm))

    def test_txt_2(self):
        pgm = "<html>{{}}</html>"
        self.assertEqual("<html></html>", interpret(pgm))

    def test_for(self):
        pgm = "{{str label := 'realises par Tony Kaye'; list liste_label := ('American History X', 'Snowblind', " \
              "'Lake of Fire');}}<html><head><title>Films {{ print label; }}</\title><head><body><h1><b>Films " \
              "{{ print label; }}<b><h1>{{for str nom_film in liste_label do print nom_film; print '<br>'; endfor; " \
              "}}<body><html>"
        self.assertEqual("<html><head><title>Films realises par Tony Kaye</\title><head><body><h1><b>Films realis"
                         "es par Tony Kaye<b><h1>American History X<br>Snowblind<br>Lake of Fire<br><body"
                         "><html>", interpret(pgm))

if __name__ == "__main__":
    with open("dumbo.lark", "r") as grammar:
        GRAMMAR = grammar.read()

    unittest.main()