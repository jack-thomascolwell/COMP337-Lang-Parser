from environment import Environment
from errors import *
from parse import Parse
from pointer import Pointer
from closure import Closure
from sexp import sexp

class Interpreter:
    def __init__(self, debug=False):
        self.__out = ''
        self.__environment = Environment()
        self.__tab = 0
        self.__debug = debug
        self.__debug_out = ''
        self.__return = 0
        self.__function_depth = 0
        self.__is_returning = False

    def _debug(self, output):
        self.__debug_out += ("  "*self.__tab) + str(output) + '\n'

    def _out(self, output):
        self.__out += str(output) + '\n'

    def _eval(self, parse):
        self._debug("eval %s with environment=%s"%(parse, self.__environment))
        if (self.__is_primitive(parse)):
            self.__tab += 1
            self._debug('got the %s %s'%(self.__type(parse),parse))
            self.__tab -= 1
            return parse
        self.__tab += 1

        renamed_types = { '+':'add', '-': 'sub', '*': 'mul', '/': 'div', '||': 'or', '&&': 'and', '!':'not', '<':'lt', '>': 'gt', '<=': 'leq', '>=': 'geq', '==': 'eq', '!=': 'neq'}
        evaluator = getattr(self, '_eval_%s'%(renamed_types.get(parse.type, parse.type)), None)
        if (not callable(evaluator)):
            raise RuntimeError()

        result = evaluator(parse)
        self._debug('got the %s %s'%(self.__type(result),result))
        self.__tab -= 1
        return result

    def _exec(self, parse):
        self._debug("exec %s with environment=%s"%(parse, self.__environment))
        if (self.__is_primitive(parse)):
            return parse

        renamed_types = { '+':'add', '-': 'sub', '*': 'mul', '/': 'div'}
        executor = getattr(self, '_exec_%s'%(renamed_types.get(parse.type, parse.type)), None)
        self.__tab += 1
        result = None
        if (not callable(executor)):
            result = self._eval(parse)
        else:
            result = executor(parse)
        #self._debug('got %s'%result)
        self.__tab -= 1
        return result

    def __is_primitive(self, parse):
        return not isinstance(parse, Parse)


    def __is_truthy(self, value):
        return isinstance(value, Closure) or value != 0

    def __type(self, value):
        if (isinstance(value, Closure)):
            return 'closure'
        if (isinstance(value, Pointer)):
            return 'pointer'
        if (isinstance(value, Parse)):
            return 'parse'
        if (isinstance(value, Environment)):
            return 'environment'
        return 'integer'

    def execute(self, parse):
        self.__tab = 0;
        self._debug("Interpreting %s"%parse)
        try:
            self._exec(parse)
        except RuntimeError as e:
            self._out(e)
        finally:
            if (len(self.__out) > 0):
                self.__out = self.__out[:-1]
            if (len(self.__debug_out) > 0):
                self.__debug_out = self.__debug_out[:-1]
            if (self.__debug):
                return (self.__out, self.__debug_out)
            else:
                return self.__out

    def _eval_add(self, parse):
        (operandA, operandB) = parse.children
        resultA = self._eval(operandA)
        resultB = self._eval(operandB)
        if (isinstance(resultA, Closure) or isinstance(resultB, Closure)):
            raise MathOperationOnFunctionError()

        return resultA + resultB

    def _eval_sub(self, parse):
        (operandA, operandB) = parse.children
        resultA = self._eval(operandA)
        resultB = self._eval(operandB)
        if (isinstance(resultA, Closure) or isinstance(resultB, Closure)):
            raise MathOperationOnFunctionError()
        return resultA - resultB

    def _eval_mul(self, parse):
        (operandA, operandB) = parse.children
        resultA = self._eval(operandA)
        resultB = self._eval(operandB)
        if (isinstance(resultA, Closure) or isinstance(resultB, Closure)):
            raise MathOperationOnFunctionError()
        return resultA * resultB

    def _eval_div(self, parse):
        (operandA, operandB) = parse.children
        resultA = self._eval(operandA)
        resultB = self._eval(operandB)
        if (isinstance(resultA, Closure) or isinstance(resultB, Closure)):
            raise MathOperationOnFunctionError()
        if (resultB == 0):
            raise DivideByZeroError()
        return int(resultA / resultB)

    def _eval_lookup(self, parse):
        var = parse.children[0]
        environment = self.__environment
        while((not environment.contains(var)) and (not self.__is_returning)):
            environment = environment.get_parent()
            if (environment == None):
                raise UndefinedVariableError()
        return environment.get(var)

    def _eval_varloc(self, parse):
        var = parse.children[0]
        environment = self.__environment
        while(not environment.contains(var)):
            environment = environment.get_parent()
            if (environment == None):
                raise UndefinedVariableError()
        return Pointer(environment, var)

    def _eval_not(self, parse):
        result = self._eval(parse.children[0])
        if (self.__is_truthy(result)):
            return 0
        return 1

    def _eval_and(self, parse):
        (operandA, operandB) = parse.children
        resultA = self._eval(operandA)
        resultB = self._eval(operandB)
        if (self.__is_truthy(resultA) and self.__is_truthy(resultB)):
            return 1
        return 0

    def _eval_or(self, parse):
        (operandA, operandB) = parse.children
        resultA = self._eval(operandA)
        resultB = self._eval(operandB)
        if (self.__is_truthy(resultA) or self.__is_truthy(resultB)):
            return 1
        return 0

    def _eval_lt(self, parse):
        (operandA, operandB) = parse.children
        resultA = self._eval(operandA)
        resultB = self._eval(operandB)
        if ((self.__type(resultA) != 'integer') or (self.__type(resultB) != 'integer')):
            raise MathOperationOnFunctionError()
        if (resultA < resultB):
            return 1
        return 0

    def _eval_gt(self, parse):
        (operandA, operandB) = parse.children
        resultA = self._eval(operandA)
        resultB = self._eval(operandB)
        if ((self.__type(resultA) != 'integer') or (self.__type(resultB) != 'integer')):
            raise MathOperationOnFunctionError()
        if (resultA > resultB):
            return 1
        return 0

    def _eval_leq(self, parse):
        (operandA, operandB) = parse.children
        resultA = self._eval(operandA)
        resultB = self._eval(operandB)
        if ((self.__type(resultA) != 'integer') or (self.__type(resultB) != 'integer')):
            raise MathOperationOnFunctionError()
        if (resultA <= resultB):
            return 1
        return 0

    def _eval_geq(self, parse):
        (operandA, operandB) = parse.children
        resultA = self._eval(operandA)
        resultB = self._eval(operandB)
        if ((self.__type(resultA) != 'integer') or (self.__type(resultB) != 'integer')):
            raise MathOperationOnFunctionError()
        if (resultA >= resultB):
            return 1
        return 0

    def _eval_eq(self, parse):
        (operandA, operandB) = parse.children
        resultA = self._eval(operandA)
        resultB = self._eval(operandB)
        if ((self.__type(resultA) != 'integer') or (self.__type(resultB) != 'integer')):
            if (resultA is resultB):
                return 1
            return 0
        if (resultA == resultB):
            return 1
        return 0

    def _eval_neq(self, parse):
        (operandA, operandB) = parse.children
        resultA = self._eval(operandA)
        resultB = self._eval(operandB)
        if ((self.__type(resultA) != 'integer') or (self.__type(resultB) != 'integer')):
            if (resultA is resultB):
                return 0
            return 1
        if (resultA != resultB):
            return 1
        return 0

    def _eval_function(self, parse):
        (params, body) = parse.children
        if (len(params.children) != len(set(params.children))):
            raise DuplicateParameterError()
        return Closure(params.children, body, self.__environment)

    def _eval_call(self, parse):
        closure = self._eval(parse.children[0])
        if (not isinstance(closure, Closure)):
            raise CallingNonFunctionError()

        args = parse.children[1]

        if (len(closure.params()) != len(args.children)):
            raise ArgumentMismatchError()

        func_environment = Environment(closure.environment())
        for param, arg in zip(closure.params(), args.children):
            val = self._eval(arg)
            func_environment.set(param, val)

        original_environment = self.__environment
        self.__environment = func_environment

        self.__function_depth += 1
        returning = self.__is_returning
        self.__is_returning = False

        self._exec(closure.body())

        value = self.__return

        self.__function_depth -= 1
        self.__return = 0
        self.__is_returning = returning

        self.__environment = original_environment

        return value

    def _exec_print(self, parse):
        value = self._eval(parse.children[0])
        self._out(value)

    def _exec_sequence(self, parse):
        for statement in parse.children:
            if (self.__is_returning):
                return
            self._exec(statement)

    def _exec_declare(self, parse):
        val = self._eval(parse.children[1])
        var = parse.children[0]
        if (self.__environment.contains(var)):
            raise VariableAlreadyDefinedError()
        self.__environment.set(var, val)

    def _exec_assign(self, parse):
        val = self._eval(parse.children[1])
        ptr = self._eval(parse.children[0])
        ptr.set(val)

    def _exec_while(self, parse):
        (cond, body) = parse.children
        while((self._eval(cond) != 0) and (not self.__is_returning)):
            self.__environment = Environment(self.__environment)
            self._exec(body)
            self.__environment = self.__environment.get_parent()

    def _exec_if(self, parse):
        (cond, body) = parse.children
        if(self._eval(cond) != 0):
            self.__environment = Environment(self.__environment)
            self._exec(body)
            self.__environment = self.__environment.get_parent()

    def _exec_ifelse(self, parse):
        (cond, body_if, body_else) = parse.children

        if(self._eval(cond) != 0):
            self.__environment = Environment(self.__environment)
            self._exec(body_if)
            self.__environment = self.__environment.get_parent()
        else:
            self.__environment = Environment(self.__environment)
            self._exec(body_else)
            self.__environment = self.__environment.get_parent()

    def _exec_return(self, parse):
        if (self.__function_depth <= 0):
            raise IllegalReturnError()
        value = self._eval(parse.children[0])
        self.__is_returning = True
        self.__return = value

