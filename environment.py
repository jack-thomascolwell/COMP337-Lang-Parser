class Environment:

    def __init__(self, parent=None):
        self.__parent = parent
        self.__variables = dict()

    def __str__(self):
        return str(self.__variables)

    def get_parent(self):
        return self.__parent

    def contains(self, var):
        return var in self.__variables

    def set(self, var, value, varType):
        self.__variables[var] = [value,varType]

    def get(self, var):
        return self.__variables[var][0]

    def get_type(self, var):
        return self.__variables[var][1]
