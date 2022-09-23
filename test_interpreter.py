from re import T
import unittest
from xmlrpc.client import TRANSPORT_ERROR 
from .interpreter import Interpreter
import interpreter

class InterpreterTest(unittest.TestCase):
    def exec_interpreter(self, source, local_vals = None, dump_code = False, trace_stack = False):
        interpreter = Interpreter(source, local_vals = local_vals, dump_code = dump_code, trace_stack = trace_stack)
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

