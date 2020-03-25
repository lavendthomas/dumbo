from lark import Lark, tree

grammar = r'''
    programme: txt | txt programme | dumbo_bloc | dumbo_bloc programme
    txt: /[a-zA-Z0-9 _;&<>"-.:,]+/
    dumbo_bloc: "{{" expressions_list "}}"
    expressions_list: ( expression ";" expressions_list ) 
                    | ( expression ";" )
    expression: "print" string_expression
              | "for" VARIABLE "in" string_list "do" expressions_list "endfor"
              | "for" VARIABLE "in" VARIABLE "do" expressions_list "endfor"
              | VARIABLE ":=" string_expression
              | VARIABLE ":=" string_list
    string_expression: STRING 
                     | VARIABLE
                     | string_expression "." string_expression
    string_list: "(" string_list_interior ")"
    string_list_interior: STRING | STRING "," string_list_interior
    
    VARIABLE: /[a-zA-Z0-9_]+/
    STRING  : /'[a-zA-Z0-9 _;&<>"-.:,]+'/
    
    %import common.NUMBER
    %import common.WORD
    
    %ignore /[ \n]/
'''

# TODO ajouter \n\p `a STRING et TXT

l: Lark = Lark(grammar, start='programme')

text = """
{{
label := 'realises par Tony Kaye';
label_list := ('American History X', 'Snowblind', 'Lake of Fire');
}}
"""

tree = l.parse(text, start="programme")

print(tree)



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


def txt(node: tree):
    print(node.content) # TODO


def programme(head: tree):
    if head.data != "programme":
        raise ValueError("Not a program!")

    for child in head.children:
        if child.data == "txt":
            try:
                txt(child)
            except ValueError:
                continue
