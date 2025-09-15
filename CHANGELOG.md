# Changelog

All notable changes to OptClang will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

# Changelog

All notable changes to OptClang will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Output Directory Support**: New `--output-dir` option for flexible output management
  - Automatically uses input filename stem when placing files in directory
  - Creates output directory if it doesn't exist
  - Mutually exclusive with `-o/--output` option
  - Enhanced error handling for invalid directory paths
- **LLVM 19+ Compatibility**: Full support for LLVM 19.1.6 and new pass manager
  - Automatic detection of new vs legacy pass manager
  - Graceful fallback for incremental configurations with new pass manager
  - Maintains backward compatibility with older LLVM versions

### Improved
- **Test Coverage**: Added comprehensive tests for output directory functionality
- **Documentation**: Enhanced README with detailed output options examples
- **Error Handling**: Better validation for mutually exclusive output options

## [0.2.0] - 2025-09-14

### Added
- **Incremental Configuration System**: New configuration format allowing base optimization levels with incremental modifications
  - Support for base optimization levels: `s` (size), `0`, `1`, `2`, `3` 
  - Incremental changes with `+` (add) and `-` (remove) syntax
  - Both array and string formats supported for incremental changes
  - Smart pass resolution with duplicate detection and ordering preservation
- **Enhanced Pass Discovery**: Comprehensive optimization pass listing and analysis
  - `--list-passes`: List all available LLVM optimization passes
  - `--list-O1`, `--list-O2`, `--list-O3`: List passes used in standard optimization levels
  - `--incremental-diff`: Show incremental differences between optimization levels
- **Example Configurations**: Multiple example configurations demonstrating new features
  - `incremental_config.yaml`: O2 base with custom vectorization tweaks
  - `size_opt_config.yaml`: Size optimization with targeted modifications
  - `o3_custom.yaml`: O3 base with vectorization disabled
  - `o0_basic.yaml`: O0 base with essential optimizations added
- **Comprehensive Documentation**: 
  - Detailed incremental configuration guide
  - Updated README with new features and examples
  - Migration guide from legacy to incremental format

### Improved
- **Error Handling**: Enhanced subprocess handling to gracefully manage binary output from LLVM tools
- **UTF-8 Compatibility**: Fixed encoding issues with LLVM tool output
- **Configuration Validation**: Support for both legacy and new configuration formats with proper validation
- **Verbose Output**: Enhanced verbose mode showing pass resolution details and base optimization information

### Technical Changes
- Enhanced `CppCompiler` class with incremental pass resolution methods
- Updated `ConfigParser` to validate both legacy and incremental configuration formats
- Improved `_run_command` method with robust binary output handling
- Added comprehensive pass discovery and listing functionality

## [0.1.0] - 2025-09-14

### Added
- Initial release of OptClang
- **Core Compilation**: C++ compilation with custom LLVM optimization passes
- **LLVM Integration**: Automatic detection of LLVM tools with CXX environment variable support
- **Configuration System**: YAML-based configuration for optimization passes and compiler settings
- **CLI Interface**: Command-line interface with convenient wrapper script
- **Testing Framework**: Comprehensive test suite with pytest
- **Examples**: Sample configurations and C++ test program
- **Setup Automation**: Automated setup script for easy installation

### Features
- Compile C++ files using LLVM/Clang with custom optimization passes
- Honor the `CXX` environment variable for non-standard LLVM installations
- Automatically detect LLVM tools in the same directory as your compiler
- Configure optimization passes via YAML files
- Support for custom compiler and linker flags
- Verbose output mode for debugging
- Cross-platform compatibility (Linux, macOS, Windows)

### Configuration Options
- `optimization_passes`: List of LLVM optimization passes to apply
- `compiler_flags`: Additional flags for the compilation step
- `linker_flags`: Additional flags for the linking step
- `cxx_path`: Path to clang++ compiler (overrides CXX environment variable)

### Requirements
- Python 3.8 or higher
- LLVM/Clang toolchain
- PyYAML

---

## Version History Summary

- **v0.2.0**: Major feature release with incremental configuration system and enhanced pass discovery
- **v0.1.0**: Initial release with core compilation functionality and legacy configuration format
