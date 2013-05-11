### Curry Lisp
### Take 5

global_context = {
    ':=': '<special form ":=">'
}

# Anything defined as a synonym of :=
define_operators = set([':='])

# nested context
class context:
    def __init__ (self, members={}, parent=None):
        self.__parent = parent

        if isinstance(members, dict):
            self.__members = members.copy()
        elif isinstance(members, context):
            self.__members = members.__members
            if parent is None:
                self.__parent = members.__parent
        else:
            raise TypeError("members must be dict or context")

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
        return iter(self.keys())

    def __len__ (self):
        return len(self.keys())

    def keys (self):
        keys = set(self.__members.keys())
        if self.__parent is None:
            return keys
        else:
            return keys.union(set(self.__parent.keys()))

    def __str__ (self):
        output = "context:"
        for k in sorted(self.keys()):
            output += "\n  %s => %s" % (k, self[k])
        return output

    def __repr__ (self):
        return "context(%s, parent=%s)" % (repr(self.__members),
                                           repr(self.__parent))

    def update (self, *args):
        for mapping in args:
            for key in mapping:
                self[key] = mapping[key]


# lambda application
class application (list):
    def __repr__(self):
        return "application(" + repr(list(self)) + ")"
    def __getslice__ (self, start, end):
        return application(list(self)[start:end])


# lambda abstraction
class function:
    def __init__ (self, c, arg_name, body):
        self.__c = context(c)
        self.__arg_name = arg_name
        self.__body = application(body)

    def __call__ (self, c2, expr):
        outer_context = context(c2, self.__c)
        inner_context = context({self.__arg_name: expr if isinstance(expr, function) else evaluate(outer_context, expr)},
                                outer_context)

        result = evaluate(inner_context, self.__body)
        return result

    def __str__ (self):
        def reducer(x,y):
            if isinstance(y, list):
                y = "(" + reduce(reducer, y, '') + ")"

            # Give a more traditional look to the lambdas
            if y[0] == '\\':
                y += ' .'

            return y if x == '' else x + ' ' + y
        output = '\\%s . %s' % (self.__arg_name, reduce(reducer, self.__body, ''))

        if len(self.__c) > 0:
            relevant_keys = ""
            for key in self.__c:
                def in_expr (key, expr):
                    if key in expr: return True
                    for subexpr in expr:
                        if isinstance(subexpr, (application, list)):
                            if in_expr(key, subexpr):
                                return True
                    return False

                if in_expr(key, self.__body):
                    relevant_keys += "\n  %s => %s" % (key, self.__c[key])

            if len(relevant_keys) > 0:
                output += "\nwith:" + relevant_keys

        return output

    def __repr__ (self):
        return "function(%s, %s, %s)" % (repr(self.__c),
                                         repr(self.__arg_name),
                                         repr(self.__body))

    def context (self):
        return context(self.__c)

    def body (self):
        return application(self.__body)

    def argument (self):
        return self.__arg_name


def evaluate (c, expr):
    def hashable (obj):
        try:
            return hash(obj) and True
        except:
            return False

    def islambda (expr):
        return isinstance(expr, str) and expr[0] == '\\'

    def make_lambda (arg_name, body):
        # Must have an argument and a body
        if min(len(arg_name), len(body)) > 0:
            return function(c, arg_name, body)
        # No, absolutely *must* have both
        else:
            raise TypeError("lambda expression (\\) requires an argument and body")

    # Symbol -- evaluate
    if isinstance(expr, str):
        if expr in define_operators:
            return c[':=']
        return c[expr]
    # Application
    elif isinstance(expr, (application, list)):
        # Empty list
        if len(expr) == 0:
            return None
        # Lambda expression
        elif islambda(expr[0]):
            return make_lambda(expr[0][1:], expr[1:])
        # Single expression evaluates to itself
        elif len(expr) == 1:
            return evaluate(c, expr[0])
        # Global definition -- has to be handled differently
        elif hashable(expr[0]) and expr[0] in define_operators:
            if len(expr) > 2:
                name = expr[1]

                # Catch the attempt to create a := synonym
                if len(expr) == 3 and hashable(expr[2]) \
                   and expr[2] in define_operators:
                    if name in global_context:
                        del global_context[name]
                    define_operators.add(name)
                else:
                    value = evaluate(c, expr[2:])

                    # Catch the attempt to redefine :=
                    if name == ':=':
                        raise NameError("cannot redefine :=")
                    # Redefining a := synonym is permissible
                    elif name in define_operators:
                        define_operators.remove(name)

                    global_context.update({name: value})

                # Return the identity function.
                # This will allow files to be read.
                return function(c, 'x', ['x'])
            else:
                raise TypeError("global definition (:=) requires a name and a value")
        # Call with arguments
        else:
            fn = evaluate(c, expr[0])

            # reductively apply the arguments
            for i in range(1, len(expr)):
                arg = expr[i]

                # A lambda expression consumes the rest of the expression
                if islambda(arg):
                    return fn(c, make_lambda(arg[1:], expr[i+1:]))
                else:
                    fn = fn(c, evaluate(c, arg))
            return fn


# REPL functions
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
            tree += ['\\']
        elif ch == ' ':
            # Hack: stops variable building for last variable
            tree.append('')

        # Increment i
        i += 1
    filtered_tree = filter(lambda x: None if x == '' else x, tree)
    return filtered_tree if start == 0 else (filtered_tree, i)

def trampoline (f):
    while callable(f):
        f = f()
    return f

def reader (stream, prompt=None, prev='', open_paren=0):
    print prompt,
    line = stream.readline()

    for ch, i in zip(line, range(len(line))):
        if ch == '(':
            open_paren += 1
        elif ch == ')':
            open_paren -= 1
        elif ch == ';':
            line = line[:i]
            break

    if open_paren == 0:
        try:
            print evaluate(context({}, parent=global_context),
                           parse(prev + ' ' + line))
        except KeyError, e:
            print "Value not found:", e
        return lambda: reader(stream, prompt, '', 0)
    else:
        return lambda: reader(stream, prompt, prev + ' ' + line, open_paren)

def start_repl ():
    from sys import stdin

    try:
        trampoline(reader(stdin, ">> "))
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    from sys import argv
    if len(argv) > 1:
        for filename in argv[1:]:
            filehandle = open(filename)
            trampoline(reader(filehandle))

    start_repl()
