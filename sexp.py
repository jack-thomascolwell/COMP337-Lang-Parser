from parse import Parse

def sexp(exp):
    if (exp[0] != '('):
        return int(exp)

    if (exp[-1] != ')'):
        return None

    terms = exp[1:-1].split(' ')
    parses = []
    title = terms.pop(0)
    for term in terms:
        parses.append(term)

    return Parse(title, 0, *parses)
