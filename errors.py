class Error(Exception):
    def __str__(self):
        return "error"

class RuntimeError(Error):
    def __str__(self):
        return "runtime error"

class DivideByZeroError(RuntimeError):
    def __str__(self):
        return ("runtime error: divide by zero")

class SyntaxError(Error):
    def __str__(self):
        return "syntax error"

class VariableAlreadyDefinedError(RuntimeError):
    def __str__(self):
        return ("runtime error: variable already defined")

class UndefinedVariableError(RuntimeError):
    def __str__(self):
        return ("runtime error: undefined variable")

class IllegalReturnError(RuntimeError):
    def __str__(self):
        return ("runtime error: returning outside function")

class ArgumentMismatchError(RuntimeError):
    def __str__(self):
        return ("runtime error: argument mismatch")

class CallingNonFunctionError(RuntimeError):
    def __str__(self):
        return "runtime error: calling a non-function"

class MathOperationOnFunctionError(RuntimeError):
    def __str__(self):
        return "runtime error: math operation on functions"

class DuplicateParameterError(RuntimeError):
    def __str__(self):
        return "runtime error: duplicate parameter"
