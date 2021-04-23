class Parse:

    def __init__(self, type, index, *children):
        self.type = type
        self.index = index
        self.children = children

    def __eq__(self, other):
        if (not (isinstance(other, Parse) and self.index == other.index and self.type == other.type)):
            return False
        for child, otherChild in zip(self.children, other.children):
            if (child != otherChild):
                return False
        return True

    def __str__(self):
        labels = ['integer', 'program tail', 'argument tail', 'parameter tail', 'call tail', '']
        if self.type in labels:
            string = ''
            for child in self.children:
                string += str(child) + ' '
            string = string[:-1]
        else:
            string = '(%s '%self.type
            for child in self.children:
                string += str(child) + ' '
            string = string[:-1] + ')'
        return string
