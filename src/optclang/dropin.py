"""
Drop-in replacement mode for OptClang.
This allows OptClang to be used as a replacement for clang++/g++ via CXX environment variable.
"""

import os
import sys
import argparse
import tempfile
from pathlib import Path
from typing import List, Optional

from .compiler import CppCompiler
from .config_parser import ConfigParser
from .llvm_tools import LLVMTools


class DropinCompiler:
    """Drop-in replacement compiler that mimics clang++/g++ interface."""
    
    def __init__(self):
        self.verbose = False
        self.config = None
        self.optimization_level = None
        
    def parse_compiler_args(self, args: List[str]) -> dict:
        """Parse standard compiler arguments and extract relevant information."""
        parsed = {
            'source_files': [],
            'output_file': None,
            'compile_only': False,
            'optimization_level': None,
            'include_dirs': [],
            'library_dirs': [],
            'libraries': [],
            'defines': [],
            'compiler_flags': [],
            'linker_flags': [],
            'standard': None,
            'debug': False,
            'warnings': [],
            'position_independent': False,
            'static': False,
            'shared': False,
            'strip_symbols': False,
            'march': None,
            'mtune': None,
            'other_flags': []
        }
        
        i = 0
        while i < len(args):
            arg = args[i]
            
            # Source files (C++ extensions)
            if arg.endswith(('.cpp', '.cxx', '.cc', '.C', '.c++', '.CPP')):
                parsed['source_files'].append(arg)
            
            # Output file
            elif arg == '-o' and i + 1 < len(args):
                parsed['output_file'] = args[i + 1]
                i += 1
            
            # Compile only (no linking)
            elif arg == '-c':
                parsed['compile_only'] = True
            
            # Optimization levels
            elif arg in ['-O0', '-O1', '-O2', '-O3', '-Os', '-Ofast', '-Og']:
                parsed['optimization_level'] = arg[2:]  # Remove -O prefix
                if arg == '-Ofast':
                    parsed['optimization_level'] = '3'  # Treat as O3
                elif arg == '-Og':
                    parsed['optimization_level'] = '1'  # Treat as O1
            
            # Debug information
            elif arg in ['-g', '-g1', '-g2', '-g3']:
                parsed['debug'] = True
                parsed['compiler_flags'].append(arg)
            
            # C++ standard
            elif arg.startswith('-std='):
                parsed['standard'] = arg
                parsed['compiler_flags'].append(arg)
            
            # Include directories
            elif arg == '-I' and i + 1 < len(args):
                parsed['include_dirs'].append(args[i + 1])
                parsed['compiler_flags'].extend([arg, args[i + 1]])
                i += 1
            elif arg.startswith('-I'):
                parsed['include_dirs'].append(arg[2:])
                parsed['compiler_flags'].append(arg)
            
            # Library directories
            elif arg == '-L' and i + 1 < len(args):
                parsed['library_dirs'].append(args[i + 1])
                parsed['linker_flags'].extend([arg, args[i + 1]])
                i += 1
            elif arg.startswith('-L'):
                parsed['library_dirs'].append(arg[2:])
                parsed['linker_flags'].append(arg)
            
            # Libraries
            elif arg == '-l' and i + 1 < len(args):
                parsed['libraries'].append(args[i + 1])
                parsed['linker_flags'].extend([arg, args[i + 1]])
                i += 1
            elif arg.startswith('-l'):
                parsed['libraries'].append(arg[2:])
                parsed['linker_flags'].append(arg)
            
            # Defines
            elif arg == '-D' and i + 1 < len(args):
                parsed['defines'].append(args[i + 1])
                parsed['compiler_flags'].extend([arg, args[i + 1]])
                i += 1
            elif arg.startswith('-D'):
                parsed['defines'].append(arg[2:])
                parsed['compiler_flags'].append(arg)
            
            # Warning flags
            elif arg.startswith('-W'):
                parsed['warnings'].append(arg)
                parsed['compiler_flags'].append(arg)
            
            # Position independent code
            elif arg in ['-fPIC', '-fpic']:
                parsed['position_independent'] = True
                parsed['compiler_flags'].append(arg)
            
            # Static/shared linking
            elif arg == '-static':
                parsed['static'] = True
                parsed['linker_flags'].append(arg)
            elif arg == '-shared':
                parsed['shared'] = True
                parsed['linker_flags'].append(arg)
            
            # Strip symbols
            elif arg == '-s':
                parsed['strip_symbols'] = True
                parsed['linker_flags'].append(arg)
            
            # Architecture flags
            elif arg.startswith('-march='):
                parsed['march'] = arg[7:]
                parsed['compiler_flags'].append(arg)
            elif arg.startswith('-mtune='):
                parsed['mtune'] = arg[7:]
                parsed['compiler_flags'].append(arg)
            
            # Verbose output
            elif arg == '-v':
                self.verbose = True
                parsed['compiler_flags'].append(arg)
            
            # Other flags we want to preserve
            elif arg.startswith('-'):
                parsed['other_flags'].append(arg)
                # Decide whether it's a compiler or linker flag
                if arg in ['-pthread', '-fopenmp', '-ffast-math', '-funroll-loops',
                          '-fno-exceptions', '-fno-rtti', '-fomit-frame-pointer']:
                    parsed['compiler_flags'].append(arg)
                else:
                    parsed['other_flags'].append(arg)
            
            # Non-flag arguments (probably source files or object files)
            else:
                if arg.endswith(('.o', '.a', '.so')):
                    parsed['linker_flags'].append(arg)
                else:
                    parsed['other_flags'].append(arg)
            
            i += 1
        
        return parsed
    
    def load_optclang_config(self) -> Optional[dict]:
        """Load OptClang configuration from environment or config file."""
        # Check for config file path in environment
        config_path = os.environ.get('OPTCLANG_CONFIG')
        if config_path and Path(config_path).exists():
            try:
                config_parser = ConfigParser()
                return config_parser.parse(Path(config_path))
            except Exception as e:
                if self.verbose:
                    print(f"Warning: Failed to load OptClang config from {config_path}: {e}", file=sys.stderr)
        
        # Look for config file in current directory
        for config_name in ['optclang.yaml', 'optclang.yml', '.optclang.yaml', '.optclang.yml']:
            config_file = Path(config_name)
            if config_file.exists():
                try:
                    config_parser = ConfigParser()
                    return config_parser.parse(config_file)
                except Exception as e:
                    if self.verbose:
                        print(f"Warning: Failed to load config from {config_file}: {e}", file=sys.stderr)
        
        # No config found, return None
        return None
    
    def create_optclang_config(self, parsed_args: dict) -> dict:
        """Create OptClang configuration from parsed arguments."""
        config = {
            'compiler_flags': parsed_args['compiler_flags'],
            'linker_flags': parsed_args['linker_flags']
        }
        
        # Override compiler if specified
        cxx_compiler = os.environ.get('OPTCLANG_CXX')
        if cxx_compiler:
            # Validate that the compiler can work with LLVM IR
            if 'g++' in cxx_compiler and 'clang' not in cxx_compiler:
                if self.verbose:
                    print(f"Warning: {cxx_compiler} may not work well with LLVM IR. Consider using clang++", file=sys.stderr)
                    print("Falling back to default clang++ for LLVM IR generation", file=sys.stderr)
            else:
                config['cxx_path'] = cxx_compiler
        
        # Load OptClang configuration if available
        optclang_config = self.load_optclang_config()
        if optclang_config:
            # Merge with loaded config
            config.update(optclang_config)
            # But preserve command-line flags
            if 'compiler_flags' in optclang_config:
                config['compiler_flags'] = list(optclang_config['compiler_flags']) + parsed_args['compiler_flags']
            if 'linker_flags' in optclang_config:
                config['linker_flags'] = list(optclang_config['linker_flags']) + parsed_args['linker_flags']
        else:
            # Create default incremental config based on optimization level
            if parsed_args['optimization_level']:
                config['base_optimization'] = parsed_args['optimization_level']
                config['incremental_changes'] = []
            else:
                # Default to basic optimization passes if no -O flag specified
                config['optimization_passes'] = ['mem2reg', 'instcombine', 'simplifycfg']
        
        return config
    
    def compile_files(self, source_files: List[str], parsed_args: dict) -> bool:
        """Compile source files using OptClang."""
        config = self.create_optclang_config(parsed_args)
        
        if self.verbose:
            print(f"OptClang drop-in mode: compiling {len(source_files)} files")
            if 'base_optimization' in config:
                print(f"Using base optimization level: {config['base_optimization']}")
            elif 'optimization_passes' in config:
                print(f"Using {len(config['optimization_passes'])} optimization passes")
        
        # Handle single file compilation
        if len(source_files) == 1:
            source_file = Path(source_files[0])
            output_file = parsed_args['output_file']
            
            if not output_file:
                if parsed_args['compile_only']:
                    # For -c flag, output .o file
                    output_file = source_file.with_suffix('.o').name
                else:
                    # For linking, default to 'a.out'
                    output_file = 'a.out'
            
            compiler = CppCompiler(config, verbose=self.verbose)
            return compiler.compile(source_file, output_file)
        
        # Handle multiple file compilation (not yet implemented)
        else:
            print("Error: Multiple file compilation not yet supported in drop-in mode", file=sys.stderr)
            return False
    
    def run(self, args: List[str]) -> int:
        """Main entry point for drop-in compiler."""
        if not args:
            print("Error: No arguments provided", file=sys.stderr)
            return 1
        
        try:
            parsed_args = self.parse_compiler_args(args)
            
            if not parsed_args['source_files']:
                # No source files, might be a query operation
                # For now, just pass through to the real compiler
                cxx_compiler = os.environ.get('OPTCLANG_CXX') or 'clang++'
                import subprocess
                try:
                    result = subprocess.run([cxx_compiler] + args, check=False)
                    return result.returncode
                except FileNotFoundError:
                    print(f"Error: Compiler '{cxx_compiler}' not found", file=sys.stderr)
                    return 1
            
            # Compile using OptClang
            success = self.compile_files(parsed_args['source_files'], parsed_args)
            return 0 if success else 1
            
        except Exception as e:
            print(f"OptClang error: {e}", file=sys.stderr)
            if self.verbose:
                import traceback
                traceback.print_exc()
            return 1


def main_dropin(args: List[str] = None) -> int:
    """Main entry point for drop-in replacement mode."""
    if args is None:
        args = sys.argv[1:]
    
    compiler = DropinCompiler()
    return compiler.run(args)


if __name__ == "__main__":
    sys.exit(main_dropin())
