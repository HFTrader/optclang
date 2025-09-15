# OptClang Drop-In Replacement

OptClang can now be used as a drop-in replacement for `clang++` or `g++` in existing build systems, Makefiles, and development workflows.

## Quick Start

### Method 1: Direct Script Usage
```bash
# Use the drop-in script directly
./optclang_dropin.py source.cpp -o output
./optclang_dropin.py source.cpp -O2 -std=c++17
```

### Method 2: Symbolic Links
```bash
# Create symbolic links
ln -sf /path/to/optclang_dropin.py /usr/local/bin/clang++
ln -sf /path/to/optclang_dropin.py /usr/local/bin/g++

# Use as normal compiler
clang++ source.cpp -o output
g++ source.cpp -O3 -std=c++20
```

### Method 3: Environment Variable Override
```bash
# In Makefiles or build systems
export CXX=/path/to/optclang_dropin.py
make

# Or directly
CXX=./optclang_dropin.py make
```

## Configuration

### Environment Variables

- **OPTCLANG_CONFIG**: Path to OptClang configuration file
- **OPTCLANG_CXX**: Override the underlying compiler (default: clang++)
- **OPTCLANG_VERBOSE**: Enable verbose output (1/true/yes)

### Examples

```bash
# Use custom config file
OPTCLANG_CONFIG=my_optimizations.yaml clang++ source.cpp -o output

# Override underlying compiler (for clang-compatible compilers only)
OPTCLANG_CXX=/usr/bin/clang++-15 clang++ source.cpp -o output

# Enable verbose output to see optimization details
OPTCLANG_VERBOSE=1 clang++ source.cpp -o output -v
```

## Supported Compiler Arguments

OptClang's drop-in mode supports most standard compiler arguments:

- **Optimization**: `-O0`, `-O1`, `-O2`, `-O3`, `-Os`, `-Oz`
- **Standards**: `-std=c++11`, `-std=c++14`, `-std=c++17`, `-std=c++20`, `-std=c++23`
- **Output**: `-o output_file`, `-c` (compile only)
- **Include paths**: `-I/path/to/headers`, `-I /path/to/headers`
- **Library paths**: `-L/path/to/libs`, `-L /path/to/libs`
- **Libraries**: `-lmath`, `-l math`
- **Defines**: `-DDEBUG`, `-D DEBUG=1`
- **Warnings**: `-Wall`, `-Wextra`, `-Werror`
- **Debug info**: `-g`, `-g0`, `-g1`, `-g2`, `-g3`
- **Position independent code**: `-fPIC`, `-fpic`

## Configuration Files

When no `OPTCLANG_CONFIG` is specified, OptClang will look for configuration files in this order:

1. `optclang.yaml`
2. `optclang.yml`
3. `.optclang.yaml`
4. `.optclang.yml`

If no configuration file is found, OptClang will use sensible defaults based on the optimization level specified with `-O` flags.

## Build System Integration

### Makefile
```makefile
CXX = /path/to/optclang_dropin.py
CXXFLAGS = -O2 -std=c++17

my_program: source.cpp
	$(CXX) $(CXXFLAGS) $< -o $@
```

### CMake
```cmake
set(CMAKE_CXX_COMPILER "/path/to/optclang_dropin.py")
```

### Environment Setup
```bash
# Add to your .bashrc or .zshrc for permanent setup
export CXX=/path/to/optclang_dropin.py
export OPTCLANG_CONFIG=/path/to/my_config.yaml
```

## Limitations

- **Multiple file compilation**: Currently supports single source file compilation
- **Non-clang compilers**: When using `OPTCLANG_CXX` with `g++`, LLVM IR generation may not work properly
- **Link-only operations**: Operations that only link object files are not yet supported

## Examples

See the `examples/` directory for various configuration files that can be used with the drop-in mode:

- `basic_config.yaml`: Basic optimization passes
- `o3_custom.yaml`: O3-based configuration with custom modifications
- `incremental_config.yaml`: Incremental optimization configuration
- `size_opt_config.yaml`: Size optimization focused configuration
