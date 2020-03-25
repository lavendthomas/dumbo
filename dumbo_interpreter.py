import os
import sys
from typing import Union

from lark import Lark, tree
from lark.lexer import Token




# TODO ajouter \n\p `a STRING et TXT





class Context:

    local: dict
    # name: Context

    def __init__(self):
        self.local = dict()
        self.next = None

    def add(self, variable: tuple):
        self.local[variable[0]] = variable[1]

    def update(self, variable: tuple):
        val = self.local[variable[0]]

        if val is None:
            if self.next is None:
                return False
            else:
                self.next.update(variable)
                return True

        self.local[variable[0]] = variable[1]
        return True

    def get(self, name: str):
        val = self.local[name]

        if val is None:
            if self.next is None:
                return None
            else:
                return self.next.get(name)
        return val

    def pop_scope(self):
        return self.next

    def push_scope(self):
        new = Context()
        new.next = self
        return new


def txt(context: Context, head: tree):
    if head.data != "programme":
        raise ValueError("Not a program!")

    print(head)


def string_expression_to_str(string_expression: tree) -> str:
    if string_expression.data != "string_expression":
        raise ValueError("Not a string_expression!")

    # TODO additional checks

    return string_expression.children[0].value


def string_list_interior(interior: tree) -> list:
    if interior.data != "string_list_interior":
        raise ValueError("Not a string_list_interior!")
    res = list()
    for child in interior.children:
        if isinstance(child.__class__, Token.__class__):
            if child.type == "STRING":
                res.append(child.value)
            else:
                raise ValueError("Expected a STRING.")
        else:
            res.extend(string_list_interior(child))
    return res


def string_list_to_list(string_list: tree) -> list:
    if string_list.data != "string_list":
        raise ValueError("Not a string_list!")

    return string_list_interior(string_list.children[0])

def print_string_expression(context: Context, head: tree):
    key: str = head.children[0].value
    print(context.get(key))


def expression_print(context: Context, head: tree):
    if head.data != "expression_print":
        raise ValueError("Not a expression_print!")

    # We can assume only string_expression can be printed
    print_string_expression(context, head.children[0])


def expression_for_0(context: Context, head: tree):
    pass


def expression_for_1(context: Context, head: tree):
    pass


def expression_assign(context: Context, head:tree):
    key: str = head.children[0].value
    val: Union[str, list] = ""

    if head.children[1].data == "string_expression":
        val = string_expression_to_str(head.children[1])
    elif head.children[1].data == "string_list":
        val = string_list_to_list(head.children[1])

    context.add((key, val))


def expression(context: Context, head: tree):
    if head.data != "expression":
        raise ValueError("Not an expressions_list!")

    if head.children[0].data == "expression_print":
        expression_print(context, head.children[0])
    elif head.children[0].data == "expression_for_0":
        expression_for_0(context, ...)
    elif head.children[0].data == "expression_for_1":
        expression_for_1(context, ...)
    elif head.children[0].data == "expression_assign":
        expression_assign(context, head.children[0])


def expressions_list(context: Context, head: tree):
    if head.data != "expressions_list":
        raise ValueError("Not an expressions_list!")

    for child in head.children:
        if child.data == "expression":
            expression(context, child)
        if child.data == "expressions_list":
            expressions_list(context, child)

def dumbo_block(context:Context, head: tree):
    if head.data != "dumbo_bloc":
        raise ValueError("Not a dumbo_bloc!")

    new_scope = context.push_scope()

    expressions_list(new_scope, head.children[0]) # Only an expression_list can be present


def programme(context: Context, head: tree):
    if head.data != "programme":
        raise ValueError("Not a program!")

    for child in head.children:
        if child.data == "txt":
            txt(context, child)
        if child.data == "dumbo_bloc":
            dumbo_block(context, child)
        if child.data == "programme":
            programme(context, child)


if __name__ == '__main__':

    grammar = open("dumbo.lark", "r")

    l: Lark = Lark(grammar.read(), start='programme')

    variables = Context()

    for file in sys.argv[1:]:
        with open(file, "r") as f:
            tree = l.parse(f.read(), start="programme")
            programme(variables, tree)