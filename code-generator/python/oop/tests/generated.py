#!/usr/bin/python3
import platform
from ctypes import *

this = c_void_p  # to use when structure has pointer to itself as it's field 

# +----------------------------------------------------------------------+
# +    samples/include/header.h                                          +
# +----------------------------------------------------------------------+


HEADER_DEFINE_test = "header_define_test" 
MACRO_INT1_test = c_int(42) 
MACRO_INT2_test = c_int(123) 
MACRO_STR_test = "string" 

# +----------------------------------------------------------------------+
# +    samples/source.c                                                  +
# +----------------------------------------------------------------------+

IncompleteHandler_test = c_void_p 
EnumAlias_test = c_int 
callback_test = CFUNCTYPE(c_int32, c_int32, c_int32) 
S_handler = POINTER(struct_S_test) 
T_handler = POINTER(struct_T) 
Q_handler = POINTER(Q_alias) 

SOURCE_DEFINE_test = "source_define_test" 


# EnumAlias_test
ZERO = c_int(0)
ONE = c_int(1)

# enum EnumWithoutTypedef_test
NEGATIVE = c_int(-1)
MACRO = c_int(42)



class Typedef_IncompleteStruct_test(Structure):  # incomplete type, pointers to type replaced with 'c_void_p'
    _fields_ = [
    ]


class S_callback_test(Structure):  
    _fields_ = [
        ("function", callback_test),
    ]


class struct_S_test(Structure):  
    _fields_ = [
        ("array", c_int32 * 123),
        ("c", c_char),
        ("self", POINTER(this)),
        ("self_handler", POINTER(this)),
    ]


class struct_T(Structure):  
    _fields_ = [
        ("t", this),
    ]


class P_alias(Structure):  
    _fields_ = [
        ("p", this),
    ]


class Q_alias(Structure):  
    _fields_ = [
        ("q", POINTER(this)),
    ]


# +----------------------------------------------------------------------+
# +    Functions class                                                   +
# +----------------------------------------------------------------------+

class VlnsAPhySdk(object):
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if VlnsAPhySdk._instance is None:
            VlnsAPhySdk._instance = object.__new__(cls)
        return VlnsAPhySdk._instance 
    
    def __init__(self, libpath=None): 
        if VlnsAPhySdk._initialized: 
            pass 
        else: 
            if libpath is None: 
                is_linux = lambda: True if platform.system() == "Linux" else False 
                libpath = "./libvalens_aphy.{0}".format("so" if is_linux() else "dll") 
            lib = cdll.LoadLibrary(libpath)
            
# +----------------------------------------------------------------------+
# +    samples/include/header.h                                          +
# +----------------------------------------------------------------------+

# +----------------------------------------------------------------------+
# +    samples/source.c                                                  +
# +----------------------------------------------------------------------+

            self.FunctionEmpty_test = lib.FunctionEmpty_test
            self.FunctionEmpty_test.restype = c_void_p
            self.FunctionEmpty_test.argtypes = []

            self.FunctionDefault_test = lib.FunctionDefault_test
            self.FunctionDefault_test.restype = c_int32
            self.FunctionDefault_test.argtypes = [POINTER(c_int32), POINTER(c_char_p)]

            self.FunctionAliases_test = lib.FunctionAliases_test
            self.FunctionAliases_test.restype = EnumAlias_test
            self.FunctionAliases_test.argtypes = [POINTER(POINTER(Typedef_IncompleteStruct_test))]

            self.FunctionUnknownEnum_test = lib.FunctionUnknownEnum_test
            self.FunctionUnknownEnum_test.restype = c_void_p
            self.FunctionUnknownEnum_test.argtypes = [POINTER(c_int)]

            self.FunctionUnknownStruct_test = lib.FunctionUnknownStruct_test
            self.FunctionUnknownStruct_test.restype = c_void_p
            self.FunctionUnknownStruct_test.argtypes = [POINTER(struct_S_test)]



            # init

            sdk_version = self.aphy_sdk_version()
            print('*****************************************************************')
            print('Py Wrapper: {0} [APhySdk: {1}]'.format(VlnsAPhySdk.get_version(), sdk_version.versionString))
            print('*****************************************************************')

            status = self.valens_aphy_init(True)
            if not status:
                raise Exception("Failed to init 'valens_aphy' library") 

            VlnsAPhySdk._initialized = True

    @staticmethod 
    def get_version():
        return "01.08.2022 15:54:12" 
