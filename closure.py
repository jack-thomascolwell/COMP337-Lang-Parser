class Closure:
    def __init__(self, params, body, environment, signature):
        self.__params = params #params is a list of parameter names
        self.__body = body #body is a sequence parse
        self.__environment = environment
        self.__signature = signature

    def params(self):
        return self.__params;

    def body(self):
        return self.__body;

    def environment(self):
        return self.__environment;

    def signature(self):
        return self.__signature;

    def __str__(self):
        return "closure"
