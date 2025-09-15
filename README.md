# OptClang

A Python 3 tool for compiling C++ files with custom LLVM optimization passes.

## Features

- **Drop-In Replacement**: Use as a transparent replacement for clang++ or g++ in existing build systems
- **Incremental Configuration**: Start with standard optimization levels (O0, O1, O2, O3, Os) and make targeted modifications
- **Legacy Configuration**: Full control with explicit optimization pass lists
- **Pass Discovery**: Comprehensive tools to explore and understand LLVM optimization passes
- **LLVM Integration**: Automatic LLVM tool detection with CXX environment variable support
- **Flexible Configuration**: YAML-based configuration with support for both incremental and legacy formats
- **Robust Compilation**: Multi-stage compilation pipeline (C++ → LLVM IR → Optimized IR → Executable)

## Quick Start

### Drop-In Replacement Mode
```bash
# Use as direct replacement for clang++
./optclang_dropin.py source.cpp -o output -O2

# Create symlinks for transparent replacement
ln -sf /path/to/optclang_dropin.py /usr/local/bin/clang++
export CXX=/usr/local/bin/clang++
make  # Works with any build system

# Use with custom configuration
OPTCLANG_CONFIG=my_config.yaml clang++ source.cpp -o output
```

### Standalone Mode
```bash
# Install dependencies
./setup.sh

# List all available optimization passes
./optclang_cli.py --list-passes

# See incremental differences between optimization levels  
./optclang_cli.py --incremental-diff

# Compile with incremental configuration (O2 base + custom tweaks)
./optclang_cli.py examples/sample.cpp -c examples/incremental_config.yaml -o optimized_sample

# Compile with legacy configuration (explicit pass list)
./optclang_cli.py examples/sample.cpp -c examples/basic_config.yaml -o basic_sample
```

## Requirements

- Python 3.8 or higher
- LLVM/Clang toolchain
- PyYAML

## Installation

### Quick Setup

```bash
# Clone or download the project
cd optclang

# Run the setup script
./setup.sh
```

### Manual Installation

```bash
# Install dependencies
pip3 install -r requirements.txt

# Run tests to verify installation
PYTHONPATH=src python3 -m pytest tests/ -v
```

## Usage

### Drop-In Replacement Mode

OptClang can transparently replace `clang++` or `g++` in existing build systems:

```bash
# Direct usage as compiler replacement
./optclang_dropin.py source.cpp -o output -O2 -std=c++17

# Create symbolic links for system-wide usage
sudo ln -sf /path/to/optclang_dropin.py /usr/local/bin/clang++
export CXX=clang++

# Use with make, cmake, or any build system
make clean && make

# Configure with environment variables
OPTCLANG_CONFIG=examples/o3_custom.yaml make
OPTCLANG_VERBOSE=1 make  # Enable verbose output
```

For detailed drop-in usage instructions, see [docs/dropin-replacement-guide.md](docs/dropin-replacement-guide.md).

### Command Line

```bash
# List all available optimization passes
./optclang_cli.py --list-passes

# List passes used in standard optimization levels
./optclang_cli.py --list-O1
./optclang_cli.py --list-O2
./optclang_cli.py --list-O3

# Show incremental differences between optimization levels
./optclang_cli.py --incremental-diff

# Basic compilation with output filename
./optclang_cli.py examples/sample.cpp -c examples/basic_config.yaml -o optimized_sample

# Compilation with output directory (automatically uses input filename stem)
./optclang_cli.py examples/sample.cpp -c examples/basic_config.yaml --output-dir ./build

# Multiple files to the same directory
./optclang_cli.py examples/sample.cpp -c examples/basic_config.yaml --output-dir ./dist
./optclang_cli.py examples/my_program.cpp -c examples/advanced_config.yaml --output-dir ./dist

# Direct module execution
python3 src/optclang/main.py examples/sample.cpp -c examples/basic_config.yaml -o optimized_sample

# As a Python module
PYTHONPATH=src python3 -m optclang.main examples/sample.cpp -c examples/basic_config.yaml -o optimized_sample

# With custom LLVM installation
CXX=/usr/local/llvm/bin/clang++ ./optclang_cli.py examples/sample.cpp -c examples/advanced_config.yaml -o advanced_sample

# Verbose output
./optclang_cli.py examples/sample.cpp -c examples/basic_config.yaml -v
```

