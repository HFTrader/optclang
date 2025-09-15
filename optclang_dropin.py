#!/usr/bin/env python3
"""
OptClang Drop-in Replacement Entry Point

This script serves as a drop-in replacement for clang++ or g++.
It can be symlinked or copied as 'clang++' or 'g++' to transparently
use OptClang with existing build systems.

Usage:
    # Direct usage
    python3 optclang_dropin.py source.cpp -o output
    
    # As drop-in replacement
    ln -s /path/to/optclang_dropin.py /usr/local/bin/clang++
    export CXX=/usr/local/bin/clang++
    make  # or any build system
    
Environment Variables:
    OPTCLANG_CXX: Override the underlying compiler (default: clang++)
    OPTCLANG_CONFIG: Path to OptClang configuration file
    OPTCLANG_VERBOSE: Enable verbose output (1/true/yes)
"""

import sys
import os

# Add src directory to Python path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, 'src')
sys.path.insert(0, src_dir)

def main():
    """Main entry point for drop-in replacement functionality."""
    try:
        from optclang.dropin import main_dropin
        return main_dropin()
    except ImportError as e:
        print(f"Error importing OptClang dropin module: {e}", file=sys.stderr)
        print("Make sure OptClang is properly installed.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error in drop-in mode: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