def main():
    #addn = Parse("sequence", 0, Parse("print", 0, 1), Parse("print", 0, Parse('+',0, 2, 3)))
    #look = Parse("sequence", 0, Parse("declare", 0, 'a', 1), Parse("print", 0, Parse('lookup', 0, 'a')), Parse("assign", 0, Parse("varloc", 0, 'a'), 3), Parse("print", 0, Parse('lookup', 0, 'a')))
    #control = Parse("sequence", 0, Parse("declare", 0, 'a', 5), Parse("while", 0, Parse('lookup', 0, 'a'), Parse('sequence', 0, Parse("assign", 0, Parse("varloc", 0, 'a'), Parse("-", 0, Parse("lookup", 0, 'a'), 1)), Parse('print', 0, Parse('lookup', 0, 'a')))))
    #function = Parse("sequence", 0, Parse("declare", 0, 'a', Parse("function", 0, Parse("parameters", 0, 'a'), Parse('sequence', 0, Parse('print', 0, Parse('lookup', 0, 'a'))))), Parse("call", 0, Parse("lookup", 0 ,'a'), Parse("arguments", 0, 12)))

    program = sexp('(sequence (declare foo (function (parameters a b a) (sequence (print (lookup a)) (print (lookup b))))) (call (lookup foo) (arguments 1 2 3)))')

    interpreter = Interpreter(True)
    out, debug = interpreter.execute(program)
    print("-/ DEBUG /------------------------")
    print(debug)
    print("-/ OUT /--------------------------")
    print(out)
    print("----------------------------------")


if __name__ == '__main__':
    main()
