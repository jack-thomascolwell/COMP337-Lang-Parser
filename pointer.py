class Pointer:
    def __init__(self, environment, var):
        self.__environment = environment
        self.__var = var

    def get(self):
        self.__environment.get(self.__var)

    def set(self, val):
        self.__environment.set(self.__var, val)

    def __str__(self):
        return "-> %s in %s"%(self.__var,self.__environment)
