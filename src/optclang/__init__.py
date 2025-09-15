"""
OptClang: A tool for compiling C++ files with custom LLVM optimization passes.
"""

__version__ = "1.1.0"

from .main import main
from .compiler import CppCompiler
from .config_parser import ConfigParser
from .llvm_tools import LLVMTools

__all__ = [
    'main',
    'CppCompiler', 
    'ConfigParser',
    'LLVMTools'
]
