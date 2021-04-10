from parse import Parse
import re

def normalize_sexp(string):

    def fail(index):
        return None, index

    def skip_whitespace(string, index):
        while index < len(string) and string[index] in ' \n':
            index += 1
        return index

    def _normalize_sexp(string, index):
        if index > len(string):
            return fail(index)
        index = skip_whitespace(string, index)
        sexp = ''
        if index < len(string) and string[index] == '(':
            index = skip_whitespace(string, index + 1)
            sexp += '('
        match = re.match('[^() \n]+', string[index:])
        if not match:
            return fail(index)
        if sexp == '':
            return match.group(), index + len(match.group())
        sexp = '(' + match.group()
        index += len(match.group())
        # match all children
        while True:
            index = skip_whitespace(string, index)
            # match a child
            child, index = _normalize_sexp(string, index)
            if child is None:
                break
            sexp += ' ' + child
        index = skip_whitespace(string, index)
        if not string[index] == ')':
            raise SyntaxError('malformed S-expression')
        sexp += ')'
        index = skip_whitespace(string, index + 1)
        return sexp, index

    sexp, index = _normalize_sexp(string, 0)
    if index == len(string):
        return sexp
    else:
        raise SyntaxError('malformed S-expression')

def sexp(string, t=0):
    if (string == None):
        return None
    string = normalize_sexp(string)
    #print(f'{t*"  "}Parsing {string}')
    if (string.isnumeric()):
        #print(f'{t*"  "}got numeric')
        return int(string)
    if (not ((')' in string) or ('(' in string))):
        #print(f'{t*"  "}got string')
        return string
    if (re.match('^[(](\S+)[)]$', string) != None):
        return Parse(string[1:-1],0)
    match = re.search("^[(](\S+)[\s]+(.*)[)]$", string)
    if (match == None):
        return None
    title = match.group(1)
    rest = split_terms(match.group(2)).split('\n')
    #print('%sTitle: %s, terms: %s'%(t*'  ',title, rest))
    rest_parsed = [ sexp(term, t+1) for term in rest ]
    #print('%sParsed Terms: %s isa %s'%(t*'  ',[str(p) for p in rest_parsed],[type(p) for p in rest_parsed]))
    for parsed in rest_parsed:
        if (parsed == None):
            return None
    return Parse(title, 0, *rest_parsed)

def split_terms(string):
    string = list(string)
    pCount = 0
    i = 0
    while(i < len(string)):
        if (string[i] == '('):
            pCount += 1
        if (string[i] == ')'):
            pCount -= 1
        if (string[i] == ' ' and pCount == 0):
            string[i] = '\n'
        i += 1
    string = ''.join(string)
    return string

def print_parses(parse):
     if(isinstance(parse, Parse)):
         print(parse)
         for child in parse.children:
             print_parses(child)
     else:
         print('Not a parse: %s'%parse)

def validate_parse(parse):
    if (isinstance(parse, Parse)):
        if (('(' in parse.type) or (')' in parse.type)):
            print('validated %s to false for parsetype'%(parse))
            return False
        result = True
        for child in parse.children:
            result = result and validate_parse(child)
            if (not result):
                print('validated %s to false for parsetypechild'%(parse))
        return result
    else:
        if (('(' in str(parse)) or (')' in str(parse))):
            print('validated %s to false for primitive'%(parse))
        return not (('(' in str(parse)) or (')' in str(parse)))

def main():
    string = '(sequence (declare x 5) (declare printer (function (parameters n) (sequence))) (assign (varloc x) (call (lookup printer) (arguments 42))) (print (lookup x)))'
    sexp_result = sexp(string)
    print(str(sexp_result))
    print(validate_parse(sexp_result))

if __name__ == '__main__':
    main()
