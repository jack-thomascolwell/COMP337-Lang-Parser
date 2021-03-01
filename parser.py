from parse import Parse

class Parser:
    FAIL = Parse('fail',-1)
    KEYWORDS = ['print', 'var', 'if', 'else', 'while', 'func', 'ret', 'class', 'int', 'bool', 'string']

    def __init__(self):
        self._cache = dict()
        self._string = None

    def parse(self, string, term, index=0):
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
        result = self.parse(string, term, index)
        while (result != Parser.FAIL):
            index = result.index
            parsed.append(result)
            result = self.parse(string, term, index)
        return parsed

    def _one_or_more(self, string, index, term):
        first = self.parse(string, term, index)
        if (first == Parser.FAIL):
            return Parser.FAIL
        index = first.index
        rest = self._zero_or_more(string, term, index)
        return [first, *rest]

    def _zero_or_one(self, string, index, term):
        parse = self.parse(string, term, index)
        if (parse == Parser.FAIL):
            return []
        return [parse]

    def _choose(self, string, index, *terms):
        for term in terms:
            result = self.parse(string, term, index)
            if (result != Parser.FAIL):
                return result
        return Parser.FAIL

    def _character(self, string, index, character):
        if (index >= len(string)):
            return Parser.FAIL
        if (string[index] != character):
            return Parser.FAIL
        return Parse('character',index + 1)

    # FIXME there's already a variable named _string so this should be renamed
    def _string1(self, string, index, word):
        if (index >= len(string)):
            return Parser.FAIL
        i = index
        for char in word:
            if string[i] != char:
                return Parser.FAIL
            i += 1
        index = i
        return Parse('string', index)

    # def _parse_program(self, string, index):
    #     space = self.parse(string, 'opt_space', index)
    #     index = space.index
    #     program = self._zero_or_more(string, index, 'program_tail')


    # def _parse_program_tail(self, string, index):
    #     statement = self.parse(string, 'statement', index)
    #     if statement == Parser.FAIL:
    #         return Parser.FAIL
    #     index = statement.index
    #     space = self.parse(string, 'opt_space', index)
    #     index = space.index
    #     return Parse('program tail', index)

    def _parse_parenthesized_expression(self, string, index):
        parenthesis = self._character(string, index, '(')
        if (parenthesis == Parser.FAIL):
            return Parser.FAIL
        index += 1

        add_expression = self.parse(string, 'add_expression', index)
        if (add_expression == Parser.FAIL):
            return Parser.FAIL
        index = add_expression.index

        parenthesis = self._character(string, index, ')')
        if (parenthesis == Parser.FAIL):
            return Parser.FAIL
        index += 1

        add_expression.index = index

        return add_expression

    def _parse_add_expression(self, string, index):
        mul_div_expression = self.parse(string, 'mul_div_expression', index)
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

        mul_div_expression = self.parse(string, 'mul_div_expression', index)
        if (mul_div_expression == Parser.FAIL):
            return Parser.FAIL
        index = mul_div_expression.index

        return Parse('add tail', index, operator.type, mul_div_expression)

    def _parse_mul_div_expression(self, string, index):
        operand = self.parse(string, 'operand', index)
        if (operand == Parser.FAIL):
            return Parser.FAIL
        index = operand.index

        mul_tails = self._zero_or_more(string, index, 'mul_tail')

        parsed = operand
        for tail in mul_tails:
            index = tail.index
            parsed = Parse(tail.children[0], index, parsed, tail.children[1])

        return parsed

    def _parse_mul_tail(self, string, index):
        operator = self._choose(string, index, 'mul_operator', 'div_operator')
        if (operator == Parser.FAIL):
            return Parser.FAIL
        index = operator.index

        operand = self.parse(string, 'operand', index)
        if (operand == Parser.FAIL):
            return Parser.FAIL
        index = operand.index

        return Parse('add tail', index, operator.type, operand)

    def _parse_assignment_statement(self, string, index):
        location = self.parse(string, 'identifier', index)
        if (location == Parser.FAIL):
            return Parser.FAIL
        location.type = 'varloc'
        index = location.index

        space = self.parse(string, 'opt_space', index)
        index = space.index

        equals = self._character(string, index, '=')
        if (equals == Parser.FAIL):
            return Parser.FAIL
        index = equals.index

        space = self.parse(string, 'opt_space', index)
        index = space.index

        expression = self.parse(string, 'add_expression', index)
        if (expression == Parser.FAIL):
            return Parser.FAIL
        index = expression.index
 
        space = self.parse(string, 'opt_space', index)
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
        return Parse('identifier tail', index, id_char) # FIXME ?

    def _parse_declaration_statement(self, string, index):
        word = self._string1(string, index, 'var')
        if (word == Parser.FAIL):
            return Parser.FAIL
        index = word.index

        space = self._character(string, index, ' ')
        if (space == Parser.FAIL):
            return Parser.FAIL
        index = space.index

        assignment_statement = self.parse(string, 'assignment_statement', index)
        if (assignment_statement == Parser.FAIL):
            return Parser.FAIL
        index = assignment_statement.index
        return Parse('declare', index, assignment_statement.children[0], assignment_statement.children[1]) # FIXME??


    def _parse_operand(self, string, index):
        return self._choose(string, index, 'parenthesized_expression', 'integer', 'identifier')

    def _parse_integer(self, string, index):
        parsed = ''
        while (index < len(string) and string[index].isdigit()):
            parsed += string[index]
            index += 1
        if (parsed == ''):
            return Parser.FAIL
        return Parse('integer', index, int(parsed))

    def _parse_sub_operator(self, string, index):
        leading_space = self.parse(string, 'opt_space', index)
        index = leading_space.index

        operator = self._character(string, index, '-')
        if (operator == Parser.FAIL):
            return Parser.FAIL
        index += 1

        trailing_space = self.parse(string, 'opt_space', index)
        index = trailing_space.index
        return Parse('-',index)

    def _parse_add_operator(self, string, index):
        leading_space = self.parse(string, 'opt_space', index)
        index = leading_space.index

        operator = self._character(string, index, '+')
        if (operator == Parser.FAIL):
            return Parser.FAIL
        index += 1

        trailing_space = self.parse(string, 'opt_space', index)
        index = trailing_space.index
        return Parse('+',index)

    def _parse_mul_operator(self, string, index):
        leading_space = self.parse(string, 'opt_space', index)
        index = leading_space.index

        operator = self._character(string, index, '*')
        if (operator == Parser.FAIL):
            return Parser.FAIL
        index += 1

        trailing_space = self.parse(string, 'opt_space', index)
        index = trailing_space.index
        return Parse('*',index)

    def _parse_div_operator(self, string, index):
        leading_space = self.parse(string, 'opt_space', index)
        index = leading_space.index

        operator = self._character(string, index, '/')
        if (operator == Parser.FAIL):
            return Parser.FAIL
        index += 1

        trailing_space = self.parse(string, 'opt_space', index)
        index = trailing_space.index
        return Parse('/',index)

    def _parse_opt_space(self, string, index):
        space = self._zero_or_more(string, index, 'whitespace')
        if (len(space) > 0):
            index = space[len(space) - 1].index
        return Parse('whitespace',index)

    # FIXME need to add newlines and comments to whitespace
    def _parse_whitespace(self, string, index):
        space = self._character(string, index, ' ')
        if (space == Parser.FAIL):
            return Parser.FAIL
        index += 1
        return Parse('whitespace',index)

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
    actual = parser.parse(string, term)
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
    print(parser._parse_declaration_statement('var cat = cat;', 0))
    #test()
    print("FIXME tests won't work to check S-Expressions")
if __name__ == '__main__':
    main()
