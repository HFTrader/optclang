"""
OptClang - A Python tool for compiling C++ files with custom LLVM optimization passes.
"""

__version__ = "0.1.0"
__author__ = "Your Name"

from .compiler import CppCompiler
from .config_parser import ConfigParser
from .llvm_tools import LLVMTools

__all__ = ["CppCompiler", "ConfigParser", "LLVMTools"]
