from functools import wraps
import logging
import inspect


def initializer(fun):
    names, varargs, keywords, defaults = inspect.getargspec(fun)
    @wraps(fun)
    def wrapper(self, *args, **kargs):
        for name, arg in dict(zip(names[1:], args)).update(kargs).items():
            setattr(self, name, arg)
        fun(self, *args, **kargs)
    return wrapper
