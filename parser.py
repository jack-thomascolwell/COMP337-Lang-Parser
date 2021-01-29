class Parse:

    def __init__(self, value, index):
        self.value = value
        self.index = index

    def __eq__(self, other):
        return (
            isinstance(other, Parse)
            and self.value == other.value
            and self.index == other.index
        )

    def __str__(self):
        return 'Parse(value={}, index{})'.format(self.value, self.index)

class Parser:
    FAIL = Parse(0,-1)

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

    def _parse_constant(self, string, index, constant):
        if (index > str.length()):
            return Parser.FAIL
        return

    def _zero_or_more(self, string, index, term):
        value = 0
        parsed = 0
        result = self.parse(string, term, index)
        while (result != Parser.FAIL):
            index += result.index
            value += result.value
            parsed += result.index
            result = self.parse(string, term, index)
        return Parse(value, parsed)

    def _one_or_more(self, string, index, term):
        first = self.parse(string, term, index)
        if (first == Parser.FAIL):
            return Parser.FAIL
        rest = self._zero_or_more(string, term, index + first.index)
        return Parse(first.value + rest.value, rest.index)

    def _zero_or_one(self, string, index, term):
        first = self.parse(string, term, index)
        if (first == Parser.FAIL):
            return Parse(0,0)
        next = self.parse(string, term, index + first.parse)
        if (next == Parser.FAIL):
            return first
        return Parse(first.value + next.value, next.index)

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
        return Parse(0,1)

    def _parse_parenthesized_expression(self, string, index):
        parenthesis = self._character(string, index, '(')
        if (parenthesis == Parser.FAIL):
            return Parser.FAIL

        add_expression = self.parse(string, 'add_expression', index + 1)
        if (add_expression == Parser.FAIL):
            return Parser.FAIL

        parenthesis = self._character(string, index + 1 + add_expression.index, ')')
        if (parenthesis == Parser.FAIL):
            return Parser.FAIL

        return Parse(add_expression.value, 2 + add_expression.index)

    def _parse_add_expression(self, string, index):
        mul_div_expression = self.parse(string, 'mul_div_expression', index)
        if (mul_div_expression == Parser.FAIL):
            return Parser.FAIL
        add_tail = self._zero_or_more(string, index + mul_div_expression.index, 'add_tail')
        if (add_tail == Parser.FAIL):
            return Parser.FAIL
        return Parse(mul_div_expression.value + add_tail.value, mul_div_expression.index + add_tail.index)

    def _parse_add_tail(self, string, index):
        operator = self._choose(string, index, 'add_operator', 'sub_operator')
        if (operator == Parser.FAIL):
            return Parser.FAIL
        mul_div_expression = self.parse(string, 'mul_div_expression', index + operator.index)
        if (mul_div_expression == Parser.FAIL):
            return Parser.FAIL
        return Parse(operator.value * mul_div_expression.value, mul_div_expression.index + operator.index)

    def _parse_operand(self, string, index):
        return self._choose(string, index, 'parenthesized_expression', 'integer')

    def _parse_integer(self, string, index):
        i=index
        while (i < len(string) and string[i].isdigit()):
            i+=1
        if (i==index):
            return Parser.FAIL
        return Parse(int(string[index:i]), i - index)

    def _parse_sub_operator(self, string, index):
        leading_space = self._zero_or_more(string, index, 'whitespace')

        operator = self._character(string, index + leading_space.index, '-')
        if (operator == Parser.FAIL):
            return Parser.FAIL

        trailing_space = self._zero_or_more(string, index + leading_space.index + 1, 'whitespace')
        return Parse(-1,leading_space.index + trailing_space.index + 1)

    def _parse_add_operator(self, string, index):
        leading_space = self._zero_or_more(string, index, 'whitespace')

        operator = self._character(string, index + leading_space.index, '+')
        if (operator == Parser.FAIL):
            return Parser.FAIL

        trailing_space = self._zero_or_more(string, index + leading_space.index + 1, 'whitespace')
        return Parse(1,leading_space.index + trailing_space.index + 1)

    def _parse_whitespace(self, string, index):
        space = self._character(string, index, ' ')
        if (space == Parser.FAIL):
            return Parser.FAIL
        return Parse(0,1)


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
    test_parse(parser, 'b', 'integer', Parser.FAIL);
    test_parse(parser, '', 'integer', Parser.FAIL);

    # Addition tests
    test_parse(parser, 'b', 'add_expression', Parser.FAIL);
    test_parse(parser, ' ', 'add_expression', Parser.FAIL);
    test_parse(parser, '3-', 'add_expression', Parse(3,1));
    test_parse(parser, '3-+', 'add_expression', Parse(3,1));
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
    test_parse(parser, 'b', 'mul_div_expression', Parser.FAIL);
    test_parse(parser, ' ', 'mul_div_expression', Parser.FAIL);
    test_parse(parser, '3*', 'mul_div_expression', Parse(3,1));
    test_parse(parser, '3**', 'mul_div_expression', Parse(3,1));
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

    # Division Tests
    test_parse(parser, 'b', 'mul_div_expression', Parser.FAIL);
    test_parse(parser, ' ', 'mul_div_expression', Parser.FAIL);
    test_parse(parser, '3/', 'mul_div_expression', Parse(3,1));
    test_parse(parser, '3//', 'mul_div_expression', Parse(3,1));
    test_parse(parser, '3/4', 'mul_div_expression', Parse(0.75,3))
    test_parse(parser, '2020/2021', 'mul_div_expression', Parse(2021/2020,9))
    test_parse(parser, '1/1/', 'mul_div_expression', Parse(1,3))
    test_parse(parser, '1/1/-', 'mul_div_expression', Parse(1,3))
    test_parse(parser, '0/1/2/4*0', 'mul_div_expression', Parse(0,9))
    test_parse(parser, '0/42', 'mul_div_expression', Parse(0,4))
    test_parse(parser, '42/2', 'mul_div_expression', Parse(21,4))
    test_parse(parser, '123/234/345', 'mul_div_expression', Parse(123/234/345,11))
    test_parse(parser, '0)', 'mul_div_expression', Parse(0,1))

    # Multiplication and Division Tests
    test_parse(parser, '123*234/345', 'mul_div_expression', Parse(123*234/345,11))
    test_parse(parser, '123*234*345/2', 'mul_div_expression', Parse(123*234*345/2,13))
    test_parse(parser, '123/234*345/2', 'mul_div_expression', Parse(123/234*345/2,13))

    # Order of Operations Tests
    test_parse(parser, '123*(234+345/2)', 'mul_div_expression', Parse(123*234/345,15))
    test_parse(parser, '123+2/3-(234*345/2)', 'mul_div_expression', Parse(123+2/3-(234*345/2),19))

def main():
    test()

if __name__ == '__main__':
    main()
