### Curry Lisp

import string

class Unbound:
    def __init__ (self, symbol):
        self.value = "Unbound: " + symbol
        self.symbol = symbol
    def __call__ (self, context, arg):
        if self.symbol in context:
            return context[self.symbol]
        else:
            raise Exception(self.symbol)

def with_value(fn, value):
    fn.value = value
    return fn

global_context = {
    None: None,

    # \ is lambda
    '\\': with_value(lambda c1, argName: lambda c2, value: create_function(argName, value, context=dict(c1, **c2)),
                     ['<special form "\\">']),
    ':=': with_value(lambda c1, key: lambda c2, value: global_context.update({key: value if callable(value) else evaluate(value)}),
                     ['<special form ":=">'])
}

def trampoline (f):
    while callable(f):
        f = f()
    return f

def evaluate(value, context=global_context):
    if isinstance(value, str):
        if value in context:
            return context[value]
        else:
            return Unbound(value)
    elif isinstance(value, list):
        # Start with identity function
        fn = lambda c, x: x

        for expr in value:
            fn = fn(context, expr)
            if not callable(fn):
                if (isinstance(fn, list)):
                    fn = evaluate(fn, context=context)
                elif fn in context:
                    fn = context[fn]
                else:
                    # Hack
                    old_fn = fn
                    fn = lambda c, x: old_fn
                    fn.value = old_fn
        return fn

def create_function(argName, value, context):
    result = lambda c, arg: evaluate(value, context=dict(dict(context, **c), **{argName: evaluate(arg, context=dict(context, **c))}))
    result.value = ['\\' + argName, value]
    return result

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

def interpret(code):
    syntax_tree = parse(code)

    print syntax_tree

    value = None
    for expr in syntax_tree:
        value = evaluate(expr)

    return value

def read_line (prev, open_paren):
    line = raw_input(">> ")

    for ch in line:
        if ch == '(':
            open_paren += 1
        elif ch == ')':
            open_paren -= 1

    if open_paren == 0:
        try:
            result = interpret(prev + ' ' + line)
            if result is None:
                pass
            elif hasattr(result, 'value'):
                if isinstance(result.value, str):
                    print "=>", result.value
                else:
                    def reducer(x,y):
                        if isinstance(y, list):
                            y = "(" + reduce(reducer, y, '') + ")"
                        return y if x == '' else x + ' ' + y
                    print "=>", reduce(reducer, result.value, '')
            else:
                print result
        except Exception, e:
            print "Error:", e
        return lambda: read_line('', 0)
    else:
        return lambda: read_line(prev + ' ' + line, open_paren)

if __name__ == '__main__':
    trampoline(lambda: read_line('',0))
