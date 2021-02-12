class Error(Exception):
    pass

class RuntimeError(Error):
    pass

class DivideByZeroError(RuntimeError):
    pass

class Interpreter:
    def __init__(self):
        self.__out = ''

    def _out(self, output):
        self.__out += str(output) + '\n'
        print(output)

    def _eval(self, parse):
        print("Evaluating %s"%str(parse))
        evaluator = getattr(self, '_eval_%s'%(parse.type), None)
        if (not callable(evaluator)):
            raise RuntimeError()
        return evaluator(parse)

    def _exec(self, parse):
        print("Executing %s"%str(parse))
        executor = getattr(self, '_exec_%s'%(parse.type), None)
        if (not callable(executor)):
            raise RuntimeError()
        executor(parse)

    def execute(self, parse):
        try:
            self._exec(parse)
        except RuntimeError:
            print("Runtime error") #TODO Add index reporting

    #FIXME rename + parse to add parse
    def _eval_add(self, parse):
        (operandA, operandB) = parse.children
        resultA = self._eval(operandA)
        resultB = self._eval(operandB)
        return resultA + resultB

    #FIXME rename - parse to sub parse
    def _eval_sub(self, parse):
        (operandA, operandB) = parse.children
        resultA = self._eval(operandA)
        resultB = self._eval(operandB)
        return resultA - resultB

    #FIXME rename * parse to mul parse
    def _eval_mul(self, parse):
        (operandA, operandB) = parse.children
        resultA = self._eval(operandA)
        resultB = self._eval(operandB)
        return resultA * resultB

    #FIXME rename / parse to div parse
    def _eval_div(self, parse):
        (operandA, operandB) = parse.children
        resultA = self._eval(operandA)
        resultB = self._eval(operandB)
        if (resultB == 0):
            raise DivideByZeroError()
        return int(resultA / resultB)

    def _eval_integer(self, parse):
        value = parse.children[0]
        return value

    def _exec_print(self, parse):
        value = self._eval(parse.children[0])
        self._out(value)

    def _exec_program(self, parse):
        for statement in parse.children:
            self._exec(statement)
