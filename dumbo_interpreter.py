from lark import Lark

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

l: Lark = Lark(grammar, start='programme')

text = """
{{
label := 'realises par Tony Kaye';
label_list := ('American History X', 'Snowblind', 'Lake of Fire');
}}
"""

tree = l.parse(text, start="programme")

print(tree)
