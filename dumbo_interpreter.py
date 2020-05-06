import operator
import sys
from typing import Union

from lark import Lark
from lark import tree as Tree
from lark.visitors import Interpreter

from functools import reduce


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
        if not self.update(key, value):
            self._local[key.get()] = (key.type(), value)

    def typeof(self, name: str) -> str:
        if name in self._local:
            return self._local[name][0]

        if self._next is not None:
            return self._next.typeof(name)
        return False

    def update(self, key: Variable, new_value: Union[str, int, bool, list]):
        """
        Updates a value in the context, if it exists
        :return: True if the value was changed (if it already existed in the context)
        """
        # Find and replace
        if isinstance(key, Variable):
            val = self._local.get(key.get())
        elif isinstance(key, str):
            val = self._local.get(key)

        if val is None:
            if self._next is None:
                return False
            else:
                return self._next.update(key, new_value)
        else:
            self._local[key.get()] = (key.type(), new_value)
            return True

    def get(self, key: Union[Variable, str]) -> Union[str, int, bool, list]:
        if isinstance(key, Variable):
            val = self._local.get(key.get())
        elif isinstance(key, str):
            val = self._local.get(key)

        if val is None:
            if self._next is None:
                return None
            else:
                return self._next.get(key)
        return val[1]

    def pop_scope(self):
        return self._next

    def push_scope(self):
        new = Context()
        new._next = self
        return new

    def merge(self, other):
        """
        Shallow copy of the variable of other into self
        :param other:
        :return:
        """
        self._local.update(other._local)

