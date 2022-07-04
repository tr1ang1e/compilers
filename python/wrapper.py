#!/usr/bin/python3
import platform
from ctypes import *

# +----------------------------------------+
# +    ../examples/include/header.h        +
# +----------------------------------------+

# _typedefs_ = 
UnknownType = POINTER(c_char_p) 
Name = "struct NameS" 

# _macros_ = 
INITIALIZE = c_int(123) 

class Name(Structure):
    _fields_ = [
		("field", c_int32)]

# +----------------------------------------+
# +    ../examples/unit.c                  +
# +----------------------------------------+

# _typedefs_ = 
TEnum2 = c_int # enum Enum2 
function = CFUNCTYPE(c_void_p, POINTER(UnknownType), POINTER(POINTER(c_int32)), c_char) 
TStruct2 = "struct Struct2" 

# _macros_ = 
LINMAC = "linux" 
MACROINT = c_int(42) 
MACROSTR = "stringmacro" 

# enum Enum1 
ZERO = c_int(0) 
ONE = c_int(1) 
TWO = c_int(42) 

# TEnum2 
THREE = c_int(-1) 
FOUR = c_int(4) 
FIVE = c_int(5) 

class struct_TEST(Structure):
    _fields_ = [
		("u8t", c_uint8)]

class struct_Struct1(Structure):
    _fields_ = [
		("voidnoptr", c_void_p),
		("voidptr", c_void_p),
		("voiddoubleptr", POINTER(c_void_p)),
		("u8t", c_uint8),
		("keys", POINTER(c_char_p)),
		("next", POINTER(Name)),
		("header2", c_void_p),
		("arr", c_int32 * 123),
		("inarr", POINTER(POINTER(c_int32)) * 111),
		("field", UnknownType),
		("xy", c_size_t),
		("ij", c_uint16)]

class TStruct2(Structure):
    _fields_ = [
		("anotherint", c_int32),
		("funct", function)]

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

			self.funct_delaration = lib.funct_delaration
			self.funct_delaration.restype = c_int32
			self.funct_delaration.argtypes = [c_int32]

			self.function1 = lib.function1
			self.function1.restype = c_void_p
			self.function1.argtypes = [POINTER(UnknownType), function]

			self.function2 = lib.function2
			self.function2.restype = c_int32
			self.function2.argtypes = [c_int32, POINTER(c_char_p)]
