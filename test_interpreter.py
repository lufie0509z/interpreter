import unittest 
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
   