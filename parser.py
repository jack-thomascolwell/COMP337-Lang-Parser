import parser
import types
from parse import Parse
from sexp import sexp

class Parser:
    FAIL = Parse('',-1)
    KEYWORDS = ['print', 'var', 'if', 'else', 'while', 'func', 'ret', 'class', 'int', 'bool', 'string']

    def __init__(self):
        self._cache = dict()
        self._string = None

    def parse(self, string, term):
        parsed = self._parse(string, term, 0)
        if parsed == Parser.FAIL:
            return None
        if parsed.index < len(string) - 1:
            return None
        parsed = sexp(str(parsed))
        return parsed

    def _parse(self, string, term, index):
        if (self._string != string):
            self._cache = dict()
        if ((term, index) in self._cache):
            return self._cache[(term, index)]
        nonterminal = getattr(self, '_parse_%s'%term, None)
        if (not callable(nonterminal)):
            raise AssertionError('Unexpected term %s'%term)
        result = nonterminal(string, index)
        self._cache[(term,index)] = result
        return result

    def _zero_or_more(self, string, index, term):
        parsed = []
        result = self._parse(string, term, index)
        while (result != Parser.FAIL):
            index = result.index
            parsed.append(result)
            result = self._parse(string, term, index)
        return parsed

    def _one_or_more(self, string, index, term):
        first = self._parse(string, term, index)
        if (first == Parser.FAIL):
            return Parser.FAIL
        index = first.index
        rest = self._zero_or_more(string, index, term)
        return [first, *rest]

    def _zero_or_one(self, string, index, term):
        parse = self._parse(string, term, index)
        if (parse == Parser.FAIL):
            return []
        return [parse]

    def _choose(self, string, index, *terms):
        for term in terms:
            result = self._parse(string, term, index)
            if (result != Parser.FAIL):
                return result
        return Parser.FAIL

    def _choose_chars(self, string, index, *terms):
        for term in terms:
            result = self._string_term(string, index, term)
            if (result != Parser.FAIL):
                result.type = term
                return result
        return Parser.FAIL

    def _character(self, string, index, character):
        if (index >= len(string)):
            return Parser.FAIL
        if (string[index] != character):
            return Parser.FAIL
        return Parse('character',index + 1)

    def _string_term(self, string, index, word):
        if (index >= len(string)):
            return Parser.FAIL
        i = index
        for char in word:
            if string[i] != char:
                return Parser.FAIL
            i += 1
        index = i
        return Parse('string', index)

    def _parse_program(self, string, index):
        leading_space = self._parse(string, 'opt_space', index)
        index = leading_space.index
        program = self._zero_or_more(string, index, 'program_tail')
        if len(program) != 0:
            index = program[len(program)-1].index
        else:
            return Parse('sequence', index)
        trailing_space = self._parse(string, 'opt_space', index)
        index = trailing_space.index
        parse = Parse('sequence', index)
        parse.children = program
        return parse

    def _parse_program_tail(self, string, index):
        statement = self._parse(string, 'statement', index)
        if statement == Parser.FAIL:
            return Parser.FAIL
        index = statement.index
        space = self._parse(string, 'opt_space', index)
        index = space.index
        return Parse('program tail', index, statement)

    def _parse_statement(self, string, index):
        return self._choose(string, index, 'declaration_statement', 'assignment_statement', 'print_statement', 'ifelse_statement', 'if_statement', 'while_statement', 'return_statement', 'expression_statement')

    def _parse_print_statement(self, string, index):
        p = self._string_term(string, index, 'print')
        if p == Parser.FAIL:
            return Parser.FAIL
        index = p.index
        space = self._parse(string, 'req_space', index)
        if space == Parser.FAIL:
            return Parser.FAIL
        index = space.index
        expression = self._parse(string, 'expression', index)
        if expression == Parser.FAIL:
            return Parser.FAIL
        index = expression.index
        opt_space = self._parse(string, 'opt_space', index)
        index = opt_space.index
        semicolon = self._character(string, index, ';')
        if semicolon == Parser.FAIL:
            return Parser.FAIL
        index = semicolon.index

        return Parse('print', index, expression)

    def _parse_expression_statement(self, string, index):
        startingIndex = index
        exp = self._parse(string, 'expression', index)
        if exp == Parser.FAIL:
            return Parser.FAIL
        index = exp.index

        space = self._parse(string, 'opt_space', index)
        index = space.index

        semicolon = self._character(string, index, ';')
        if semicolon == Parser.FAIL:
            return Parser.FAIL
        exp.index = semicolon.index
        return exp

    def _parse_return_statement(self, string, index):
        ret = self._string_term(string, index, 'ret')
        if ret == Parser.FAIL:
            return Parser.FAIL
        index = ret.index
        space1 = self._parse(string, 'req_space', index)
        if space1 == Parser.FAIL:
            return Parser.FAIL
        index = space1.index
        exp = self._parse(string, 'expression', index)
        if exp == Parser.FAIL:
            return Parser.FAIL
        index = exp.index
        space2 = self._parse(string, 'opt_space', index)
        index = space2.index
        semicolon = self._character(string, index, ';')
        if semicolon == Parser.FAIL:
            return Parser.FAIL
        index += 1
        return Parse('return', index, exp)


    def _parse_expression(self, string, index):
        return self._parse(string, 'or_expression', index)

    def _parse_or_expression(self, string, index):
        and_exp = self._parse(string, 'and_expression', index)
        if and_exp == Parser.FAIL:
            return Parser.FAIL
        index = and_exp.index

        or_tails = self._zero_or_more(string, index, 'or_tail')
        parsed = and_exp
        for tail in or_tails:
            index = tail.index
            parsed = Parse(tail.children[0], index, parsed, tail.children[1])

        return parsed

    def _parse_or_tail(self, string, index):
        operator = self._parse(string, 'or_operator', index)
        if operator == Parser.FAIL:
            return Parser.FAIL
        index = operator.index

        exp = self._parse(string, 'and_expression', index)
        if exp == Parser.FAIL:
            return Parser.FAIL
        index = exp.index

        return Parse('or tail', index, '||', exp)

    def _parse_and_expression(self, string, index):
        opt_not = self._parse(string, 'opt_not_expression', index)
        if opt_not == Parser.FAIL:
            return Parser.FAIL
        index = opt_not.index

        and_tails = self._zero_or_more(string, index, 'and_tail')
        parsed = opt_not
        for tail in and_tails:
            index = tail.index
            parsed = Parse(tail.children[0], index, parsed, tail.children[1])

        return parsed


    def _parse_and_tail(self, string, index):
        operator = self._parse(string, 'and_operator', index)
        if operator == Parser.FAIL:
            return Parser.FAIL
        index = operator.index

        exp = self._parse(string, 'opt_not_expression', index)
        if exp == Parser.FAIL:
            return Parser.FAIL
        index = exp.index

        return Parse('and tail', index, '&&', exp)

    def _parse_opt_not_expression(self, string, index):
        exp = self._choose(string, index, 'comp_expression', 'not_expression')
        if exp == Parser.FAIL:
            return Parser.FAIL
        return exp

    def _parse_not_expression(self, string, index):
        exclamation = self._character(string, index, '!')
        if exclamation == Parser.FAIL:
            return Parser.FAIL
        index += 1
        space = self._parse(string, 'opt_space', index)
        index = space.index
        comp_exp = self._parse(string, 'comp_expression', index)
        if comp_exp == Parser.FAIL:
            return Parser.FAIL
        index = comp_exp.index

        return Parse('!', index, comp_exp)


    def _parse_comp_expression(self, string, index):
        add_sub = self._parse(string, 'add_expression', index)
        if add_sub == Parser.FAIL:
            return Parser.FAIL
        index = add_sub.index

        comp_tail = self._zero_or_one(string, index, 'comp_tail')
        if len(comp_tail) == 0:
            return add_sub

        tail = comp_tail[0]
        index = tail.index
        parsed = Parse(tail.children[0], index, add_sub, tail.children[1])

        return parsed


    def _parse_comp_tail(self, string, index):
        operator = self._parse(string, 'comp_operator', index)
        if operator == Parser.FAIL:
            return Parser.FAIL
        index = operator.index

        exp = self._parse(string, 'add_expression', index)
        if exp == Parser.FAIL:
            return Parser.FAIL
        index = exp.index

        return Parse('comp tail', index, operator.type, exp)


    def _parse_if_statement(self, string, index):
        _if = self._string_term(string, index, 'if')
        if _if == Parser.FAIL:
            return Parser.FAIL
        index = _if.index
        space1 = self._parse(string, 'opt_space', index)
        index = space1.index
        open_paren = self._character(string, index, '(')
        if open_paren == Parser.FAIL:
            return Parser.FAIL
        index = open_paren.index
        space2 = self._parse(string, 'opt_space', index)
        index = space2.index
        condition = self._parse(string, 'expression', index)
        if condition == Parser.FAIL:
            return Parser.FAIL
        index = condition.index
        space3 = self._parse(string, 'opt_space', index)
        index = space3.index
        closed_paren = self._character(string, index, ')')
        if closed_paren == Parser.FAIL:
            return Parser.FAIL
        index = closed_paren.index
        space4 = self._parse(string, 'opt_space', index)
        index = space4.index
        open_bracket = self._character(string, index, '{')
        if open_bracket == Parser.FAIL:
            return Parser.FAIL
        index = open_bracket.index
        space5 = self._parse(string, 'opt_space', index)
        index = space5.index
        program = self._parse(string, 'program', index)
        if program == Parser.FAIL:
            return Parser.FAIL
        index = program.index
        space6 = self._parse(string, 'opt_space', index)
        index = space6.index
        closed_bracket = self._character(string, index, '}')
        if closed_bracket == Parser.FAIL:
            return Parser.FAIL
        index = closed_bracket.index

        return Parse('if', index, condition, program)

    def _parse_ifelse_statement(self, string, index):
        _if = self._string_term(string, index, 'if')
        if _if == Parser.FAIL:
            return Parser.FAIL
        index = _if.index
        space1 = self._parse(string, 'opt_space', index)
        index = space1.index
        open_paren = self._character(string, index, '(')
        if open_paren == Parser.FAIL:
            return Parser.FAIL
        index = open_paren.index
        space2 = self._parse(string, 'opt_space', index)
        index = space2.index
        condition = self._parse(string, 'expression', index)
        if condition == Parser.FAIL:
            return Parser.FAIL
        index = condition.index
        space3 = self._parse(string, 'opt_space', index)
        index = space3.index
        closed_paren = self._character(string, index, ')')
        if closed_paren == Parser.FAIL:
            return Parser.FAIL
        index = closed_paren.index
        space4 = self._parse(string, 'opt_space', index)
        index = space4.index
        open_bracket = self._character(string, index, '{')
        if open_bracket == Parser.FAIL:
            return Parser.FAIL
        index = open_bracket.index
        space5 = self._parse(string, 'opt_space', index)
        index = space5.index
        if_program = self._parse(string, 'program', index)
        if if_program == Parser.FAIL:
            return Parser.FAIL
        index = if_program.index
        space6 = self._parse(string, 'opt_space', index)
        index = space6.index
        closed_bracket = self._character(string, index, '}')
        if closed_bracket == Parser.FAIL:
            return Parser.FAIL
        index = closed_bracket.index
        space7 = self._parse(string, 'opt_space', index)
        index = space7.index
        _else = self._string_term(string, index, 'else')
        if _else == Parser.FAIL:
            return Parser.FAIL
        index = _else.index
        space8 = self._parse(string, 'opt_space', index)
        index = space8.index
        open_bracket = self._character(string, index, '{')
        if open_bracket == Parser.FAIL:
            return Parser.FAIL
        index = open_bracket.index
        space9 = self._parse(string, 'opt_space', index)
        index = space9.index
        else_program = self._parse(string, 'program', index)
        if else_program == Parser.FAIL:
            return Parser.FAIL
        index = else_program.index
        space10 = self._parse(string, 'opt_space', index)
        index = space10.index
        closed_bracket = self._character(string, index, '}')
        if closed_bracket == Parser.FAIL:
            return Parser.FAIL
        index = closed_bracket.index

        return Parse('ifelse', index, condition, if_program, else_program)

    def _parse_while_statement(self, string, index):
        _while = self._string_term(string, index, 'while')
        if _while == Parser.FAIL:
            return Parser.FAIL
        index = _while.index
        space1 = self._parse(string, 'opt_space', index)
        index = space1.index
        open_paren = self._character(string, index, '(')
        if open_paren == Parser.FAIL:
            return Parser.FAIL
        index = open_paren.index
        space2 = self._parse(string, 'opt_space', index)
        index = space2.index
        condition = self._parse(string, 'expression', index)
        if condition == Parser.FAIL:
            return Parser.FAIL
        index = condition.index
        space3 = self._parse(string, 'opt_space', index)
        index = space3.index
        closed_paren = self._character(string, index, ')')
        if closed_paren == Parser.FAIL:
            return Parser.FAIL
        index = closed_paren.index
        space4 = self._parse(string, 'opt_space', index)
        index = space4.index
        open_bracket = self._character(string, index, '{')
        if open_bracket == Parser.FAIL:
            return Parser.FAIL
        index = open_bracket.index
        space5 = self._parse(string, 'opt_space', index)
        index = space5.index
        body = self._parse(string, 'program', index)
        if body == Parser.FAIL:
            return Parser.FAIL
        index = body.index
        space6 = self._parse(string, 'opt_space', index)
        index = space6.index
        closed_bracket = self._character(string, index, '}')
        if closed_bracket == Parser.FAIL:
            return Parser.FAIL
        index = closed_bracket.index

        return Parse('while', index, condition, body)


    def _parse_parenthesized_expression(self, string, index):
        parenthesis = self._character(string, index, '(')
        if (parenthesis == Parser.FAIL):
            return Parser.FAIL
        index += 1
        space1 = self._parse(string, 'opt_space', index)
        index = space1.index
        expression = self._parse(string, 'expression', index)
        if (expression == Parser.FAIL):
            return Parser.FAIL
        index = expression.index
        space1 = self._parse(string, 'opt_space', index)
        index = space1.index

        parenthesis = self._character(string, index, ')')
        if (parenthesis == Parser.FAIL):
            return Parser.FAIL
        index += 1

        expression.index = index

        return expression

    def _parse_add_expression(self, string, index):
        mul_div_expression = self._parse(string, 'mul_div_expression', index)
        if (mul_div_expression == Parser.FAIL):
            return Parser.FAIL
        index = mul_div_expression.index

        add_tails = self._zero_or_more(string, index, 'add_tail')

        parsed = mul_div_expression
        for tail in add_tails:
            index = tail.index
            parsed = Parse(tail.children[0], index, parsed, tail.children[1])

        return parsed

    def _parse_add_tail(self, string, index):
        operator = self._choose(string, index, 'add_operator', 'sub_operator')
        if (operator == Parser.FAIL):
            return Parser.FAIL
        index = operator.index

        mul_div_expression = self._parse(string, 'mul_div_expression', index)
        if (mul_div_expression == Parser.FAIL):
            return Parser.FAIL
        index = mul_div_expression.index

        return Parse('add tail', index, operator.type, mul_div_expression)

    def _parse_mul_div_expression(self, string, index):
        call = self._parse(string, 'call_expression', index)
        if (call == Parser.FAIL):
            return Parser.FAIL
        index = call.index
        space = self._parse(string, 'opt_space', index)
        index = space.index
        mul_tails = self._zero_or_more(string, index, 'mul_tail')
        parsed = call
        for tail in mul_tails:
            index = tail.index
            parsed = Parse(tail.children[0], index, parsed, tail.children[1])
        return parsed

    def _parse_mul_tail(self, string, index):
        operator = self._choose(string, index, 'mul_operator', 'div_operator')
        if (operator == Parser.FAIL):
            return Parser.FAIL
        index = operator.index
        space = self._parse(string, 'opt_space', index)
        index = space.index
        call = self._parse(string, 'call_expression', index)
        if (call == Parser.FAIL):
            return Parser.FAIL
        index = call.index
        return Parse('mul tail', index, operator.type, call)

    def _parse_assignment_statement(self, string, index):
        location = self._parse(string, 'identifier', index)
        if (location == Parser.FAIL):
            return Parser.FAIL
        location.type = 'varloc'
        index = location.index

        space = self._parse(string, 'opt_space', index)
        index = space.index

        equals = self._character(string, index, '=')
        if (equals == Parser.FAIL):
            return Parser.FAIL
        index = equals.index

        space = self._parse(string, 'opt_space', index)
        index = space.index

        expression = self._parse(string, 'expression', index)
        if (expression == Parser.FAIL):
            return Parser.FAIL
        index = expression.index

        space = self._parse(string, 'opt_space', index)
        index = space.index

        semicolon = self._character(string, index, ';')
        if (semicolon == Parser.FAIL):
            return Parser.FAIL
        index = semicolon.index

        return Parse('assign', index, location, expression)

    def _parse_identifier(self, string, index):
        first = self._choose(string, index, 'alpha', 'underscore')
        if (first == Parser.FAIL):
            return Parser.FAIL
        index = first.index
        id_tails = self._zero_or_more(string, index, 'identifier_tail')
        identifier = string[index - 1]
        if (len(id_tails) > 0):
            last_index = id_tails[len(id_tails) - 1].index
        else:
            last_index = index
        for tail in id_tails:
            if tail.children[0].index > last_index:
                break
            identifier += string[tail.children[0].index -1]
        if identifier in Parser.KEYWORDS:
            return Parser.FAIL
        return Parse('lookup', last_index, identifier)

    def _parse_identifier_tail(self, string, index):
        id_char = self._choose(string, index, 'alpha', 'integer', 'underscore')
        if (id_char == Parser.FAIL):
            return Parser.FAIL
        index = id_char.index
        return Parse('identifier tail', index, id_char)

    def _parse_declaration_statement(self, string, index):
        word = self._parse(string, 'type', index)
        if (word == Parser.FAIL):
            return Parser.FAIL
        if word.type == 'var':
            word.type = ''
        index = word.index

        space = self._parse(string, 'req_space', index)
        if (space == Parser.FAIL):
            return Parser.FAIL
        index = space.index

        assignment_statement = self._parse(string, 'assignment_statement', index)
        if (assignment_statement == Parser.FAIL):
            return Parser.FAIL
        index = assignment_statement.index
        assignment_statement.children[0].type = ''
        return Parse('declare', index, word.type, assignment_statement.children[0], assignment_statement.children[1])

    def _parse_parameters(self, string, index):
        leading_space = self._parse(string, 'opt_space', index)
        index = leading_space.index
        params = self._zero_or_one(string, index, 'parameters_inner')
        if len(params) == 0:
            trailing_space = self._parse(string, 'opt_space', index)
            index = trailing_space.index
            return Parse('parameters', index)
        index = params[len(params)-1].index
        trailing_space = self._parse(string, 'opt_space', index)
        index = trailing_space.index
        parsed = Parse('parameters', params[0].index)
        parsed.children =  params[0].children
        return parsed

    def _parse_parameters_inner(self, string, index):
        identifier = self._parse(string, 'parameter', index)
        if identifier == Parser.FAIL:
            return Parser.FAIL
        index = identifier.index

        space1 = self._parse(string, 'opt_space', index)
        index = space1.index

        param_tails = self._zero_or_more(string, index, 'parameter_tail')
        param_tails.insert(0, identifier)
        for tail in param_tails:
            index = tail.index
        parsed = Parse('parameters inner', index)
        parsed.children = param_tails
        
        return parsed

    def _parse_parameter_tail(self, string, index):
        comma = self._character(string, index, ',')
        if comma == Parser.FAIL:
            return Parser.FAIL
        index += 1

        leading_space = self._parse(string, 'opt_space', index)
        index = leading_space.index

        identifier = self._parse(string, 'parameter', index)
        if identifier == Parser.FAIL:
            return Parser.FAIL
        index = identifier.index

        trailing_space = self._parse(string, 'opt_space', index)
        index = trailing_space.index
        return Parse(identifier.type, index, identifier)

    def _parse_parameter(self, string, index):
        p_type = self._zero_or_one(string, index, 'param_type')
        if len(p_type) != 0:
            index = p_type[0].index
        identifier = self._parse(string, 'identifier', index)
        if identifier == Parser.FAIL:
            return Parser.FAIL
        index = identifier.index
        identifier.type = ''
        if len(p_type)==0:
            return Parse(identifier.type, index, identifier)
        return Parse(p_type[0].type, index, identifier)
    
    def _parse_param_type(self, string, index):
        p_type = self._parse(string, 'type', index)
        if p_type == Parser.FAIL:
            return Parser.FAIL
        index = p_type.index
        space = self._parse(string, 'req_space', index)
        if space == Parser.FAIL:
            return Parser.FAIL
        index = space.index
        return Parse(p_type.type, index)

    def _parse_type(self, string, index):
        t = self._choose_chars(string, index, 'func', 'int', 'var')
        if t == Parser.FAIL:
            return Parser.FAIL
        index = t.index
        return t

    def _parse_return_type(self, string, index):
        arrow = self._string_term(string, index, '->')
        if arrow == Parser.FAIL:
            return Parser.FAIL
        index = arrow.index
        space = self._parse(string, 'opt_space', index)
        index = space.index
        t = self._parse(string, 'type', index)
        if t == Parser.FAIL:
            return Parser.FAIL
        index = t.index
        return Parse('return type', index, t)

    def _parse_arguments(self, string, index):
        leading_space = self._parse(string, 'opt_space', index)
        index = leading_space.index
        args = self._zero_or_one(string, index, 'arguments_inner')
        if len(args) == 0:
            trailing_space = self._parse(string, 'opt_space', index)
            index = trailing_space.index
            return Parse('arguments', index)
        index = args[len(args)-1].index
        trailing_space = self._parse(string, 'opt_space', index)
        index = trailing_space.index
        parsed = Parse('arguments', args[0].index)
        parsed.children =  args[0].children
        return parsed

    def _parse_arguments_inner(self, string, index):
        exp = self._parse(string, 'expression', index)
        if exp == Parser.FAIL:
            return Parser.FAIL
        index = exp.index

        space1 = self._parse(string, 'opt_space', index)
        index = space1.index

        arg_tails = self._zero_or_more(string, index, 'argument_tail')
        arg_tails.insert(0, exp)
        for tail in arg_tails:
            index = tail.index
        parsed = Parse('arguments inner', index)
        parsed.children = arg_tails

        return parsed

    def _parse_argument_tail(self, string, index):
        comma = self._character(string, index, ',')
        if comma == Parser.FAIL:
            return Parser.FAIL
        index += 1

        leading_space = self._parse(string, 'opt_space', index)
        index = leading_space.index

        exp = self._parse(string, 'expression', index)
        if exp == Parser.FAIL:
            return Parser.FAIL
        index = exp.index

        trailing_space = self._parse(string, 'opt_space', index)
        index = trailing_space.index

        return Parse('argument tail', index, exp)

    def _parse_function(self, string, index):
        func = self._string_term(string, index, 'func')
        if func == Parser.FAIL:
            return Parser.FAIL
        index = func.index
        space1 = self._parse(string, 'opt_space', index)
        index = space1.index
        open_paren = self._character(string, index, '(')
        if open_paren == Parser.FAIL:
            return Parser.FAIL
        index += 1
        params = self._parse(string, 'parameters', index)
        if params == Parser.FAIL:
            return Parser.FAIL
        index = params.index
        closed_paren = self._character(string, index, ')')
        if closed_paren == Parser.FAIL:
            return Parser.FAIL
        index += 1
        space2 = self._parse(string, 'opt_space', index)
        index = space2.index
        ret_type = self._zero_or_one(string, index, 'return_type')
        if len(ret_type) != 0:
            index = ret_type[0].index
        space3 = self._parse(string, 'opt_space', index)
        index = space3.index
        open_bracket = self._character(string, index, '{')
        if open_bracket == Parser.FAIL:
            return Parser.FAIL
        index += 1
        program = self._parse(string, 'program', index)
        if program == Parser.FAIL:
            return Parser.FAIL
        index = program.index
        closed_bracket = self._character(string, index, '}')
        if closed_bracket == Parser.FAIL:
            return Parser.FAIL
        index += 1

        types_list = []
        for child in params.children:
            types_list.append(child.type)
        if len(ret_type) != 0 or 'var' in types_list or 'func' in types_list or 'int' in types_list: # FIXME or if any of the parameters are typed
            if len(ret_type) == 0:
                ret_type.append(Parse('ret type', 0, Parse('var', 0)))
            types_list = []
            for child in params.children:
                if child.type == '':
                    child.type = 'var'
                types_list.append(child.type)
            print("types list: " + str(types_list))
            types_list.append(ret_type[0].children[0].type)
            sig = Parse('signature', index)
            sig.children = types_list
            return Parse('function', index, sig, params, program)
        return Parse('function', index, params, program)

    def _parse_function_call(self, string, index):
        open_paren = self._character(string, index, '(')
        if open_paren == Parser.FAIL:
            return Parser.FAIL
        index += 1
        space1 = self._parse(string, 'opt_space', index)
        index = space1.index
        args = self._parse(string, 'arguments', index)
        if args == Parser.FAIL:
            return Parser.FAIL
        index = args.index
        space2 = self._parse(string, 'opt_space', index)
        index = space2.index
        closed_paren = self._character(string, index, ')')
        if closed_paren == Parser.FAIL:
            return Parser.FAIL
        index += 1
        parsed = Parse(args.type, index)
        parsed.children = args.children
        return parsed

    def _parse_call_expression(self, string, index):
        operand = self._parse(string, 'operand', index)
        if (operand == Parser.FAIL):
            return Parser.FAIL
        index = operand.index
        space = self._parse(string, 'opt_space', index)
        index = space.index
        call_tails = self._zero_or_more(string, index, 'call_tail')
        parsed = operand
        if len(call_tails) == 0:
            return Parse('', index, operand)
        for tail in call_tails:
            index = tail.index
            parsed = Parse('call', index, parsed, tail.children[0])
        return parsed

    def _parse_call_tail(self, string, index):
        call = self._parse(string, 'function_call', index)
        if call == Parser.FAIL:
            return Parser.FAIL
        index = call.index
        return Parse('call tail', index, call)

    def _parse_operand(self, string, index):
        return self._choose(string, index, 'parenthesized_expression', 'function', 'identifier', 'integer')

    def _parse_integer(self, string, index):
        parsed = ''
        while (index < len(string) and string[index].isdigit()):
            parsed += string[index]
            index += 1
        if (parsed == ''):
            return Parser.FAIL
        return Parse('integer', index, int(parsed))

    def _parse_sub_operator(self, string, index):
        leading_space = self._parse(string, 'opt_space', index)
        index = leading_space.index

        operator = self._character(string, index, '-')
        if (operator == Parser.FAIL):
            return Parser.FAIL
        index += 1

        trailing_space = self._parse(string, 'opt_space', index)
        index = trailing_space.index
        return Parse('-',index)

    def _parse_add_operator(self, string, index):
        leading_space = self._parse(string, 'opt_space', index)
        index = leading_space.index

        operator = self._character(string, index, '+')
        if (operator == Parser.FAIL):
            return Parser.FAIL
        index += 1

        trailing_space = self._parse(string, 'opt_space', index)
        index = trailing_space.index
        return Parse('+',index)

    def _parse_mul_operator(self, string, index):
        leading_space = self._parse(string, 'opt_space', index)
        index = leading_space.index

        operator = self._character(string, index, '*')
        if (operator == Parser.FAIL):
            return Parser.FAIL
        index += 1

        trailing_space = self._parse(string, 'opt_space', index)
        index = trailing_space.index
        return Parse('*',index)

    def _parse_div_operator(self, string, index):
        leading_space = self._parse(string, 'opt_space', index)
        index = leading_space.index

        operator = self._character(string, index, '/')
        if (operator == Parser.FAIL):
            return Parser.FAIL
        index += 1

        trailing_space = self._parse(string, 'opt_space', index)
        index = trailing_space.index
        return Parse('/',index)

    def _parse_comp_operator(self, string, index):
        leading_space = self._parse(string, 'opt_space', index)
        index = leading_space.index

        operator = self._choose_chars(string, index, '==', '!=', '<=', '>=', '<', '>')
        if (operator == Parser.FAIL):
            return Parser.FAIL
        index = operator.index

        trailing_space = self._parse(string, 'opt_space', index)
        index = trailing_space.index
        return Parse(operator.type, index)

    def _parse_and_operator(self, string, index):
        leading_space = self._parse(string, 'opt_space', index)
        index = leading_space.index

        operator = self._string_term(string, index, '&&')
        if (operator == Parser.FAIL):
            return Parser.FAIL
        index += 2

        trailing_space = self._parse(string, 'opt_space', index)
        index = trailing_space.index
        return Parse('&&', index)

    def _parse_or_operator(self, string, index):
        leading_space = self._parse(string, 'opt_space', index)
        index = leading_space.index

        operator = self._string_term(string, index, '||')
        if (operator == Parser.FAIL):
            return Parser.FAIL
        index += 2

        trailing_space = self._parse(string, 'opt_space', index)
        index = trailing_space.index
        return Parse('||', index)

    def _parse_opt_space(self, string, index):
        space = self._zero_or_more(string, index, 'whitespace')
        if (len(space) > 0):
            index = space[len(space) - 1].index
        return Parse('whitespace', index)

    def _parse_req_space(self, string, index):
        space = self._one_or_more(string, index, 'whitespace')
        if space == Parser.FAIL:
            return Parser.FAIL
        index = space[len(space) - 1].index
        return Parse('whitespace', index)

    def _parse_whitespace(self, string, index):
        space = self._choose_chars(string, index, ' ', '\n', '\t')
        if space == Parser.FAIL:
            comment = self._parse(string, 'comment', index)
            if (comment == Parser.FAIL):
                return Parser.FAIL
            else:
                index = comment.index
        else:
            index += 1
        return Parse('whitespace',index)

    def _parse_comment(self, string, index):
        pound = self._character(string, index, '#')
        if pound == Parser.FAIL:
            return Parser.FAIL
        index += 1

        while string[index] != '\n' and index < len(string):
            if index == len(string)-1:
                return Parser.FAIL
            index += 1
        index += 1

        return Parse('comment', index)

    def _parse_alpha(self, string, index):
        if (index >= len(string)):
            return Parser.FAIL
        if not string[index].isalpha():
            return Parser.FAIL
        index += 1
        return Parse('alpha', index)

    def _parse_underscore(self, string, index):
        underscore = self._character(string, index, '_')
        if (underscore == Parser.FAIL):
            return Parser.FAIL
        index += 1
        return Parse('_', index)

def main():
    parser = Parser()
if __name__ == '__main__':
    main()
