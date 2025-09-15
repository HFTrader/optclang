# Incremental Configuration Guide

This document explains the new incremental configuration feature in OptClang, which allows you to start with standard optimization levels and make targeted modifications.

## Overview

Instead of specifying every optimization pass manually, you can now:
1. Choose a base optimization level (s, 0, 1, 2, 3)
2. Add or remove specific passes incrementally
3. Let OptClang handle pass ordering and deduplication

## Configuration Format

### Basic Syntax

```yaml
base_optimization: "2"           # Start with O2 optimization
incremental_changes:             # Make specific modifications
  - "-loop-vectorize"           # Remove vectorization
  - "+aggressive-instcombine"   # Add aggressive instruction combining
```

### Base Optimization Levels

| Level | Description | Pass Count | Equivalent |
|-------|-------------|------------|------------|
| `"s"` | Size optimization | 77 passes | `-Os` |
| `"0"` | No optimization | 3 passes | `-O0` |
| `"1"` | Basic optimization | 75 passes | `-O1` |
| `"2"` | Standard optimization | 86 passes | `-O2` |
| `"3"` | Aggressive optimization | 88 passes | `-O3` |

### Incremental Changes Formats

#### Array Format (Recommended)
```yaml
incremental_changes:
  - "-loop-vectorize"           # Remove pass
  - "-slp-vectorizer"           # Remove another pass
  - "+aggressive-instcombine"   # Add pass
  - "+mem2reg"                  # Add another pass
```

#### String Format (Compact)
```yaml
incremental_changes: "+mem2reg,-loop-vectorize,+instcombine,-dce"
```

## How It Works

### Pass Resolution Process

1. **Load Base Passes**: Get the standard pass list for the specified optimization level
2. **Apply Removals**: Remove passes marked with `-` prefix
3. **Apply Additions**: Add passes marked with `+` prefix (if not already present)
4. **Maintain Order**: Preserve the original pass ordering for optimal results

### Smart Handling

- **Duplicate Detection**: Adding a pass that's already present is ignored (no error)
- **Missing Pass Removal**: Removing a non-existent pass is ignored (no error)
- **Order Preservation**: New passes are inserted in optimal positions
- **Validation**: All pass names are validated against available LLVM passes

## Common Use Cases

### 1. Size-Optimized Build with Performance Tweaks

```yaml
# Start with size optimization, add loop unrolling for hot paths
base_optimization: "s"
incremental_changes:
  - "+loop-unroll"
  - "+licm"                     # Loop invariant code motion
```

### 2. O2 Without Vectorization

```yaml
# Standard optimization without vectorization (for debugging)
base_optimization: "2"
incremental_changes:
  - "-loop-vectorize"
  - "-slp-vectorizer"
```

### 3. O3 with Custom Instruction Optimization

```yaml
# Aggressive optimization with enhanced instruction combining
base_optimization: "3"
incremental_changes:
  - "+aggressive-instcombine"
  - "+instcombine"              # Add regular instcombine too (redundant but safe)
```

### 4. Custom O1 with Specific Additions

```yaml
# Basic optimization plus specific advanced passes
base_optimization: "1"
incremental_changes:
  - "+gvn"                      # Global value numbering
  - "+loop-unroll"              # Loop unrolling
  - "+tailcallelim"             # Tail call elimination
```

### 5. Minimal O0 with Essential Optimizations

```yaml
# No optimization base with just memory and basic optimizations
base_optimization: "0"
incremental_changes:
  - "+mem2reg"                  # Memory to register promotion
  - "+instcombine"              # Basic instruction combining
  - "+simplifycfg"              # Control flow graph simplification
```

## Complete Configuration Examples

### Development Configuration
```yaml
# Good for development: fast compilation, some optimization, debugging-friendly
base_optimization: "1"
incremental_changes:
  - "-loop-vectorize"           # Remove vectorization for easier debugging
  - "+mem2reg"                  # Ensure register allocation
  - "+dce"                      # Remove dead code

compiler_flags:
  - "-std=c++20"
  - "-Wall"
  - "-g"                        # Debug symbols

linker_flags:
  - "-lm"
```

