from parse import Parse
from sexp import sexp

class Parser:
    FAIL = Parse('',-1)
    KEYWORDS = ['print', 'var', 'if', 'else', 'while', 'func', 'ret', 'class', 'int', 'bool', 'string']

    # FIXME add syntax error messages

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

    def _parse(self, string, term, index):  # used to have index=0
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

    def _choose_chars(self, string, index, *terms): #FIXME change fn name
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
        # opt leading and trailing spaces included in comp_operator parse, FIXME add this to CHARACTER
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

    # def _parse_mul_div_expression(self, string, index):
    #     operand = self._parse(string, 'operand', index)
    #     if (operand == Parser.FAIL):
    #         return Parser.FAIL
    #     index = operand.index

    #     mul_tails = self._zero_or_more(string, index, 'mul_tail')

    #     parsed = operand
    #     for tail in mul_tails:
    #         index = tail.index
    #         parsed = Parse(tail.children[0], index, parsed, tail.children[1])

    #     return parsed

    # def _parse_mul_tail(self, string, index):
    #     operator = self._choose(string, index, 'mul_operator', 'div_operator')
    #     if (operator == Parser.FAIL):
    #         return Parser.FAIL

    #     index = operator.index

    #     operand = self._parse(string, 'operand', index)
    #     if (operand == Parser.FAIL):
    #         return Parser.FAIL
    #     index = operand.index

    #     return Parse('add tail', index, operator.type, operand)

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
        word = self._string_term(string, index, 'var')
        if (word == Parser.FAIL):
            return Parser.FAIL
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
        return Parse('declare', index, assignment_statement.children[0], assignment_statement.children[1])

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
        identifier = self._parse(string, 'identifier', index)
        if identifier == Parser.FAIL:
            return Parser.FAIL
        identifier.type = ''
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

        identifier = self._parse(string, 'identifier', index)
        if identifier == Parser.FAIL:
            return Parser.FAIL
        identifier.type = ''
        index = identifier.index

        trailing_space = self._parse(string, 'opt_space', index)
        index = trailing_space.index

        return Parse('parameter tail', index, identifier)

    def _parse_arguments(self, string, index):
        leading_space = self._parse(string, 'opt_space', index)
        index = leading_space.index
        args = self._zero_or_one(string, index, 'arguments_inner')
        if len(args) == 0: # orr check for num children being > 0 wherever this is called?
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
        return Parse('function', index, params, program)

    def _parse_function_call(self, string, index):
        open_paren = self._character(string, index, '(')
        if open_paren == Parser.FAIL:
            return Parser.FAIL
        index += 1
        args = self._parse(string, 'arguments', index)
        if args == Parser.FAIL:
            return Parser.FAIL
        index = args.index
        closed_paren = self._character(string, index, ')')
        if closed_paren == Parser.FAIL:
            return Parser.FAIL
        index += 1
        parsed = Parse(args.type, index)
        parsed.children = args.children
        return parsed

    # def _parse_mul_div_expression(self, string, index):
        # call = self._parse(string, 'call_expression', index)
        # if (call == Parser.FAIL):
        #     return Parser.FAIL
        # index = call.index
        # space = self._parse(string, 'opt_space', index)
        # index = space.index
        # mul_tails = self._zero_or_more(string, index, 'mul_tail')
        # parsed = call
        # for tail in mul_tails:
        #     index = tail.index
        #     parsed = Parse(tail.children[0], index, parsed, tail.children[1])
        # return parsed

    # def _parse_mul_tail(self, string, index):
        # operator = self._choose(string, index, 'mul_operator', 'div_operator')
        # if (operator == Parser.FAIL):
        #     return Parser.FAIL
        # index = operator.index
        # space = self._parse(string, 'opt_space', index)
        # index = space.index
        # call = self._parse(string, 'call_expression', index)
        # if (call == Parser.FAIL):
        #     return Parser.FAIL
        # index = call.index
        # return Parse('mul tail', index, operator.type, call)

    def _parse_call_expression(self, string, index): #FIXME repeated lookup things in parsed arguments
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

    # def _parse_call_expression(self, string, index): #FIXME broken for multiple calls in a row
    #     parse = Parse('', index)
    #     operand = self._parse(string, 'operand', index)
    #     if operand == Parser.FAIL:
    #         return Parser.FAIL
    #     index = operand.index
    #     call_tail = self._zero_or_more(string, index, 'call_tail')
    #     if len(call_tail) != 0:
    #         index = call_tail[len(call_tail)-1].index
    #         parse.type = 'call'
    #     trailing_space = self._parse(string, 'opt_space', index)
    #     index = trailing_space.index
    #     parse.index = index
    #     #parse.type = operand.type
    #     call_tail.insert(0, operand)
    #     parse.children = call_tail

    #     return parse

    # def _parse_call_tail(self, string, index):
    #     space = self._parse(string, 'opt_space', index)
    #     index = space.index
    #     call = self._parse(string, 'function_call', index)
    #     if call == Parser.FAIL:
    #         return Parser.FAIL
    #     index = call.index
    #     return Parse('call tail', index, call)

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

    def _parse_whitespace(self, string, index): #FIXME what is a 'BLANK'??
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


