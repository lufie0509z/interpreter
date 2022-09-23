from ast import arg
import dis
import builtins
from unittest import result

class ReturnValue(Exception):
    pass

class Interpreter:
    def __init__(self, source, local_vals = None, dump_code = False, trace_stack = False):
        self._code = compile(source, filename = '', mode = 'exec')
        self._locals = {}
        self._stack = []
        self._dump_code = dump_code
        self._trace_stack = trace_stack
        self._instructions = list(dis.get_instructions(self._code))
        self._next_instruction = 0
        self._builtins = {x: getattr(builtins, x) for x in dir(builtins) if not x.startswith('__')}
        if local_vals:
            for k, v in local_vals.items():
                self.set_local(k, v)

    def get_local(self, name):
        return self._locals[name]
    
    def set_local(self, name, value):
        self._locals[name] = value
    
    def get_const(self, consti):
        return self._code.co_consts[consti]

    def get_name(self, namei):
        return self._code.co_names[namei]

    def stack_push(self, value):
        self._stack.append(value)
    
    def stack_pop(self):
        return self._stack.pop(-1)

    def stack_popn(self, count):
        if count:
            result = self._stack[-count:]
            self._stack = self._stack[:-count]
            return result
        return []

    def dump_code(self):
        print("====dis code==")
        print('co_names:', self._code.co_names)
        print('co_consts:', self._code.co_consts)
        print('co_code:', self._code.co_code)
        print('co_varnames:', self._code.co_varnames)
        dis.dis(self._code)

    def dump_stack(self, instruction):
         print(f'Stack after {instruction.opname}({instruction.offset}): {self._stack}')

    def exec(self):
        if self._dump_code:
            self.dump_code()
        while True:
            try:
                # print(self._next_instruction)
                instruction = self._instructions[self._next_instruction]
                fn = getattr(self, 'exec_' + instruction.opname)
                result = fn(instruction.arg) #The instructions that execute the jump need to set the jump target and return True
                if self._trace_stack:
                    self.dump_stack(instruction)
                if not result:
                    self._next_instruction += 1
            except ReturnValue:
                    break

    def exec_LOAD_NAME(self, namei):
        name = self.get_name(namei)
        if name in self._locals:
            value = self.get_local(name)
        elif name in self._builtins:
            value = self._builtins[name]
        else:
            raise NameError(name)
        self.stack_push(value)

    def exec_LOAD_CONST(self, consti):
        value = self.get_const(consti)
        self.stack_push(value)

    def exec_BINARY_ADD(self, _):
        a = self.stack_pop()
        b = self.stack_pop()
        self.stack_push(a + b)
    
    def exec_STORE_NAME(self, namei):
        name = self._code.co_names[namei]
        self._locals[name] = self.stack_pop()
    
    def exec_RETURN_VALUE(self, _):
        raise ReturnValue()

    def exec_CALL_FUNCTION(self, argc):
        argc = self.stack_popn(argc)
        func = self._stack.pop(-1)
        result = func(*argc)
        self.stack_push(result)
    
    def exec_COMPARE_OP(self, opname):
        opname = dis.cmp_op[opname]
        comparers = {
            '<': lambda x, y: x < y,
            '<=': lambda x, y: x <= y,
            '==': lambda x, y: x == y,
            '!=': lambda x, y: x != y,
            '>': lambda x, y: x > y,
            '>=': lambda x, y: x >= y
        }
        comparer = comparers[opname]
        rhs = self.stack_pop()
        lhs = self.stack_pop()
        result = comparer(lhs, rhs)
        self.stack_push(result)

    def jump_by_offset(self, offset):
        for i, instruction in enumerate(self._instructions):
            if offset == instruction.offset:
                self._next_instruction = i

    def exec_POP_JUMP_IF_FALSE(self, target):
        value = self.stack_pop()
        if not value:
            self.jump_by_offset(target)
            return True
        return False

    def exec_JUMP_FORWARD(self, offset):
        target = self._instructions[self._next_instruction + 1].offset + offset
        self.jump_by_offset(target)
        return True