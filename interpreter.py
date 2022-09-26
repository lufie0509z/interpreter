
from cgitb import reset
import dis
import builtins
from collections import ChainMap
from unittest import result

def dump_recursive(code):
    def dump_code(x):
        print(f"====dis code of {code.co_name}==")
        print('co_names:', x.co_names)
        print('co_consts:', x.co_consts)
        print('co_code:', x.co_code)
        print('co_varnames:', x.co_varnames)
        dis.dis(x)

    dump_code(code)
    for item in code.co_consts:
        if hasattr(item, 'co_code'):
            dump_recursive(item)

class ReturnValue(Exception):
    def __init__(self, value):
        self.value = value

class Function:
    def __init__(self, interpreter, name, code, freevars, annonations, kwdefaults, defaults):
        self.interpreter = interpreter
        self.name = name
        self.code = code
        self.freevars = freevars
        self.annonations = annonations
        self.kwdefaults = kwdefaults
    
    def __call__(self, *args, **kwds):
        frame = Frame(self.interpreter, self.code, self.interpreter.top_frame()._scope)
        frame.set_args(args)
        self.interpreter.frame_push(frame)
        result = self.interpreter.top_frame().exec()
        self.interpreter.frame_pop()
        return result


class Frame:
    def __init__(self, interpreter, code, scope):
        self._interpreter = interpreter
        self._code = code
        self._instructions = list(dis.get_instructions(code))
        self._next_instruction = 0
        self._scope = scope.new_child()
        self._stack = []
          
    def get_local(self, name):
        return self._scope[name]
    
    def set_local(self, name, value):
        self._scope[name] = value
    
    def get_const(self, consti):
        return self._code.co_consts[consti]

    def get_name(self, namei):
        return self._code.co_names[namei]

    def set_args(self, args):
        print(args)
        for i, arg in enumerate(args):
            print(i, arg)
            name = self._code.co_varnames[i]
            self.set_local(name, arg)

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

    def dump_stack(self, instruction):
         print(f'Stack after {instruction.opname}({instruction.offset}): {self._stack}')

    def exec(self):
        while True:
            try:
                # print(self._next_instruction)
                instruction = self._instructions[self._next_instruction]
                fn = getattr(self, 'exec_' + instruction.opname)
                result = fn(instruction.arg) #The instructions that execute the jump need to set the jump target and return True
                if self._interpreter._trace_stack:
                    self.dump_stack(instruction)
                if not result:
                    self._next_instruction += 1
            except ReturnValue as e:
                    return e.value

    def exec_LOAD_NAME(self, namei):
        name = self.get_name(namei)
        value = self.get_local(name)
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
        value = self.stack_pop()
        self.set_local(name, value)
    
    def exec_RETURN_VALUE(self, _):
        value = self.stack_pop()
        raise ReturnValue(value)

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
    
    def exec_MAKE_FUNCTION(self, flags):
        name = self.stack_pop()
        code = self.stack_pop()
        freevars, annonations, defaults, kwdefaults = None, None, None, None
        if flags & 0x8:
            freevars = self.stack_pop()
        if flags & 0x4:
            annonations = self.stack_pop()
        if flags & 0x2:
            kwdefaults = self.stack_pop()
        if flags & 0x1:
            defaults = self.stack_pop()
        func = Function(self._interpreter, name, code, freevars, annonations, kwdefaults, defaults)
        self.stack_push(func)

    def exec_LOAD_FAST(self, index):
        name = self._code.co_varnames[index]
        value = self.get_local(name)
        self.stack_push(value)

    def exec_LOAD_FAST(self, varnum):
        name = self._code.co_varnames[varnum]
        value = self.get_local(name)
        self.stack_push(value)

class Interpreter:
    def __init__(self, source, local_vars = None, dump_code = False, trace_stack = False):
        self._code = compile(source, filename = '', mode = 'exec')
        # self._locals = {}
        # self._stack = []
        self._dump_code = dump_code
        self._trace_stack = trace_stack
        # self._instructions = list(dis.get_instructions(self._code))
        # self._next_instruction = 0
        builtins_dict = {x: getattr(builtins, x) for x in dir(builtins) if not x.startswith('__')}
        # if local_vals:
        #     for k, v in local_vals.items():
        #         self.set_local(k, v)
        self._scope = ChainMap(builtins_dict)
        self._frames = []

        main_frame = Frame(self, self._code, self._scope)
        if local_vars:
            for k, v in local_vars.items():
                main_frame.set_local(k, v)      
        self._frames.append(main_frame)

    def top_frame(self):
        return self._frames[-1]

    def get_local(self, name):
        return self.top_frame().get_local(name)
    
    def set_local(self, name, value):
        self.top_frame().set_local(name, value)

    def frame_push(self, frame):
        self._frames.append(frame)

    def frame_pop(self):
        if len(self._frames) == 1:
            raise RuntimeError('main frame cannot pop out')
        return self._frames.pop(-1)

    def exec(self):
        if self._dump_code:
            dump_recursive(self._code)
        self.top_frame().exec()
       