def test_parse(parser, string, term, expected):
    actual = parser._parse(string, term)
    assert actual is not None, 'Got None when parsing "{}"'.format(string)
    assert actual == expected, 'Parsing "{}"; expected {} but got {}'.format(
        string, expected, actual
    )

def test():
    parser = Parser()
    # Integer tests
    test_parse(parser, '3', 'integer', Parse(3,1))
    test_parse(parser, '0', 'integer', Parse(0,1))
    test_parse(parser, '100', 'integer', Parse(100,3))
    test_parse(parser, '2021', 'integer', Parse(2021,4))
    test_parse(parser, 'b', 'integer', Parser.FAIL)
    test_parse(parser, '', 'integer', Parser.FAIL)

    # Addition tests
    test_parse(parser, 'b', 'add_expression', Parser.FAIL)
    test_parse(parser, ' ', 'add_expression', Parser.FAIL)
    test_parse(parser, '3-', 'add_expression', Parse(3,1))
    test_parse(parser, '3-+', 'add_expression', Parse(3,1))
    test_parse(parser, '3+4', 'add_expression', Parse(7,3))
    test_parse(parser, '2020+2021', 'add_expression', Parse(4041,9))
    test_parse(parser, '0+0', 'add_expression', Parse(0,3))
    test_parse(parser, '1+1+', 'add_expression', Parse(2,3))
    test_parse(parser, '1+1+-', 'add_expression', Parse(2,3))
    test_parse(parser, '0+0+0+0+0', 'add_expression', Parse(0,9))
    test_parse(parser, '0+42', 'add_expression', Parse(42,4))
    test_parse(parser, '42+0', 'add_expression', Parse(42,4))
    test_parse(parser, '123+234+345', 'add_expression', Parse(702,11))
    test_parse(parser, '0)', 'add_expression', Parse(0,1))

    # Parenthesis tests
    test_parse(parser, '(0)', 'parenthesized_expression', Parse(0,3))
    test_parse(parser, '(', 'parenthesized_expression', Parser.FAIL)
    test_parse(parser, '(0', 'parenthesized_expression', Parser.FAIL)
    test_parse(parser, '(0+0)', 'parenthesized_expression', Parse(0,5))
    test_parse(parser, '(1+2)', 'parenthesized_expression', Parse(3,5))
    test_parse(parser, '(1+2+3)', 'parenthesized_expression', Parse(6,7))

    # Addition with parenthesis tests
    test_parse(parser, '4+(1+2+3)', 'add_expression', Parse(10,9))
    test_parse(parser, '(1+2+3)+4', 'add_expression', Parse(10,9))
    test_parse(parser, '4+(1+2+3)+4', 'add_expression', Parse(14,11))
    test_parse(parser, '3+4+(5+6)+9', 'add_expression', Parse(27,11))

    # End to end test
    test_parse(parser, '(3+4)+((2+3)+0+(1+2+3))+9', 'add_expression', Parse(27,25))

    # Tests with spaces
    test_parse(parser, '1+ 2', 'add_expression', Parse(3,4))
    test_parse(parser, '1 +2', 'add_expression', Parse(3,4))
    test_parse(parser, '1 + 2', 'add_expression', Parse(3,5))
    test_parse(parser, '1- 2', 'add_expression', Parse(-1,4))
    test_parse(parser, '1 -2', 'add_expression', Parse(-1,4))
    test_parse(parser, '1 - 2', 'add_expression', Parse(-1,5))
    test_parse(parser, '( 1)', 'add_expression', Parser.FAIL)
    test_parse(parser, '(1 )', 'add_expression', Parser.FAIL)
    test_parse(parser, '( 1 )', 'add_expression', Parser.FAIL)

    # Tests with subtraction
    test_parse(parser, '3-4', 'add_expression', Parse(-1,3))
    test_parse(parser, '2020-2021', 'add_expression', Parse(-1,9))
    test_parse(parser, '0-0', 'add_expression', Parse(0,3))
    test_parse(parser, '4-(1+2+3)', 'add_expression', Parse(-2,9))
    test_parse(parser, '(1-2+3)+4', 'add_expression', Parse(6,9))
    test_parse(parser, '4-(1+2+3)-4', 'add_expression', Parse(-6,11))
    test_parse(parser, '3+4-(5-6)+9', 'add_expression', Parse(17,11))

    # Multiplication Tests
    test_parse(parser, 'b', 'mul_div_expression', Parser.FAIL)
    test_parse(parser, ' ', 'mul_div_expression', Parser.FAIL)
    test_parse(parser, '3*', 'mul_div_expression', Parse(3,1))
    test_parse(parser, '3**', 'mul_div_expression', Parse(3,1))
    test_parse(parser, '3*4', 'mul_div_expression', Parse(12,3))
    test_parse(parser, '2020*2021', 'mul_div_expression', Parse(2021*2020,9))
    test_parse(parser, '0*0', 'mul_div_expression', Parse(0,3))
    test_parse(parser, '1*1*', 'mul_div_expression', Parse(1,3))
    test_parse(parser, '1*1*-', 'mul_div_expression', Parse(1,3))
    test_parse(parser, '0*0*0*0+0', 'mul_div_expression', Parse(0,9))
    test_parse(parser, '0*42', 'mul_div_expression', Parse(0,4))
    test_parse(parser, '42*0', 'mul_div_expression', Parse(0,4))
    test_parse(parser, '123*234*345', 'mul_div_expression', Parse(123*234*345,11))
    test_parse(parser, '0)', 'mul_div_expression', Parse(0,1))
    test_parse(parser, '0)', 'mul_div_expression', Parse(0,1))

    # Division Tests
    test_parse(parser, 'b', 'mul_div_expression', Parser.FAIL)
    test_parse(parser, ' ', 'mul_div_expression', Parser.FAIL)
    test_parse(parser, '3/', 'mul_div_expression', Parse(3,1))
    test_parse(parser, '3//', 'mul_div_expression', Parse(3,1))
    test_parse(parser, '3/4', 'mul_div_expression', Parse(0.75,3))
    test_parse(parser, '2020/2021', 'mul_div_expression', Parse(2021/2020,9))
    test_parse(parser, '1/1/', 'mul_div_expression', Parse(1,3))
    test_parse(parser, '1/1/-', 'mul_div_expression', Parse(1,3))
    test_parse(parser, '0/1/2/4*0', 'mul_div_expression', Parse(0,9))
    test_parse(parser, '0/42', 'mul_div_expression', Parse(0,4))
    test_parse(parser, '42/2', 'mul_div_expression', Parse(21,4))
    test_parse(parser, '123/234/345', 'mul_div_expression', Parse(123/234/345,11))
    test_parse(parser, '0)', 'mul_div_expression', Parse(0,1))
    test_parse(parser, '2', 'mul_div_expression', Parse(10,16))

    # Multiplication and Division Tests
    test_parse(parser, '123*234/345', 'mul_div_expression', Parse(123*234/345,11))
    test_parse(parser, '123*234*345/2', 'mul_div_expression', Parse(123*234*345/2,13))
    test_parse(parser, '123/234*345/2', 'mul_div_expression', Parse(123/234*345/2,13))

    # Order of Operations Tests
    test_parse(parser, '123*(234+345/2)', 'mul_div_expression', Parse(123*234/345,15))
    test_parse(parser, '123+2/3-(234*345/2)', 'mul_div_expression', Parse(123+2/3-(234*345/2),19))

