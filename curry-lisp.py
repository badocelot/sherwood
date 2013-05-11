### Curry Lisp
### Take 2

import string
from aastruct import struct

class context:
    def __init__ (self, members={}, parent=None):
        self.__parent = parent
        self.__members = members.copy()

    def __getitem__ (self, key):
        if key in self.__members:
            return self.__members[key]
        else:
            if self.__parent is None:
                raise KeyError(key)
            else:
                return self.__parent[key]

    def __setitem__ (self, key, value):
        self.__members[key] = value

    def __iter__ (self):
        return self.__members.iterkeys()


class unbound:
    def __init__ (self, symbol):
        self.__doc__ = "Unbound: " + str(symbol)
        self.__symbol = symbol
    def __call__ (self, context, arg):
        if self.__symbol in context:
            return context[self.__symbol]
        else:
            raise KeyError(self.__symbol)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return self.__doc__


# Basic stuff
nil = struct({'__doc__': 'nil'})
nil.first = lambda: nil
nil.rest = lambda: nil

def cons (f, r):
    return struct({'first': lambda: f, 'rest': lambda: r})


def symbol (sym):
    return with_doc(cons(sym, nil), "symbol: " + str(sym))


# Helpers
def doc (obj):
    return obj.__doc__


def with_doc (obj, doc):
    class c:
        def __call__ (self, c, expr):
            obj(c, expr)
        def __repr__(self):
            return doc
        def __str__(self):
            return repr(self)

    return c()


# Primitive functions
def create_function (context, argName, body):
    def anon (c, expr):
        return evaluate(context({argName: evaluate(c, expr)}, c), body)
    return anon


def evaluate (context, expr):
    if isinstance(expr, str):
        if expr in context:
            return context[value]
        else:
            return unbound(value)
    elif isinstance(expr, list):
        # Start with identity function
        fn = lambda c, x: x

        for exp in expr:
            fn = fn(context, exp)
            if not callable(fn):
                if (isinstance(fn, list)):
                    fn = evaluate(fn, context=context)
                elif fn in context:
                    fn = context[fn]
                else:
                    fn = unbound(fn)
        return fn


global_context = context({
    'nil': nil,
    '\\': with_doc(lambda c, argName:
                       lambda dummy, expr:
                           create_function(c, argName, expr),
                   '<special form "\\">'),
    ':=': with_doc(lambda c, name:
                       lambda dummy, expr:
                           global_context.update({
                               name: evaluate(c, expr)
                           }) or nil,
                   '<special form ":=">'),
})

# REPL functions
def trampoline (f):
    while callable(f):
        f = f()
    return f


def parse (code, start=0):
    tree = ['']

    i = start
    while i < len(code):
        ch = code[i]
        if ch not in " ()\\":
            if isinstance(tree[-1], str):
                tree[-1] += ch
            else:
                tree.append(ch)
        elif ch == '(':
            subtree, i = parse(code, i + 1)
            tree.append(subtree)
        elif ch == ')':
            break
        elif ch == '\\':
            if not isinstance(tree[-1], str):
                tree += ['\\', '']
            elif tree[-1] == '':
                tree[-1] = '\\'
                tree.append('')
            else:
                tree[-1] += '\\'
        elif ch == ' ':
            # Hack: stops variable building for last variable
            tree.append('')

        # Increment i
        i += 1
    filtered_tree = filter(lambda x: None if x == '' else x, tree)
    return filtered_tree if start == 0 else (filtered_tree, i)


def read_line (prev, open_paren):
    line = raw_input(">> ")

    for ch in line:
        if ch == '(':
            open_paren += 1
        elif ch == ')':
            open_paren -= 1

    if open_paren == 0:
        try:
            result = evaluate(global_context, parse(prev + ' ' + line))
            if result is None:
                pass
            elif isinstance(result, list):
                def reducer(x,y):
                    if isinstance(y, list):
                        y = "(" + reduce(reducer, y, '') + ")"
                    return y if x == '' else x + ' ' + y
                print "=>", reduce(reducer, result, '')
            else:
                print result
        except KeyError, e:
            print "Value not found:", e
        return lambda: read_line('', 0)
    else:
        return lambda: read_line(prev + ' ' + line, open_paren)


if __name__ == '__main__':
    trampoline(read_line('',0))