### Production Configuration
```yaml
# Optimized for production: aggressive optimization with size considerations
base_optimization: "3"
incremental_changes:
  - "+function-merge"           # Merge identical functions
  - "+constmerge"               # Merge identical constants
  - "-loop-unroll"              # Remove loop unrolling to save code size

compiler_flags:
  - "-std=c++20"
  - "-Wall"
  - "-DNDEBUG"                  # Disable assertions

linker_flags:
  - "-lm"
  - "-s"                        # Strip symbols
```

### Benchmarking Configuration
```yaml
# For performance testing: specific optimization focus
base_optimization: "2"
incremental_changes:
  - "+loop-unroll"              # Aggressive loop unrolling
  - "+licm"                     # Loop invariant code motion
  - "+loop-rotate"              # Loop rotation
  - "-slp-vectorizer"           # Disable SLP vectorization for comparison

compiler_flags:
  - "-std=c++20"
  - "-Wall"
  - "-march=native"             # Optimize for current CPU

linker_flags:
  - "-lm"
```

## Migration from Legacy Format

### Before (Legacy Format)
```yaml
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
```

### After (Incremental Format)
```yaml
base_optimization: "1"          # O1 includes most of these passes
incremental_changes:
  - "+gvn"                      # Add the few missing ones
  - "+loop-unroll"
  - "+adce"
```

## Discovering Pass Information

Use these commands to understand optimization levels and plan your incremental changes:

```bash
# See all available passes
./optclang_cli.py --list-passes

# See what's in each optimization level
./optclang_cli.py --list-O1
./optclang_cli.py --list-O2  
./optclang_cli.py --list-O3

# See incremental differences between levels
./optclang_cli.py --incremental-diff
```

The `--incremental-diff` output shows exactly what changes between optimization levels, making it easy to understand what you might want to add or remove.

## Best Practices

### 1. Start with Standard Levels
Always begin with a standard optimization level (`0`, `1`, `2`, `3`, `s`) that's closest to your needs.

### 2. Make Targeted Changes
Only specify the passes you want to modify. Let the base optimization handle the rest.

### 3. Use Descriptive Comments
```yaml
incremental_changes:
  - "-loop-vectorize"           # Disable for easier debugging
  - "+aggressive-instcombine"   # More aggressive optimization for hot code
```

### 4. Test Incrementally
Start with just the base optimization, then add incremental changes one by one to understand their impact.

### 5. Profile Your Results
Use profiling tools to measure the impact of your incremental changes on performance and code size.

## Troubleshooting

### Invalid Pass Names
If you get "Unknown command line argument" errors, check the pass name:
```bash
# List all available passes to find the correct name
./optclang_cli.py --list-passes | grep vectorize
```

### No Effect from Changes
If your incremental changes don't seem to work:
1. Check if the pass is already in the base optimization level
2. Verify the pass name is correct
3. Use verbose mode (`-v`) to see the resolved pass list

### Performance Regression
If performance gets worse:
1. Try a higher base optimization level first
2. Remove aggressive passes one by one
3. Consider the pass ordering impact

## Advanced Features

### Combining with Legacy Fields
```yaml
base_optimization: "2"
incremental_changes:
  - "+custom-pass"

# Legacy fields still work
cxx_path: "/usr/local/llvm/bin/clang++"
compiler_flags:
  - "-std=c++20"
linker_flags:
  - "-lm"
```

### Multiple Configuration Testing
Create multiple configuration files to test different optimization strategies:
```bash
# Compare different approaches
./optclang_cli.py sample.cpp -c config_o2_base.yaml -o test_o2
./optclang_cli.py sample.cpp -c config_o3_custom.yaml -o test_o3_custom
./optclang_cli.py sample.cpp -c config_size_optimized.yaml -o test_size
```

This incremental configuration system makes it much easier to create custom optimization pipelines while leveraging the battle-tested pass sequences from standard optimization levels.