def main():
    parser = Parser()
    # print(parser._parse_while_statement('while(i<10){i=i+1;}', 0))
    # print(parser._parse_comp_expression('1>2', 0))
    # print(parser._parse_program('if(1){1+1;}else{1-1;}', 0))
    # print(parser._parse_parameters('a1, b2, a3, weee4', 0))
    # print(parser._parse_program('var num = func(n)#this is a function\n{if(1){ret 1;}else{1-1;}};', 0))
    # print(parser._parse_program('''
    # var add1 = func(n){
    #     ret n + 1;
    # };
    # var add2 = func(n){
    #     ret n + 1;
    # };
    # if (add1 == add2){
    #     print 1;
    # }
    # else {
    #     print 0;
    # }
    # ''', 0))
    # print(parser._parse_arguments('x+1, 3, b', 0))
    #print(parser._parse_call_expression('x(w, w)(2)', 0))
    # print(parser._parse_mul_div_expression('1*2', 0))
    # print(parser._parse_comment('# ree\n', 0))
    # print(parser._parse_call_expression('grr(n, 3);', 0))
    # print(parser._parse_program('''if (1 && 2 && 3){
    # print 3;
    # }
    # else {
    #     print 0;
    # }
    # ''', 0))
    # print(parser._parse_program('1&&2&&3;', 0))
    #print(parser._parse_program('1<2<3;', 0))
    #print(parser._parse_program('1&&2&&3;', 0))
    #print(parser._parse_declaration_statement('var t = 1&&2&&3;', 0))
    # test()
    # print("FIXME tests won't work to check S-Expressions")
    #print(parser.parse('var t = func(n, p){};', 'program'))
    # print(parser.parse('((10 > 2) == 1)', 'parenthesized_expression'))
if __name__ == '__main__':
    main()
