import re
import sys
from pathlib import Path

from parser import Parser # FIXME change this line to use your code if necessary
from interpreter import Interpreter # FIXME change this line to use your code if necessary
from sexp import sexp as sexp_to_parse, validate_parse

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



def fix_newlines(string):
    return '\n'.join(line for line in string.splitlines() if line.strip()) + '\n'


def test_sexp(sexp_path, parse, message):
    """Test a parse's S-expression, if one is specified.

    Parameters:
        sexp_path (Path): The path of the expected S-expression.
        parse (Parse): The Parse object to serialize.
        message (str): The message to output if the test fails.

    Raises:
        AssertError: If the test does not pass.
    """
    if not sexp_path.exists():
        return
    with sexp_path.open() as fd:
        expected_sexp = normalize_sexp(fd.read())
    # process the expected and actual output to deal with whtiespace
    actual_sexp = normalize_sexp(str(parse))
    error = [message,]
    error.append('EXPECTED S-EXPRESSION (multiple whitespaces are ignored)')
    error.append(expected_sexp)
    error.append('ACTUAL S-EXPRESSION (multiple whitespaces are ignored)')
    error.append(actual_sexp)
    assert actual_sexp == expected_sexp, '\n' + '\n'.join(error)


def test_with_file(lang_path, interpreter_only, parser_only):
    """Test using the lang program at the file path.

    Parameters:
        lang_path (Path): The path of the input program.

    Raises:
        AssertError: If the test does not pass.
    """
    # read the program to run
    with lang_path.open() as fd:
        program = fix_newlines(fd.read())
    print()
    print(f'RUNNING {lang_path}')
    print(program)
    # parse the code
    if (not (interpreter_only or parser_only)):
        parser = Parser()
        parse = parser.parse(program, 'program')
        if parse is None:
            # if there's a syntax error, that's our only output
            actual_output = 'syntax error'
        else:
            # otherwise, check against the intermediate representation
            sexp_path = lang_path.parent.joinpath(lang_path.stem + '.sexp')
            test_sexp(sexp_path, parse, 'intermediate representation does not match')
            # run the program to get the output
            actual_output = Interpreter().execute(parse)
        # read the expected output
        out_path = lang_path.parent.joinpath(lang_path.stem + '.out')
        with out_path.open() as fd:
            expected_output = fd.read()
        # process the expected and actual output to deal with newlines
        expected_output = fix_newlines(expected_output)
        actual_output = fix_newlines(actual_output)
        # check against the output
        if actual_output != expected_output:
            lines = ['\n\n']
            lines.append('EXPECTED OUTPUT:')
            lines.append(expected_output)
            lines.append('')
            lines.append('ACTUAL OUTPUT:')
            lines.append(actual_output)
            assert actual_output == expected_output, '\n'.join(lines)
    elif (interpreter_only):
        sexp_path = lang_path.parent.joinpath(lang_path.stem + '.sexp')
        if not sexp_path.exists():
            print('no sexp (no file)')
            return
        with sexp_path.open() as fd:
            contents = fd.read()
            if ((not '(' in contents) or contents == None):
                print('no sexp (empty file)')
                return
            expected_sexp = normalize_sexp(contents)
        # process the expected and actual output to deal with whtiespace
        parse = sexp_to_parse(expected_sexp)
        assert validate_parse(parse), 'Invalid sexp parse: %s'%parse
        assert expected_sexp == str(parse), 'Sexp parse does not match expected sexp: %s'%parse
        print(f'sExp {expected_sexp}')
        # run the sexp
        actual_output = Interpreter().execute(parse)
        # read the expected output
        out_path = lang_path.parent.joinpath(lang_path.stem + '.out')
        with out_path.open() as fd:
            expected_output = fd.read()
        # process the expected and actual output to deal with newlines
        expected_output = fix_newlines(expected_output)
        actual_output = fix_newlines(actual_output)
        # check against the output
        if actual_output != expected_output:
            lines = ['\n\n']
            lines.append('EXPECTED OUTPUT:')
            lines.append(expected_output)
            lines.append('')
            lines.append('ACTUAL OUTPUT:')
            lines.append(actual_output)
            assert actual_output == expected_output, '\n'.join(lines)
    else:
        parser = Parser()
        parse = parser.parse(program, 'program')
        if parse is None:
            # if there's a syntax error, that's our only output
            actual_output = 'syntax error'
            # read the expected output
            out_path = lang_path.parent.joinpath(lang_path.stem + '.out')
            with out_path.open() as fd:
                expected_output = fd.read()
            # process the expected and actual output to deal with newlines
            expected_output = fix_newlines(expected_output)
            actual_output = fix_newlines(actual_output)
            # check against the output
            if actual_output != expected_output:
                lines = ['\n\n']
                lines.append('EXPECTED OUTPUT:')
                lines.append(expected_output)
                lines.append('')
                lines.append('ACTUAL OUTPUT:')
                lines.append(actual_output)
                assert actual_output == expected_output, '\n'.join(lines)
        else:
            # otherwise, check against the intermediate representation
            sexp_path = lang_path.parent.joinpath(lang_path.stem + '.sexp')
            test_sexp(sexp_path, parse, 'intermediate representation does not match')

def test_with_directory(dir_path, interpreter_only, parser_only):
    """Test using the lang programs in the directory.

    Arguments:
        dir_path (Path): A directory containing input programs.
    """
    for lang_path in sorted(dir_path.glob('**/*.lang'), key=(lambda path: str(path).lower())):
        test_with_file(lang_path, interpreter_only, parser_only)


def main():
    """Run command line tests."""
    # set recursion limit to be really high
    sys.setrecursionlimit(10**6)
    n = 1
    interpreter_only = False
    parser_only = False

    if (len(sys.argv) > 1 and sys.argv[1] == '-i'):
        n+=1
        interpreter_only = True
    if (len(sys.argv) > 1 and sys.argv[1] == '-p'):
        n+=1
        parser_only = True

    for arg in sys.argv[n:]:
        path = Path(arg).expanduser().resolve()
        if path.is_dir():
            test_with_directory(path, interpreter_only, parser_only)
        else:
            test_with_file(path, interpreter_only, parser_only)

    print()
    if (interpreter_only):
        print("interpreter passed all test cases")
    elif (parser_only):
        print("parser passed all test cases")
    else:
        print("interpreter and parser passed all test cases")

if __name__ == '__main__':
    main()
