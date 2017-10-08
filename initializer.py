from functools import wraps
import logging
import inspect
from sys import version_info

if version_info.major == 3 and version_info.minor < 5:
    def initializer(fun):
        names, varargs, keywords, defaults = inspect.getargspec(fun)
        @wraps(fun)
        def wrapper(self, *args, **kargs):
            x =  dict(zip(names[1:], args))
            y = x.update(kargs)
            for name, arg in y.iteritems():
                setattr(self, name, arg)
            fun(self, *args, **kargs)
        return wrapper
else:
    def initializer(fun):
        names, varargs, keywords, defaults = inspect.getargspec(fun)
        @wraps(fun)
        def wrapper(self, *args, **kargs):
            for name, arg in {**dict(zip(names[1:], args)), **kargs}.items():
                setattr(self, name, arg)
            fun(self, *args, **kargs)
        return wrapper