### Arbitrary Attribute Struct
### Similar to JavaScript object

class aastruct:
    def __init__ (self, *args, **kwargs):
        for coll in args:
            if not hasattr(coll, '__getitem__'):
                raise TypeError("%s is not a mapping" % repr(coll))

        try:
            for coll in args + (kwargs,):
                for key in coll:
                    self.__dict__[key] = coll[key]
        except:
            raise TypeError("%s is not a mapping" % repr(coll))

    def __contains__ (self, key):
        return key in self.__dict__

    def __getitem__ (self, key):
        return self.__dict__[key]

    def __setitem__ (self, key, value):
        self.__dict__[key] = value

    def __delitem__ (self, key):
        del self.__dict__[key]

    def __iter__ (self):
        return self.__dict__.iterkeys()

    def __len__ (self):
        return len(self.__dict__)

    def __str__ (self):
        return repr(self)

    def __repr__ (self):
        return "aastruct(" + repr(self.__dict__) + ")"

    dict = lambda s: dict([(k,s[k]) for k in s])
    dict.__doc__ = "aastruct.dict(s) => convert aastruct s to a dict"