class DumboInterpreter(Interpreter):

    variables: Context
    _print_buffer: str = ""
    _has_error = False

    OPERATORS = {
        '+' : operator.add,
        '-' : operator.sub,
        '*' : operator.mul,
        '/' : operator.floordiv,
        '<' : operator.lt,
        '<=': operator.le,
        '>' : operator.gt,
        '>=': operator.ge,
        '!=': operator.ne,
        '=' : operator.eq,
    }

    def visit(self, tree, display=False):
        res = super(DumboInterpreter, self).visit(tree)
        if display and not self._has_error:
            print(self._print_buffer)
        return res

    def __init__(self, context: Context):
        super().__init__()
        self.variables = context


    def programme(self, tree: Tree):
        self.visit_children(tree)

    def txt(self, tree: Tree):
        self._print_buffer += tree.children[0].value

    def dumbo_block(self, tree: Tree):
        # Create a new variable scope for the dumbo_block
        self.variables = self.variables.push_scope()

        self.visit_children(tree)

        # Merge the local variables into the global variables
        locals = self.variables
        self.variables = self.variables.pop_scope()
        self.variables.merge(locals)


    def expressions_list(self, tree: Tree):
        self.visit_children(tree)

    def string(self, tree: Tree) -> str:
        val = tree.children[0].value
        return val[1:len(val)-1]        # remove surrounding quotes

    def variable_get(self, tree: Tree) -> Union[int, Variable]:
        variables = self.visit_children(tree)
        variable_name = variables[0].value
        if variable_name == "true":
            return 1
        if variable_name == "false":
            return 0
        return self.variables.get(variable_name)

    def variable_get_str(self, tree: Tree) -> Variable:
        return self.variable_get(tree)


    def variable_set(self, tree: Tree) -> Variable:
        """
        :return: the name of the variable
        """
        type = tree.children[0].value
        value = tree.children[1].value
        return Variable(type, value)

    def string_expression(self, tree: Tree) -> str:
        token = self.visit_children(tree)[0]
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

    def string_concat(self, tree: Tree) -> str:
        strings = self.visit_children(tree)
        return reduce(lambda a, b: a + b, strings, "")

    def expression_print(self, tree: Tree):
        # print can use any type as a parameter, so no checks are necessary
        to_print = self.visit_children(tree)
        self._print_buffer +=  to_print[0]

    def expression_print_b(self, tree: Tree):
        """
        Prints the argument on the screen but treats integers as booleans
        :param args:
        :return:
        """
        to_print = self.visit_children(tree)
        if isinstance(to_print[0], int):
            self._print_buffer += to_print[0] == 0    # print bool : 0 => False; 1/Other => True
        return self.expression_print(tree)

    def expression_for_0(self, tree: Tree):
        variable_set, string_list, expressions_list = tree.children
        loop_variable: Variable = self.visit(variable_set)

        if loop_variable.type() != "str":
            raise ValueError(loop_variable.get() + " must be a str.")

        loop_content: list = self.visit(string_list)

        for item_in_list in loop_content:
            # Init
            self.variables = self.variables.push_scope()
            self.variables.add(loop_variable, item_in_list)

            # Execute nested block
            self.visit(expressions_list)

            # Delete local variables
            self.variables = self.variables.pop_scope()

    def expression_for_1(self, tree: Tree):
        self.expression_for_0(tree)


    def expression_if(self, tree: Tree):
        test, expressions_list = tree.children

        boolean = self.visit(test)

        if boolean:
            # Add a new scope
            self.variables = self.variables.push_scope()

            # Execute block
            self.visit(expressions_list)

            # Remove local variables
            self.variables = self.variables.pop_scope()

    def expression_assign(self, tree: Tree):
        key, value = self.visit_children(tree)

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

    def string_list(self, tree: Tree) -> list:
        return self.visit_children(tree)[0]    # a string list can only have one string_list_interior

    def string_list_interior(self, tree: Tree) -> list:
        if len(tree.children) == 1:
            # end of the list
            return self.visit_children(tree)
        elif len(tree.children) == 2:
            return [self.visit(tree.children[0])] + self.visit(tree.children[1])

    def integer(self, tree: Tree) -> int:
        terms = self.visit_children(tree)
        try:
            val = int(terms[0].value)
        except ValueError:
            raise ValueError("Could not convert " + val + "to <class 'int'>")
        return val    # return the value stored in the leaf

    def factor(self, tree: Tree):
        terms = self.visit_children(tree)
        if not isinstance(terms[0], int):
            raise ValueError("Expected an <class 'int'> variable, got a " + str(type(terms[0])) + ".")
        return terms[0]

    def term(self, tree: Tree) -> int:
        product = 1
        op = self.OPERATORS["*"]
        for i, elem in enumerate(self.visit_children(tree)):
            if i % 2 == 0:
                try:
                    product = op(product, elem)
                except ZeroDivisionError:
                    raise ZeroDivisionError
            else:
                try:
                    op = self.OPERATORS[elem]
                except KeyError:
                    raise ValueError("Could not find operation for '" + elem + "', excpected * or /")
        return product

    def arithm_expr(self, tree: Tree) -> int:
        sum_ = 0
        op = self.OPERATORS["+"]
        for i, elem in enumerate(self.visit_children(tree)):
            if i % 2 == 0:
                sum_ = op(sum_, elem)
            else:
                try:
                    op = self.OPERATORS[elem]
                except KeyError:
                    raise ValueError("Could not find operation for '" + elem + "', excpected + or -")
        return sum_

    def comparison(self, tree: Tree) -> int:
        if len(tree.children) == 1:
            return self.visit_children(tree)[0]      # is an integer\
        result = True
        last = None
        op = self.OPERATORS['!=']
        for i, elem in enumerate(self.visit_children(tree)):
            if i % 2 == 0:
                result = result and op(last, elem)
                last = elem
                if not result:      # lazy evaluation
                    break
            else:
                try:
                    op = self.OPERATORS[elem]
                except KeyError:
                    raise ValueError("Could not find operation for '" + elem + "'")
        return int(result)

    def not_test(self, tree: Tree) -> int:
        term = self.visit_children(tree)
        return term[0]

    def invert_test(self, tree: Tree) -> int:
        term = self.visit_children(tree)
        return int(not(term[0]))

    def and_test(self, tree: Tree) -> int:
        terms = self.visit_children(tree)
        return reduce(operator.and_, terms[1:], terms[0])

    def test(self, tree: Tree) -> int:
        terms = self.visit_children(tree)
        return reduce(operator.or_, terms[1:], terms[0])


if __name__ == '__main__':

    grammar = open("dumbo.lark", "r")

    text = grammar.read()

    variables = Context()

    for file in sys.argv[1:]:
        with open(file, "r") as f:
            interpreter = DumboInterpreter(variables)
            tree = Lark(text, start='programme', parser="lalr").parse(f.read())
            try:
                interpreter.visit(tree, display=True)
            except Exception as e:
                raise e
                print(e, file=sys.stderr)
