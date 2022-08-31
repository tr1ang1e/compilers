from .kinds import Kinds, CommonTypeData
from clang.cindex import CursorKind
from datetime import datetime


class Writer(Kinds):

    def __init__(self):
        self.containers = dict()
        for kind in self.cursorKinds.keys():
            self.containers[kind] = list()

    def update_containers(self, type_instance: CommonTypeData):
        parsed_instances_names = [instance.name for instance in self.containers[type_instance.cursor.kind]]

        # when type declaration and typedef are combined, clang tool handles type declaration twice
        if type_instance.name not in parsed_instances_names:
            self.containers[type_instance.cursor.kind].append(type_instance)

        # must be replaced (not skipped) to cover all possible cases
        else:
            self.containers[type_instance.cursor.kind][parsed_instances_names.index(type_instance.name)] = type_instance

    def generate_output(self, output_file: str, parsed_files: list, prefix: str):
        with open(output_file, mode="w") as wrapper:
            self.write_beginning(wrapper)
            self.write_kinds(wrapper, parsed_files, prefix, [k for k in Kinds.cursorKinds if k != CursorKind.FUNCTION_DECL])
            self.write_functions_class(wrapper, parsed_files, prefix)

    def write_kinds(self, wrapper, parsed_files, prefix, kinds):
        for current in parsed_files:
            wrapper.write("# +----------------------------------------------------------------------+\n")
            wrapper.write("# +    {:<65} +\n".format(current[len(prefix)::]))
            wrapper.write("# +----------------------------------------------------------------------+\n\n")

            for kind, instances in self.containers.items():
                if kind in kinds:
                    from_current = [instance for instance in instances if instance.location == current]
                    for instance in from_current:
                        instance.generate(wrapper)
                    if len(from_current):
                        wrapper.write('\n')

    def write_functions_class(self, wrapper, parsed_files, prefix):
        self.write_function_class_beginning(wrapper)
        self.write_kinds(wrapper, parsed_files, prefix, [CursorKind.FUNCTION_DECL])
        self.write_function_class_ending(wrapper)

    @staticmethod
    def write_beginning(wrapper):
        wrapper.write("#!/usr/bin/python3\n")
        wrapper.write("import platform\n")
        wrapper.write("from ctypes import *\n\n")
        wrapper.write("this = c_void_p  # to use when structure has pointer to itself as it's field \n\n")

    @staticmethod
    def write_function_class_beginning(wrapper):
        wrapper.write("\n")
        wrapper.write("# +----------------------------------------------------------------------+\n")
        wrapper.write("# +    {:<65} +\n".format("Functions class"))
        wrapper.write("# +----------------------------------------------------------------------+\n")
        wrapper.write("""
class Class(object):
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if Class._instance is None:
            Class._instance = object.__new__(cls)
        return Class._instance 
    
    def __init__(self, libpath=None): 
        if Class._initialized: 
            pass 
        else: 
            if libpath is None: 
                is_linux = lambda: True if platform.system() == "Linux" else False 
                libpath = "./library.{0}".format("so" if is_linux() else "dll") 
            lib = cdll.LoadLibrary(libpath)
            
""")

    @staticmethod
    def write_function_class_ending(wrapper):
        generated = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        wrapper.write("""
            # init
            
            version = ...
            print('+---------------------------------------------------------------+')
            print('Py Wrapper: ...                                                  ')
            print('+---------------------------------------------------------------+')

            status = True  # replace with appropriate init() 
            if not status:
                raise Exception("Failed to init '...' library") 

            self._instance._initialized = True

    @staticmethod 
    def get_version():
""")
        wrapper.write('        return "{}" \n'.format(generated))
