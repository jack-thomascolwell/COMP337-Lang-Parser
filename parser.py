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

    def parse(self, string, term, index=0, cache=dict()):
        if (self._string != string):
            self._cache = dict()
        if ((term, index) in cache):
            return cache[(term, index)]
        nonterminal = getattr(self, '_parse_%s'%term, None)
        if (not callable(nonterminal)):
            return Parser.FAIL
        result = nonterminal(string, index)
        cache[(term,index)] = result
        return result

    def _parse_constant(self, string, index, constant):
        if (index > str.length()):
            return Parse.FAIL
        return

    def _zero_or_more(self, string, index, term):
        value = 0
        result = self.parse(string, term, index)
        while (result != Parser.FAIL):
            index += result.index
            value += result.value
            result = self.parse(string, term, index)
        return Parse(value, index)

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
            if (result != parse.FAIL):
                return result
