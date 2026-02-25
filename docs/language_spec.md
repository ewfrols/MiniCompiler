```ebnf
letter           = "A" | ... | "Z" | "a" | ... | "z" ;
digit            = "0" | ... | "9" ;
underscore       = "_" ;

identifier       = letter (letter | digit | underscore)* ;

integer_literal  = digit+ ;
float_literal    = digit+ "." digit+ ;
string_literal   = '"' (character - '"')* '"' ;

keyword          = "if" | "else" | "while" | "for" | "int" | "float"
                 | "bool" | "return" | "true" | "false" | "void"
                 | "struct" | "fn" ;

operator         = "+" | "-" | "*" | "/" | "%" | "==" | "!=" | "<" | "<="
                 | ">" | ">=" | "&&" | "||" | "!" | "=" | "+=" | "-="
                 | "*=" | "/=" ;

delimiter        = "(" | ")" | "{" | "}" | "[" | "]" | ";" | "," | ":" ;

whitespace       = " " | "\t" | "\n" | "\r" ;
comment          = "//" (character - newline)* newline
                 | "/*" (character - "*/")* "*/" ;