### Output Options

OptClang provides flexible output options to suit different workflows:

#### Explicit Output Filename (`-o, --output`)
```bash
# Specify exact output filename
./optclang_cli.py source.cpp -c config.yaml -o my_program
./optclang_cli.py source.cpp -c config.yaml -o /path/to/executable
```

#### Output Directory (`--output-dir`)
```bash
# Place executable in specific directory (uses input filename stem)
./optclang_cli.py examples/sample.cpp -c config.yaml --output-dir ./build
# Creates: ./build/sample

./optclang_cli.py examples/my_program.cpp -c config.yaml --output-dir ./dist
# Creates: ./dist/my_program

# Directory is created automatically if it doesn't exist
./optclang_cli.py source.cpp -c config.yaml --output-dir ./new/nested/dir
```

#### Default Behavior
```bash
# No output option - uses input filename stem in current directory
./optclang_cli.py examples/sample.cpp -c config.yaml
# Creates: ./sample
```

**Note**: The `--output` and `--output-dir` options are mutually exclusive.

### As a script

```bash
# Make the main script executable
chmod +x src/optclang/main.py

# Run directly (requires PYTHONPATH)
PYTHONPATH=src ./src/optclang/main.py examples/sample.cpp -c examples/basic_config.yaml -o optimized_sample

# Or use the provided CLI script
./optclang_cli.py examples/sample.cpp -c examples/basic_config.yaml -o optimized_sample
```

### Configuration File Formats

OptClang supports two configuration formats: **legacy full pass lists** and **new incremental configurations**.

#### Incremental Configuration (Recommended)

Start with a base optimization level and apply incremental changes:

```yaml
# Incremental configuration - Start with O2, then customize
base_optimization: "2"
incremental_changes:
  - "-loop-vectorize"         # Remove vectorization
  - "-slp-vectorizer"         # Remove SLP vectorization  
  - "+aggressive-instcombine" # Add aggressive instruction combining

compiler_flags:
  - "-std=c++20"
  - "-Wall"

linker_flags:
  - "-lm"
```

**Base optimization levels:**
- `"s"` - Size optimization (77 passes, equivalent to `-Os`)
- `"0"` - No optimization (3 basic passes, equivalent to `-O0`)
- `"1"` - Basic optimization (75 passes, equivalent to `-O1`)
- `"2"` - Standard optimization (86 passes, equivalent to `-O2`)
- `"3"` - Aggressive optimization (88 passes, equivalent to `-O3`)

**Incremental changes formats:**
```yaml
# Array format (recommended for readability)
incremental_changes:
  - "-loop-vectorize"
  - "+aggressive-instcombine"
  - "-slp-vectorizer"

# Or string format (compact)
incremental_changes: "+mem2reg,-dce,+instcombine"
```

#### Legacy Full Pass List Configuration

Specify the complete list of optimization passes:

```yaml
# Legacy configuration - Full pass list
optimization_passes:
  - mem2reg
  - instcombine
  - simplifycfg
  - dce

compiler_flags:
  - "-std=c++17"
  - "-Wall"
  - "-Wextra"

linker_flags:
  - "-lm"
```

```yaml
# Advanced legacy configuration with custom LLVM path
cxx_path: "/usr/local/llvm/bin/clang++"

optimization_passes:
  - mem2reg
  - sroa
  - instcombine
  - simplifycfg
  - reassociate
  - gvn
  - dce
  - adce
  - loop-unroll
  - licm

compiler_flags:
  - "-std=c++20"
  - "-Wall"
  - "-Wextra"
  - "-O0"  # Start with no built-in optimization

linker_flags:
  - "-lm"
  - "-lpthread"
```

## Configuration Options

