#!/usr/bin/python3
import platform
from ctypes import *

# +----------------------------------------+
# +    ../test/source.c                    +
# +----------------------------------------+

# _typedefs_ = 
function_p = CFUNCTYPE(c_void_p, POINTER(POINTER(c_int32)), c_char) 
char_pp = POINTER(c_char_p) 
EnumTypedefAlias = c_int # enum EnumTypedefUnderlying 
StructTypedefAlias = "struct StructTypedefUnderlying" 

# _macros_ = 
LINMAC = "linux" 
NOTWINMAC = "notwin" 
MACRO_INT = c_int(42) 

# enum EnumNotTypedef 
ZERO = c_int(0) 
ONE = c_int(1) 
BY_MACRO_INT = c_int(42) 

# EnumTypedefAlias 
NEGATIVE = c_int(-1) 
FOUR = c_int(4) 
FIVE = c_int(5) 

class struct_XXX(Structure):
    _fields_ = [
		("i", c_int32)]

class struct_StructNotTypedef(Structure):
    _fields_ = [
		("void_nop", c_void_p),
		("void_p", c_void_p),
		("void_pp", POINTER(c_void_p)),
		("u8", c_uint8),
		("s16", c_int16),
		("sizet", c_size_t),
		("arraySizeFromHeaderMacro", c_int32 * 123),
		("arrayPointerPointer", POINTER(POINTER(c_int32)) * 42),
		("char_nop", c_char),
		("char_p", c_char_p),
		("char_pp", POINTER(c_char_p)),
		("without_c", c_int32),
		("without_v", c_int32),
		("without_cv", c_int32),
		("xxx", struct XXX),
		("struct_notypedef", c_void_p),
		("struct_typedef", StructTypedefAlias),
		("enum_notypedef", c_void_p),
		("enum_typedef", EnumTypedefAlias),
		("struct_nogeneratedHeader", c_void_p)]

class StructTypedefAlias(Structure):
    _fields_ = [
		("structField", c_void_p)]

# +----------------------------------------+
# +    Functions class                     +
# +----------------------------------------+

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

			self.function_declaraion = lib.function_declaraion
			self.function_declaraion.restype = c_void_p
			self.function_declaraion.argtypes = [c_size_t]

			self.function_definition = lib.function_definition
			self.function_definition.restype = c_void_p
			self.function_definition.argtypes = [POINTER(c_int32), c_int32]
