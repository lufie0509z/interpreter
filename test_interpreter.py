from re import T
import unittest
from xmlrpc.client import TRANSPORT_ERROR 
from .interpreter import Interpreter
import interpreter

class InterpreterTest(unittest.TestCase):
    def exec_interpreter(self, source, local_vars = None, dump_code = False, trace_stack = False):
        interpreter = Interpreter(source, local_vars = local_vars, dump_code = dump_code, trace_stack = trace_stack)
        interpreter.exec()
        return interpreter


    def test_add(self):
        source = "a = b + 1"
        interpreter = self.exec_interpreter(source, {'b': 1}, False, False)
        self.assertEqual(2, interpreter.get_local('a'))


    def test_call_func(self):
        source = "n = divmod(a, 2)"
        interpreter = self.exec_interpreter(source, {'a': 11})
        self.assertEqual((5, 1), interpreter.get_local('n'))

    def test_if(self):
        source = """
if a > 10:
    b = True
else:
    b = False""".strip()

        interpreter = self.exec_interpreter(source, {"a": 11})
        self.assertEqual(True, interpreter.get_local('b'))
        
        interpreter = self.exec_interpreter(source, {"a": 1})
        self.assertEqual(False, interpreter.get_local('b'))

        
    def test_define_fuc(self):
            source = """
def f(x, y):
    return x + y + 1

a = 1
b = 2
n = f(a, b)""".strip()

            interpreter = self.exec_interpreter(source, {}, True, True)
            self.assertEqual(4, interpreter.get_local('n'))

    def test_list_resolution(self):
        source = """
n = [x for x in range(a) if x > 5]
        """.strip()
        interpreter = self.exec_interpreter(source, {'a' : 10}, True, True)
        self.assertEqual([6, 7, 8, 9], interpreter.get_local('n'))
