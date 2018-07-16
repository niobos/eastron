class Promise:
    def __init__(self, output_function=None):
        self.output_function = output_function
        self.value = None

    def set_value(self, value):
        self.value = value

    def get_value(self):
        if self.output_function is not None:
            return self.output_function(self.value)
        return self.value


class PromiseFunc:
    def __init__(self, func, *promises, **kwpromises):
        self.func = func
        self.promises = promises
        self.kwpromises = kwpromises

    def get_value(self):
        pos_values = [
            p.get_value()
            for p in self.promises
        ]
        kw_values = {
            k: p.get_value()
            for k, p in self.kwpromises.items()
        }
        return self.func(*pos_values, **kw_values)


if __name__ == '__main__':
    p = Promise()
    assert(p.get_value() is None)

    p.set_value(42)
    assert(p.get_value() == 42)

    p = Promise(lambda x: 2*x)
    p.set_value(7)
    assert(p.get_value() == 14)

    x = Promise()
    y = Promise()
    f = PromiseFunc(lambda x, y: x + y,
                    x, y)
    x.set_value(1)
    y.set_value(2)
    assert(f.get_value() == 3)

    x = Promise()
    y = Promise()
    f = PromiseFunc(lambda a, b: a * b,
                    a=x, b=y)
    x.set_value(4)
    y.set_value(5)
    assert(f.get_value() == 20)
