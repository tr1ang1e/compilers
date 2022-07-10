from kind import Kind, Type


class Container(Kind):
    def __init__(self):
        for name in self.cursorKinds.values():
            setattr(Container, name + 's', list())