### Incremental Configuration Options
- `base_optimization`: Base optimization level (`"s"`, `"0"`, `"1"`, `"2"`, or `"3"`)
- `incremental_changes`: List or string of pass modifications (`"+pass"` to add, `"-pass"` to remove)
- `compiler_flags`: Additional flags for the compilation step
- `linker_flags`: Additional flags for the linking step
- `cxx_path`: Path to clang++ compiler (overrides CXX environment variable)

### Legacy Configuration Options
- `optimization_passes`: List of LLVM optimization passes to apply
- `compiler_flags`: Additional flags for the compilation step
- `linker_flags`: Additional flags for the linking step
- `cxx_path`: Path to clang++ compiler (overrides CXX environment variable)

### Configuration Benefits

**Incremental configuration advantages:**
- **Intuitive**: Start with known optimization levels (O0, O1, O2, O3, Os)
- **Maintainable**: Only specify what you want to change
- **Robust**: Automatically handles duplicates and missing passes
- **Flexible**: Mix and match optimizations from different levels

**Legacy configuration advantages:**
- **Explicit**: Full control over the exact pass sequence
- **Deterministic**: Same results regardless of LLVM version differences
- **Educational**: See exactly which passes are being applied

## Discovering Optimization Passes

To see all available optimization passes for your LLVM installation:

```bash
./optclang_cli.py --list-passes
```

To see which passes are used in standard optimization levels:

```bash
# List passes used in -O1
./optclang_cli.py --list-O1

# List passes used in -O2  
./optclang_cli.py --list-O2

# List passes used in -O3
./optclang_cli.py --list-O3
```

To see incremental differences between optimization levels:

```bash
# Show what passes are added/removed between O0→O1, O1→O2, O2→O3
./optclang_cli.py --incremental-diff
```

These commands will display:
- A numbered list of optimization passes
- Example configuration file snippet
- Equivalent clang++ optimization level
- **Incremental changes**: One-line comma-separated lists of added/removed passes

The incremental diff shows exactly what changes between optimization levels:
- **O0 to O1**: Adds ~64 basic optimization passes
- **O1 to O2**: Adds ~12 passes (vectorization, advanced opts), removes 1
- **O2 to O3**: Adds ~3 aggressive optimization passes

This helps you understand what optimizations are applied at each level and lets you create custom optimization pipelines based on standard levels.

Common optimization passes include:
- `mem2reg`: Promote memory to register
- `instcombine`: Combine redundant instructions
- `simplifycfg`: Simplify the control flow graph
- `dce`: Dead code elimination
- `gvn`: Global value numbering
- `sroa`: Scalar replacement of aggregates
- `licm`: Loop invariant code motion
- `loop-unroll`: Unroll loops

## Environment Variables

- `CXX`: Path to the C++ compiler (default: `clang++`)

## Testing

Run the test suite with pytest:

```bash
# Quick test with setup script
./setup.sh

# Manual testing
PYTHONPATH=src python3 -m pytest tests/

# Run tests with verbose output
PYTHONPATH=src python3 -m pytest -v tests/
```

## Examples

The `examples/` directory contains sample configurations:

### Incremental Configuration Examples
- `incremental_config.yaml`: O2 base with vectorization removed and aggressive instcombine added
- `size_opt_config.yaml`: Size optimization base with loop unrolling and custom dead code elimination
- `o3_custom.yaml`: O3 base with vectorization disabled
- `o0_basic.yaml`: O0 base with basic memory and instruction optimizations added

### Legacy Configuration Examples  
- `basic_config.yaml`: Basic optimization configuration with essential passes
- `advanced_config.yaml`: Advanced optimization with custom LLVM path and comprehensive passes

### Test Program
- `sample.cpp`: Example C++ source file for testing (vector operations, loops, function calls)

## How It Works

1. **IR Generation**: Compiles C++ source to LLVM IR using `clang++ -S -emit-llvm`
2. **Optimization**: Applies specified optimization passes using `opt`
3. **Executable Generation**: Compiles optimized IR to executable using `clang++`

## License

MIT License
