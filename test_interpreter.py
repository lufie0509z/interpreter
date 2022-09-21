import unittest 
from .interpreter import Interpreter

class InterpreterTest(unittest.TestCase):
    def test_add(self):
        source = "a = b + 1"
        interpreter = Interpreter(source)
        interpreter.set_local('b', 2)
        interpreter.exec()
        self.assertEqual(3, interpreter.get_local('a'))

