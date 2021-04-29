from sexp import sexp
from parse import Parse

class ConstantFoldingTransform:

    def is_add_sub(self, node):
        return isinstance(node, Parse) and node.type in '+-'

    def is_mul_div(self, node):
        return isinstance(node, Parse) and node.type in '*/'

    def is_statement(self, node):
        return isinstance(node, Parse) #and node.type in ('declare', 'assign', 'ifelse', 'if', 'while', 'return', 'print', '' )

    def visit(self, node):
        if (isinstance(node, int)):
            return node
        children = []
        for child in node.children:
            if self.is_statement(child):
                print((str(child), self.is_add_sub(node), self.is_add_sub(child)))
                child = self.visit(child)
                if not self.is_add_sub(node) and self.is_add_sub(child):
                    child = self.add_sub_transform(child)
            children.append(child)
        node.children = children
        if self.is_mul_div(node):
            return self.mul_div_transform(node)
        else:
            return node

    def add_sub_transform(self, node):
        # This function is called on the _top_ addition or subtraction node.
        # "Top" here means that if the node's parent is _not_ an addition or
        # subtraction node. So for (print (+ 2 (* 3 (+ 4 5)))), this function
        # will be called twice - once for (+ 4 5), and once for (+ 2 ... ).
        if (isinstance(node, int)):
            return node
        if (not self.is_add_sub(node)):
            return (node, 0, 1)

        sign = eval('0 %s 1'%node.type)
        

        # print(node)
        # if not self.is_add_sub(node):
        #     print("not addsub")
        #     return (node, 0, 1)
        # sign = eval('%s1'%node.type)
        # childA, childB = node.children
        # if (isinstance(childA, int) and isinstance(childB, int)):
        #     print("both primitive %s"%(childA + sign * childB))
        #     return childA + sign * childB
        # elif (isinstance(childA, int)):
        #     childB = self.add_sub_transform(childB)
        #     if (isinstance(childB, tuple)):
        #         childB, constantB, signB = childB
        #         print("A primitive B tuple %s, %s, %s"%(childB, signB * (sign* childA + constantB), sign * signB))
        #         return (childB, childA + sign*constantB, sign * signB)
        #     print("A primitive B primitive %s"%childB + childA)
        #     return childB + childA
        # elif (isinstance(childB, int)):
        #     childA = self.add_sub_transform(childA)
        #     if (isinstance(childA, tuple)):
        #         childA, constantA, signA = childA
        #         print("B primitive A tuple %s, %s, %s"%(childA, sign * childB + constantA, signA))
        #         return (childA, sign * childB + constantA, signA)
        #     print("B primitive A primitive %s"%childA + sign * childB)
        #     return childA + sign * childB
        # childA = self.add_sub_transform(childA)
        # childB = self.add_sub_transform(childB)
        # if (isinstance(childA, tuple) and isinstance(childB, tuple)):
        #     childA, constantA, signA = childA
        #     childB, constantB, signB = childB
        #     print("neither primitive -> both tuple %s %s %s"%(str(Parse(('+', '-')[signA != signB], 0, childA, childB)), constantA*signA + constantB*signB*sign, signA*sign))
        #     return (Parse(('+', '-')[signA != sign], 0, childA, childB), constantA*signA + constantB*signB*sign, signA)
        # elif (isinstance(childA, tuple)):
        #     childA, constantA, signA = childA
        #     print("neither primitive -> a tuple %s %s %s"%(childA, sign * childB + constantA, signA))
        #     return (childA, sign * childB + constantA, signA)
        # elif (isinstance(childB, tuple)):
        #     childB, constantB, signB = childB
        #     print("neither primitive -> b tuple %s %s %s"%(childB, sign * signB * (childA + constantB), sign * signB))
        #     return (childB, sign * signB * (childA + constantB), sign * signB)
        # print ("neither primitive -> neither tuple %s"%(childA+childB))
        # return childA + childB

    def extract_terms(self, node):


    def mul_div_transform(self, node):
        # This function is called on _every_ multiply and divide node.
        childA, childB = node.children
        if (isinstance(childA, int) and isinstance(childB, int)):
            if (node.type == '/' and childB == 0):
                return node
            return int(eval('%d %s %d'%(childA, node.type, childB)))
        return node

def main():
    transform = ConstantFoldingTransform()
    print(transform.visit(sexp('(print (+ (- (- (lookup i) (lookup i)) (lookup i)) 12))')))
if __name__ == '__main__':
    main()
