from kinds import Kinds, CommonTypeData


class Writer(Kinds):

    def __init__(self):
        self.containers = dict()
        for kind in self.cursorKinds.keys():
            self.containers[kind] = list()

    def update_containers(self, type_instance: CommonTypeData):
        # when type declaration and typedef are combined, clang tool handles type declaration twice  >>  skip one
        if type_instance.name not in [instance.name for instance in self.containers[type_instance.cursor.kind]]:
            self.containers[type_instance.cursor.kind].append(type_instance)

    def generate_output(self, filename: str):
        with open(filename, mode="w") as output:
            self.__class__.write_beginning(output)
            #  write all excluding functions:
            #    must be in the right order of containers
            #    must be in the right order of files (units)
            self.__class__.write_functions(output)
            self.__class__.write_ending(output)

    @staticmethod
    def write_beginning(output):
        pass

    @staticmethod
    def write_functions(output):
        pass

    @staticmethod
    def write_ending(output):
        pass
