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
                child = self.visit(child)
                if not self.is_add_sub(node) and self.is_add_sub(child):
                    child = self.add_sub_transform(child)
                    # BOTTOM-UP APPROACH
                    # if (not isinstance(child, int)):
                    #     child, constant, sign = child
                    #     if (sign == 1): #+child
                    #         if (constant == 0): #0
                    #             child = child
                    #         elif (constant > 0): #+
                    #             child = Parse('+', 0, child, constant)
                    #         else: #-
                    #             child = Parse('-', 0, child, -1 * constant)
                    #     else: #-child
                    #         if (constant == 0): #0
                    #             child = Parse('-', 0, 0, child)
                    #         elif (constant > 0): #+
                    #             child = Parse('-', 0, constant, child)
                    #         else: #-
                    #             child = Parse('-', 0, Parse('-', 0, child), -1 * constant)


            children.append(child)
        node.children = children
        if self.is_mul_div(node):
            return self.mul_div_transform(node)
        else:
            return node

    def add_sub_transform(self, node):
        print("Add sub transform: %s"%node)
        # Extract terms and signs on terms (base case if not +- node)
        terms = self.extract_terms(node) # List of tuples with (term, sign) where sign=1,-1
        print("Got terms: %s"%(', '.join([str((str(term[0]), term[1])) for term in terms])))

        # Combine constants and move to end
        constant = sum([ term[0] * term[1] for term in terms if isinstance(term[0], int) ])
        terms = [ term for term in terms if not isinstance(term[0], int) ]
        if (constant < 0):
            terms += [(-1 * constant, -1)]
        elif (constant > 0):
            terms += [(constant, 1)]
        print("Combined and moved constants: %s"%(', '.join([str((str(term[0]), term[1])) for term in terms])))

        # Possibly add a zero at the front or move first nonnegative term to front
        for (index, term) in enumerate(terms):
            if term[1] == 1:
                terms = [term] + terms[:index] + terms[index+1:]
                break
        if (len(terms) == 0 or terms[0][1] != 1): #only negative terms
            terms = [(0,1)] + terms

        print("Moved so positive in front: %s"%(', '.join([str((str(term[0]), term[1])) for term in terms])))

        # Merge nonconstant terms using same alg as parser (add tails)
        parse = terms[0][0]
        for term, sign in terms[1:]:
            parse = Parse(('-', '+')[sign == 1], 0, parse, term)
        print("Merged terms to get: %s"%parse)
        return parse

    def extract_terms(self, node, sign=1):
        if (not self.is_add_sub(node)):
            return [(node, sign)]
        return self.extract_terms(node.children[0], sign) + self.extract_terms(node.children[1], (-1,1)[node.type=='+'] * sign)

    # BOTTOM-UP APPROACH
    # def add_sub_transform(self, node):
    #     # This function is called on the _top_ addition or subtraction node.
    #     # "Top" here means that if the node's parent is _not_ an addition or
    #     # subtraction node. So for (print (+ 2 (* 3 (+ 4 5)))), this function
    #     # will be called twice - once for (+ 4 5), and once for (+ 2 ... ).
    #     if (isinstance(node, int)):
    #         return node
    #     if (not self.is_add_sub(node)):
    #         return (node, 0, 1)
    #
    #     (+ 2 (+ (lookup i) (+ (lookup i) 2)))
    #     2 + (i + (i + 2))
    #     [ (2, 1) , i, i, 2 ]
    #     (i+i) + 4
    #
    #     #12-(i+2)-32-(i-3)+43-(12-i)
    #
    #     # Extract terms and signs on terms (base case if not +- node)
    #     # Combine constants
    #     # Maybe add a zero at the front (or move first nonnegative term to front)
    #     # Merge nonconstant terms using same alg as parser (add tails)
    #
    #     a = self.add_sub_transform(node.children[0])
    #     b = self.add_sub_transform(node.children[1])
    #     pA = isinstance(a, int)
    #     pB = isinstance(b, int)
    #     if (node.type == '+'): # Add node
    #         if (pA and pB): # Both primitive
    #             return a + b
    #         elif (pA): # only A primitive
    #             b, cB, sB = b
    #             return (b, a+cB, sB)
    #         elif (pB): # only B primitive
    #             a, cA, sA = a
    #             return (a, cA+b,sA)
    #         else: # neither primitive
    #             a, cA, sA = a
    #             b, cB, sB = b
    #             if (sA == 1 and sB == 1): # ++
    #                 return (Parse('+', 0, a, b), cA+cB, 1)
    #             elif (sA == 1): #+-
    #                 return (Parse('-', 0, a, b), cA+cB, 1)
    #             elif (sB == 1): #-+
    #                 return (Parse('-', 0, b, a), cA+cB, 1) #(Parse('-', 0, a, b), cA+cB, -1)#
    #             else: #--
    #                 return (Parse('+', 0, a, b), cA+cB, -1)
    #     else: # Sub node
    #         if (pA and pB): # Both primitive
    #             return a - b
    #         elif (pA): # only A primitive
    #             b, cB, sB = b
    #             return (b, a-cB, -1*sB)
    #         elif (pB): # only B primitive
    #             a, cA, sA = a
    #             return (a, cA-b, sA)
    #         else: # neither primitive
    #             a, cA, sA = a
    #             b, cB, sB = b
    #             if (sA == 1 and sB == 1): #++
    #                 return (Parse('-', 0, a, b), cA-cB, 1)
    #             elif (sA == 1): #+-
    #                 return (Parse('+', 0, a, b), cA-cB, 1)
    #             elif (sB == 1): #-+
    #                 return (Parse('+', 0, a, b), cA-cB, -1)
    #             else: #--
    #                 return (Parse('-', 0, b, a), cA-cB, 1) #(Parse('-', 0, a, b), cA-cB, -1)#

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
    # 1 - (12 - (i*2) - 32 - (i - 3) + 43 - (12*i))
    # 1 - 12 + 2i + 32 + (i-3) - 43 + 12i
    # 1 - 12 + 2i + 32 + i - 3 - 43 + 12i
    # 2i + i + 12i - 25
    # (print (- 1 (- (+ (- (- (- 12 (* (lookup i) 2)) 32) (- (lookup i) 3)) 43) (* 12 (lookup i)))))
    result = transform.visit(sexp('(sequence (declare empty (function (parameters) (sequence))) (print (- (+ 3 (lookup empty)) 3)))'))
    print(result)
if __name__ == '__main__':
    main()
