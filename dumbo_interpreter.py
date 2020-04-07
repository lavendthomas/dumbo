import os
import sys
from typing import Union

from lark import Lark, tree, Transformer
from lark.lexer import Token

from functools import reduce




# TODO ajouter \n\p `a STRING et TXT


class Variable:

    def __init__(self, type, name):
        self._type = type
        self._name = name

    def get(self):
        return self._name

    def type(self):
        return self._type

    def __hash__(self):
        return self._name.__hash__()

    def __eq__(self, other):
        if isinstance(other, str):
            return other == self._name
        if isinstance(other, Variable):
            return self._name == other._name and self._type == other._type
        return False

    def __str__(self):
        return "{"+ self._type + " " + self._name + "}"

    def __repr__(self):
        return str(self)

class Context:

    _local: dict
    # _name: Context

    def __init__(self):
        self._local = dict()    # str -> (type, value)
        self._next = None

    def add(self, key: Variable, value: Union[str, int, bool, list]):
        self._local[key.get()] = (key.type(), value)

    def typeof(self, name: str) -> str:
        if name in self._local:
            return self._local[name][0]

        if self._next is not None:
            return self._next.typeof(name)
        return False

    def update(self, key: Variable, new_value: Union[str, int, bool, list]):
        val = self._local[key.get()][1]

        if val is None:
            if self._next is None:
                return False
            else:
                self._next.update(key, new_value)
                return True

        self._local[key.get()] = (key.type(), new_value)
        return True

    def get(self, key: Union[Variable, str]) -> Union[str, int, bool, list]:
        if isinstance(key, Variable):
            val = self._local[key.get()]
        elif isinstance(key, str):
            val = self._local[key]

        if val is None:
            if self._next is None:
                return None
            else:
                return self._next.get(key)
        return val

    def pop_scope(self):
        return self._next

    def push_scope(self):
        new = Context()
        new._next = self
        return new



class Interpreter(Transformer):

    variables: Context

    def __init__(self, visit_tokens):
        super().__init__(visit_tokens=visit_tokens)
        self.variables = Context()

    def txt(self, text_token) -> str:
        print(text_token[0])
        return text_token[0]    # put the text on the tree

    def dumbo_bloc(self, args):
        self.variables = self.variables.push_scope()
        return args

    def string(self, string) -> str:
        val = string[0].value
        return val[1:len(val)-1]        # remove surrounding quotes

    def variable_get(self, variable) -> Union[int, Variable]:
        variable_name = variable[0].value
        if variable_name == "true":
            return 1
        if variable_name == "false":
            return 0
        return self.variables.get(variable_name)

    def variable_get_str(self, variable) -> Variable:
        return self.variable_get(variable)


    def variable_set(self, variable) -> Variable:
        """
        :return: the name of the variable
        """
        type = variable[0].value
        value = variable[1].value
        return Variable(type, value)

    def string_expression(self, arg) -> str:
        token = arg[0]
        if isinstance(token, str):    # if concat or string
            return token
        if isinstance(token, int):    # if an arithmetic expression or a test
            return str(token)
        if isinstance(token, list):   # if a list variable is used as a parameter
            return str(token)
        if token.type == "VARIABLE":
            return self.variables.get(token)         # TODO Afficher un message d'erreur si variable inconnue
        else:
            raise ValueError("Unknown string")

    def string_concat(self, args) -> str:
        return reduce(lambda a, b: a + b, args, "")

    def expression_print(self, args):
        # print can use any type as a parameter, so no checks are necessary
        print(args[0])
        return None

    def expression_print_b(self, args):
        """
        Prints the argument on the screen but treats integers as booleans
        :param args:
        :return:
        """
        if isinstance(args[0], int):
            print(args[0] == 0)    # print bool : 0 => False; 1/Other => True
        return self.expression_print()

    def expression_for_0(self, args):
        print(args)
        return args

    def expression_assign(self, args):
        key = args[0]
        value = args[1]

        # Assignment checks
        if key.type() == "int":
            if not isinstance(value, int):
                raise ValueError("Variable '" + key.get() + "' expexted an int, got a " + str(type(value)))
        if key.type() == "str":
            if not isinstance(value, str):
                raise ValueError("Variable '" + key.get() + "' expexted a str, got a " + str(type(value)))
        if key.type() == "list":
            if not isinstance(value, list):
                raise ValueError("Variable '" + key.get() + "' expexted a list, got a " + str(type(value)))
        if key.type() == "bool":
            if not isinstance(value, int):
                raise ValueError("Variable '" + key.get() + "' expexted an int, got a " + str(type(value)))

        # Add to variables
        self.variables.add(key, value)
        return None

    def string_list(self, args):
        return args[0]

    def string_list_interior(self, args):
        if len(args) == 1:
            # end of the list
            return [args[0]]
        elif len(args) == 2:
            return [args[0]] + args[1]

    def integer(self, args) -> int:
        try:
            val = int(args[0].value)
        except ValueError:
            raise ValueError("Could not convert " + val + "to <class 'int'>")
        return val    # return the value stored in the leaf

    def factor(self, args):
        if not isinstance(args[0], int):        # TODO and for variables ?
            raise ValueError("Expected an <class 'int'> variable, got a " + str(type(args[0])) + ".")
        return args[0]

    def term(self, args) -> int:
        product = 1
        op = lambda a, b: a*b
        for i, elem in enumerate(args):
            if i % 2 == 0:
                try:
                    product = op(product, elem)
                except ZeroDivisionError:
                    raise ZeroDivisionError
            else:
                if elem == "*":
                    op = lambda a, b: a*b
                elif elem == "/":
                    op = lambda a, b: int(a/b)  # TODO  round ?
        return product

    def arithm_expr(self, args) -> int:
        sum_ = 0
        op = lambda a, b: a + b
        for i, elem in enumerate(args):
            if i % 2 == 0:
                sum_ = op(sum_, elem)
            else:
                if elem == "+":
                    op = lambda a, b: a + b
                elif elem == "-":
                    op = lambda a, b: a - b
        return sum_

    def comparison(self, args) -> int:
        if len(args) == 1:
            return args[0]      # args is an integer
        result = True
        last = None
        op = lambda a, b: a != b
        for i, elem in enumerate(args):
            if i % 2 == 0:
                result = result and op(last, elem)
                last = elem
                if not result:      # lasy evaluation
                    break
            else:
                if elem == "=":
                    op = lambda a, b: a == b
                elif elem == ">":
                    op = lambda a, b: a > b
                elif elem == ">=":
                    op = lambda a, b: a >= b
                elif elem == "<":
                    op = lambda a, b: a < b
                elif elem == "<=":
                    op = lambda a, b: a <= b
                elif elem == "!=":
                    op = lambda a, b: a != b
        return int(result)

    def not_test(self, args) -> int:
        return args[0]

    def invert_test(self, args) -> int:
        return int(not(args[0]))

    def and_test(self, args) -> int:
        return reduce(lambda a, b: a and b, args[1:], args[0])

    def test(self, args) -> int:
        return reduce(lambda a, b: a or b, args[1:], args[0])




if __name__ == '__main__':

    grammar = open("dumbo.lark", "r")

    text = grammar.read()


    interpreter: Lark = Lark(text,
                             parser='lalr',
                             start='programme',
                             transformer=Interpreter(visit_tokens=True))

    for file in sys.argv[1:]:
        with open(file, "r") as f:
            if False:
                tree = Lark(text, start='programme', parser="lalr").parse(f.read())
                print(tree)
                print(tree.pretty())
            else:
                tree = interpreter.parse(f.read())
                # programme(variables, tree)
                print(tree)
