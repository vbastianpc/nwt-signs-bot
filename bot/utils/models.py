
class LazyProperty:
    """Para que LazyProperty pueda cachear en memoria el resultado, y no calcularlo cada vez,
    debe ser un descriptor non-data. Implementar solo __get__, no __set__ ni __delete__
    See https://realpython.com/python-descriptors/#lazy-properties"""
    def __init__(self, function):
        self.function = function
        self.name = function.__name__

    def __get__(self, obj, type=None) -> object: # pylint: disable=redefined-builtin
        if isinstance(obj.__dict__.get('_lazies'), list):
            obj.__dict__['_lazies'].append(self.name)
        else:
            obj.__dict__['_lazies'] = [self.name]
        obj.__dict__[self.name] = self.function(obj)
        return obj.__dict__[self.name]

class SpecialProperty:
    def __set_name__(self, owner, name):
        self.name = name # pylint: disable=attribute-defined-outside-init

    def __set__(self, obj, value) -> None:
        if self.name in obj.__dict__ and obj.__dict__[self.name] != value:
            if '_lazies' in obj.__dict__:
                for lazy in obj.__dict__.get('_lazies') or []:
                    del obj.__dict__[lazy]
                del obj.__dict__['_lazies']
        obj.__dict__[self.name] = value

class classinstancemethod:
    """https://stackoverflow.com/questions/48808788/make-a-method-that-is-both-a-class-method-and-an-instance-method"""
    def __init__(self, method, instance=None, owner=None):
        self.method = method
        self.instance = instance
        self.owner = owner

    def __get__(self, instance, owner=None):
        return type(self)(self.method, instance, owner)

    def __call__(self, *args, **kwargs):
        instance = self.instance
        if instance is None and args:
            instance, args = args[0], args[1:]
        cls = self.owner
        return self.method(cls, instance, *args, **kwargs)
