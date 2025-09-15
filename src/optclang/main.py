#!/usr/bin/env python3
"""
Main entry point for the OptClang tool.
"""

import argparse
import sys
from pathlib import Path

# Handle both direct execution and module import
try:
    from .compiler import CppCompiler
    from .config_parser import ConfigParser
except ImportError:
    # When run directly, add the parent directory to sys.path
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from optclang.compiler import CppCompiler
    from optclang.config_parser import ConfigParser


def _list_optimization_passes(llvm_tools, verbose=False):
    """List all available LLVM optimization passes."""
    try:
        opt_tool = llvm_tools.get_tool('opt')
        
        if verbose:
            print(f"Using opt tool: {opt_tool}")
        
        import subprocess
        
        # Get optimization passes from opt --help-list
        passes = []
        
        try:
            result = subprocess.run(
                [opt_tool, '--help-list'],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Look for lines that start with spaces followed by --pass-name
            import re
            for line in result.stdout.split('\n'):
                # Match lines like "      --pass-name                      - Description"
                match = re.match(r'^\s+--([a-z][a-z0-9-]+)\s', line)
                if match:
                    pass_name = match.group(1)
                    # Filter out non-optimization passes
                    if (not pass_name.startswith('amdgpu-') and
                        not pass_name.startswith('arm-') and
                        not pass_name.startswith('nvptx-') and
                        not pass_name.startswith('hexagon-') and
                        not pass_name.startswith('x86-') and
                        not pass_name.startswith('aarch64-') and
                        not pass_name.startswith('ppc-') and
                        not pass_name.startswith('mips-') and
                        not pass_name.startswith('webassembly-') and
                        pass_name not in ['analyze', 'asm-show-inst', 'time-passes', 
                                        'debug-pass', 'print-after', 'print-before',
                                        'verify-each', 'verify-dom-info', 'stats',
                                        'help', 'help-list', 'version']):
                        passes.append(pass_name)
            
            if verbose:
                print(f"Found {len(passes)} passes using --help-list")
                
        except subprocess.CalledProcessError as e:
            if verbose:
                print(f"--help-list failed: {e}")
        
        # Fallback to common optimization passes if none found
        if not passes:
            passes = [
                'adce', 'aggressive-instcombine', 'alignment-from-assumptions',
                'always-inline', 'argpromotion', 'attributor', 'basicaa',
                'bdce', 'break-crit-edges', 'callsite-splitting', 'called-value-propagation',
                'canonicalize-aliases', 'consthoist', 'constmerge', 'constprop',
                'correlated-propagation', 'cross-dso-cfi', 'dce', 'deadargelim',
                'div-rem-pairs', 'dse', 'early-cse', 'elim-avail-extern',
                'float2int', 'forceattrs', 'function-attrs', 'globaldce',
                'globalopt', 'globalsplit', 'guard-widening', 'gvn',
                'gvn-hoist', 'gvn-sink', 'hot-cold-split', 'inferattrs',
                'inline', 'instcombine', 'instnamer', 'ipsccp', 'jump-threading',
                'lcssa', 'licm', 'loop-deletion', 'loop-distribute', 'loop-extract',
                'loop-extract-single', 'loop-idiom', 'loop-instsimplify', 'loop-interchange',
                'loop-load-elim', 'loop-predication', 'loop-reduce', 'loop-reroll',
                'loop-rotate', 'loop-simplifycfg', 'loop-sink', 'loop-unroll',
                'loop-unroll-and-jam', 'loop-unswitch', 'loop-vectorize', 'lower-expect',
                'lower-guard-intrinsic', 'loweratomic', 'lowerinvoke', 'lowerswitch',
                'mem2reg', 'memcpyopt', 'mergefunc', 'mergeicmps', 'mldst-motion',
                'name-anon-globals', 'newgvn', 'nary-reassociate', 'partial-inliner',
                'partially-inline-libcalls', 'post-inline-ee-instrument', 'prune-eh',
                'reassociate', 'reg2mem', 'rewrite-statepoints-for-gc', 'rpo-functionattrs',
                'scalarizer', 'sccp', 'separate-const-offset-from-gep', 'simple-loop-unswitch',
                'simplifycfg', 'sink', 'slp-vectorizer', 'speculative-execution',
                'sroa', 'strip', 'strip-dead-debug-info', 'strip-dead-prototypes',
                'strip-debug-declare', 'strip-nondebug', 'structurizecfg', 'tailcallelim',
                'tbaa', 'transform-warning', 'unify-function-exit-nodes'
            ]
            if verbose:
                print("Using fallback list of common optimization passes")
        
        # Remove duplicates and sort
        passes = sorted(list(set(passes)))
        
        if passes:
            print("Available LLVM optimization passes:")
            print("=" * 50)
            
            # Group passes for better readability
            for i, pass_name in enumerate(passes, 1):
                print(f"{i:3d}. {pass_name}")
                
            print(f"\nTotal: {len(passes)} passes")
            
            # Show common optimization passes
            common_passes = ['mem2reg', 'instcombine', 'simplifycfg', 'dce', 'gvn', 'sroa', 'licm', 'loop-unroll']
            available_common = [p for p in common_passes if p in passes]
            
            if available_common:
                print("\nCommonly used optimization passes:")
                for pass_name in available_common:
                    print(f"  - {pass_name}")
                    
            print("\nExample usage in config file:")
            print("optimization_passes:")
            for pass_name in available_common[:5]:
                print(f"  - {pass_name}")
        else:
            print("No optimization passes found. Try running with --verbose for more information.")
            
    except subprocess.CalledProcessError as e:
        print(f"Error running opt tool: {e}", file=sys.stderr)
        if verbose:
            print(f"Command output: {e.stdout}", file=sys.stderr)
            print(f"Command error: {e.stderr}", file=sys.stderr)
    except Exception as e:
        print(f"Error listing passes: {e}", file=sys.stderr)


def _list_optimization_level_passes(llvm_tools, opt_level, verbose=False):
    """List optimization passes used in a specific optimization level."""
    try:
        opt_tool = llvm_tools.get_tool('opt')
        
        if verbose:
            print(f"Using opt tool: {opt_tool}")
            print(f"Getting passes for optimization level -{opt_level}")
        
        import subprocess
        import tempfile
        
        # Create a simple test file
        test_code = """
define i32 @test() {
entry:
  %a = alloca i32
  store i32 42, i32* %a
  %b = load i32, i32* %a
  ret i32 %b
}
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ll', delete=False) as f:
            f.write(test_code)
            test_file = f.name
        
        try:
            # Run opt with the specified optimization level and debug-pass flag
            result = subprocess.run(
                [opt_tool, f'-{opt_level}', '--debug-pass=Arguments', test_file, '-o', '/dev/null'],
                capture_output=True,
                text=True,
                check=False  # Don't fail on non-zero exit
            )
            
            if verbose:
                print(f"Command: {' '.join([opt_tool, f'-{opt_level}', '--debug-pass=Arguments', test_file, '-o', '/dev/null'])}")
                print(f"Return code: {result.returncode}")
                print(f"Stderr: {result.stderr}")
            
            # Parse the output to extract pass names
            passes = []
            output = result.stderr if result.stderr else result.stdout
            
            for line in output.split('\n'):
                line = line.strip()
                # Look for lines that contain pass information
                if 'Pass Arguments:' in line:
                    # Extract passes from the arguments line
                    parts = line.split('Pass Arguments:')
                    if len(parts) > 1:
                        pass_args = parts[1].strip()
                        # Split on spaces and extract pass names (those starting with -)
                        for arg in pass_args.split():
                            if arg.startswith('-') and not arg.startswith('--'):
                                pass_name = arg[1:]  # Remove the leading -
                                if pass_name and pass_name not in passes:
                                    passes.append(pass_name)
                elif line.startswith('-') and ' ' in line:
                    # Sometimes passes are listed one per line
                    pass_name = line.split()[0][1:]  # Remove leading - and get first word
                    if pass_name and pass_name not in passes:
                        passes.append(pass_name)
            
            # If we didn't get passes from debug output, try a different approach
            if not passes and opt_level in ['O1', 'O2', 'O3']:
                # Try using opt with -print-after-all to see which passes run
                result2 = subprocess.run(
                    [opt_tool, f'-{opt_level}', '--print-after-all', test_file, '-o', '/dev/null'],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                # Parse print-after-all output
                for line in result2.stderr.split('\n'):
                    if 'IR Dump After' in line:
                        # Extract pass name from "IR Dump After PassName"
                        parts = line.split('IR Dump After')
                        if len(parts) > 1:
                            pass_name = parts[1].strip().split('(')[0].strip()
                            if pass_name and pass_name not in passes:
                                passes.append(pass_name)
            
            # Fallback to known optimization passes for each level
            if not passes:
                if opt_level == 'O1':
                    passes = [
                        'mem2reg', 'instcombine', 'reassociate', 'gvn', 'simplifycfg',
                        'sroa', 'early-cse', 'correlated-propagation', 'simplifycfg',
                        'instcombine', 'tailcallelim', 'simplifycfg', 'reassociate',
                        'loop-rotate', 'licm', 'loop-unswitch', 'instcombine',
                        'indvars', 'loop-idiom', 'loop-deletion', 'loop-unroll',
                        'gvn', 'memcpyopt', 'sccp', 'instcombine', 'jump-threading',
                        'correlated-propagation', 'dse', 'adce', 'simplifycfg',
                        'instcombine'
                    ]
                elif opt_level == 'O2':
                    passes = [
                        'targetlibinfo', 'no-aa', 'tbaa', 'scoped-noalias', 'assumption-cache-tracker',
                        'forceattrs', 'inferattrs', 'ipsccp', 'called-value-propagation',
                        'globalopt', 'domtree', 'mem2reg', 'deadargelim', 'domtree',
                        'instcombine', 'simplifycfg', 'basiccg', 'globals-aa', 'prune-eh',
                        'inline', 'functionattrs', 'argpromotion', 'domtree', 'sroa',
                        'early-cse', 'speculative-execution', 'jump-threading',
                        'correlated-propagation', 'simplifycfg', 'domtree', 'instcombine',
                        'tailcallelim', 'simplifycfg', 'reassociate', 'domtree',
                        'loop-simplify', 'lcssa-verification', 'lcssa', 'scalar-evolution',
                        'loop-rotate', 'licm', 'loop-unswitch', 'instcombine',
                        'scalar-evolution', 'indvars', 'loop-idiom', 'loop-deletion',
                        'loop-unroll', 'gvn', 'memcpyopt', 'sccp', 'instcombine',
                        'jump-threading', 'correlated-propagation', 'dse', 'loop-simplify',
                        'lcssa-verification', 'lcssa', 'adce', 'simplifycfg', 'instcombine',
                        'strip-dead-prototypes', 'globaldce', 'constmerge'
                    ]
                elif opt_level == 'O3':
                    passes = [
                        'targetlibinfo', 'no-aa', 'tbaa', 'scoped-noalias', 'assumption-cache-tracker',
                        'forceattrs', 'inferattrs', 'ipsccp', 'called-value-propagation',
                        'globalopt', 'domtree', 'mem2reg', 'deadargelim', 'domtree',
                        'instcombine', 'simplifycfg', 'basiccg', 'globals-aa', 'prune-eh',
                        'inline', 'functionattrs', 'argpromotion', 'domtree', 'sroa',
                        'early-cse', 'speculative-execution', 'jump-threading',
                        'correlated-propagation', 'simplifycfg', 'domtree', 'instcombine',
                        'tailcallelim', 'simplifycfg', 'reassociate', 'domtree',
                        'loop-simplify', 'lcssa-verification', 'lcssa', 'scalar-evolution',
                        'loop-rotate', 'licm', 'loop-unswitch', 'instcombine',
                        'scalar-evolution', 'indvars', 'loop-idiom', 'loop-deletion',
                        'loop-unroll', 'gvn', 'memcpyopt', 'sccp', 'instcombine',
                        'jump-threading', 'correlated-propagation', 'dse', 'loop-simplify',
                        'lcssa-verification', 'lcssa', 'scalar-evolution', 'loop-unroll',
                        'instcombine', 'loop-simplify', 'lcssa-verification', 'lcssa',
                        'scalar-evolution', 'licm', 'alignment-from-assumptions',
                        'strip-dead-prototypes', 'globaldce', 'constmerge', 'loop-vectorize',
                        'slp-vectorizer', 'gvn', 'instcombine', 'jump-threading',
                        'correlated-propagation', 'adce', 'simplifycfg', 'instcombine'
                    ]
                
                if verbose:
                    print(f"Using fallback list for -{opt_level}")
            
            # Remove duplicates while preserving order
            seen = set()
            unique_passes = []
            for pass_name in passes:
                if pass_name not in seen:
                    seen.add(pass_name)
                    unique_passes.append(pass_name)
            
            passes = unique_passes
            
            if passes:
                print(f"Optimization passes used in -{opt_level}:")
                print("=" * 50)
                
                for i, pass_name in enumerate(passes, 1):
                    print(f"{i:3d}. {pass_name}")
                
                print(f"\nTotal: {len(passes)} passes")
                
                print(f"\nExample config file for -{opt_level} equivalent:")
                print("optimization_passes:")
                for pass_name in passes:
                    print(f"  - {pass_name}")
                    
                print(f"\nNote: This is approximately equivalent to compiling with clang++ -{opt_level}")
            else:
                print(f"Could not determine optimization passes for -{opt_level}")
                print("Try running with --verbose for more information")
        
        finally:
            # Clean up temp file
            import os
            try:
                os.unlink(test_file)
            except:
                pass
                
    except subprocess.CalledProcessError as e:
        print(f"Error running opt tool: {e}", file=sys.stderr)
        if verbose:
            print(f"Command output: {e.stdout}", file=sys.stderr)
            print(f"Command error: {e.stderr}", file=sys.stderr)
    except Exception as e:
        print(f"Error listing passes: {e}", file=sys.stderr)


def _get_optimization_passes_for_level(llvm_tools, opt_level, verbose=False):
    """Get optimization passes for a specific level, returning a list."""
    try:
        opt_tool = llvm_tools.get_tool('opt')
        
        if verbose:
            print(f"Getting passes for -{opt_level}")
        
        import subprocess
        import tempfile
        
        # Create a simple test file
        test_code = """
define i32 @test() {
entry:
  %a = alloca i32
  store i32 42, i32* %a
  %b = load i32, i32* %a
  ret i32 %b
}
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ll', delete=False) as f:
            f.write(test_code)
            test_file = f.name
        
        try:
            # Run opt with the specified optimization level and debug-pass flag
            result = subprocess.run(
                [opt_tool, f'-{opt_level}', '--debug-pass=Arguments', test_file, '-o', '/dev/null'],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Parse the output to extract pass names
            passes = []
            output = result.stderr if result.stderr else result.stdout
            
            for line in output.split('\n'):
                line = line.strip()
                if 'Pass Arguments:' in line:
                    parts = line.split('Pass Arguments:')
                    if len(parts) > 1:
                        pass_args = parts[1].strip()
                        for arg in pass_args.split():
                            if arg.startswith('-') and not arg.startswith('--'):
                                pass_name = arg[1:]
                                if pass_name and pass_name not in passes:
                                    passes.append(pass_name)
            
            # Fallback to known optimization passes for each level
            if not passes:
                if opt_level == 'O0':
                    passes = ['verify', 'ee-instrument', 'write-bitcode']
                elif opt_level == 'O1':
                    passes = [
                        'tti', 'tbaa', 'scoped-noalias', 'assumption-cache-tracker', 'targetlibinfo',
                        'verify', 'ee-instrument', 'simplifycfg', 'domtree', 'sroa', 'early-cse',
                        'lower-expect', 'profile-summary-info', 'forceattrs', 'inferattrs',
                        'ipsccp', 'called-value-propagation', 'attributor', 'globalopt', 'mem2reg',
                        'deadargelim', 'basicaa', 'aa', 'loops', 'lazy-branch-prob', 'lazy-block-freq',
                        'opt-remark-emitter', 'instcombine', 'basiccg', 'globals-aa', 'prune-eh',
                        'inline', 'functionattrs', 'memoryssa', 'early-cse-memssa', 'speculative-execution',
                        'lazy-value-info', 'jump-threading', 'correlated-propagation', 'libcalls-shrinkwrap',
                        'branch-prob', 'block-freq', 'pgo-memop-opt', 'tailcallelim', 'reassociate',
                        'loop-simplify', 'lcssa-verification', 'lcssa', 'scalar-evolution', 'loop-rotate',
                        'licm', 'loop-unswitch', 'indvars', 'loop-idiom', 'loop-deletion', 'loop-unroll',
                        'mldst-motion', 'phi-values', 'memdep', 'gvn', 'memcpyopt', 'sccp',
                        'demanded-bits', 'bdce', 'dse', 'postdomtree', 'adce', 'barrier',
                        'elim-avail-extern', 'rpo-functionattrs', 'globaldce', 'float2int',
                        'lower-constant-intrinsics', 'transform-warning', 'alignment-from-assumptions',
                        'strip-dead-prototypes', 'loop-sink', 'instsimplify', 'div-rem-pairs', 'write-bitcode'
                    ]
                elif opt_level == 'O2':
                    passes = [
                        'tti', 'tbaa', 'scoped-noalias', 'assumption-cache-tracker', 'targetlibinfo',
                        'verify', 'ee-instrument', 'simplifycfg', 'domtree', 'sroa', 'early-cse',
                        'lower-expect', 'profile-summary-info', 'forceattrs', 'inferattrs',
                        'ipsccp', 'called-value-propagation', 'attributor', 'globalopt', 'mem2reg',
                        'deadargelim', 'basicaa', 'aa', 'loops', 'lazy-branch-prob', 'lazy-block-freq',
                        'opt-remark-emitter', 'instcombine', 'basiccg', 'globals-aa', 'prune-eh',
                        'inline', 'functionattrs', 'memoryssa', 'early-cse-memssa', 'speculative-execution',
                        'lazy-value-info', 'jump-threading', 'correlated-propagation', 'libcalls-shrinkwrap',
                        'branch-prob', 'block-freq', 'pgo-memop-opt', 'tailcallelim', 'reassociate',
                        'loop-simplify', 'lcssa-verification', 'lcssa', 'scalar-evolution', 'loop-rotate',
                        'licm', 'loop-unswitch', 'indvars', 'loop-idiom', 'loop-deletion', 'loop-unroll',
                        'mldst-motion', 'phi-values', 'memdep', 'gvn', 'memcpyopt', 'sccp',
                        'demanded-bits', 'bdce', 'dse', 'postdomtree', 'adce', 'barrier',
                        'elim-avail-extern', 'rpo-functionattrs', 'globaldce', 'float2int',
                        'lower-constant-intrinsics', 'loop-accesses', 'loop-distribute', 'loop-vectorize',
                        'loop-load-elim', 'slp-vectorizer', 'transform-warning', 'alignment-from-assumptions',
                        'strip-dead-prototypes', 'constmerge', 'loop-sink', 'instsimplify', 'div-rem-pairs',
                        'write-bitcode'
                    ]
                elif opt_level == 'O3':
                    passes = [
                        'tti', 'tbaa', 'scoped-noalias', 'assumption-cache-tracker', 'targetlibinfo',
                        'verify', 'ee-instrument', 'simplifycfg', 'domtree', 'sroa', 'early-cse',
                        'lower-expect', 'profile-summary-info', 'forceattrs', 'inferattrs',
                        'callsite-splitting', 'ipsccp', 'called-value-propagation', 'attributor',
                        'globalopt', 'mem2reg', 'deadargelim', 'basicaa', 'aa', 'loops',
                        'lazy-branch-prob', 'lazy-block-freq', 'opt-remark-emitter', 'instcombine',
                        'basiccg', 'globals-aa', 'prune-eh', 'inline', 'functionattrs', 'argpromotion',
                        'memoryssa', 'early-cse-memssa', 'speculative-execution', 'lazy-value-info',
                        'jump-threading', 'correlated-propagation', 'libcalls-shrinkwrap', 'branch-prob',
                        'block-freq', 'pgo-memop-opt', 'tailcallelim', 'reassociate', 'loop-simplify',
                        'lcssa-verification', 'lcssa', 'scalar-evolution', 'loop-rotate', 'licm',
                        'loop-unswitch', 'indvars', 'loop-idiom', 'loop-deletion', 'loop-unroll',
                        'mldst-motion', 'phi-values', 'memdep', 'gvn', 'memcpyopt', 'sccp',
                        'demanded-bits', 'bdce', 'dse', 'postdomtree', 'adce', 'barrier',
                        'elim-avail-extern', 'rpo-functionattrs', 'globaldce', 'float2int',
                        'lower-constant-intrinsics', 'loop-accesses', 'loop-distribute', 'loop-vectorize',
                        'loop-load-elim', 'slp-vectorizer', 'transform-warning', 'alignment-from-assumptions',
                        'strip-dead-prototypes', 'constmerge', 'loop-sink', 'instsimplify', 'div-rem-pairs',
                        'write-bitcode'
                    ]
        
        finally:
            # Clean up temp file
            import os
            try:
                os.unlink(test_file)
            except:
                pass
        
        return passes
        
    except Exception as e:
        if verbose:
            print(f"Error getting passes for {opt_level}: {e}")
        return []


def _show_incremental_differences(llvm_tools, verbose=False):
    """Show incremental differences between optimization levels."""
    try:
        print("Incremental Optimization Level Differences:")
        print("=" * 60)
        
        # Get passes for each level
        o0_passes = _get_optimization_passes_for_level(llvm_tools, 'O0', verbose)
        o1_passes = _get_optimization_passes_for_level(llvm_tools, 'O1', verbose)
        o2_passes = _get_optimization_passes_for_level(llvm_tools, 'O2', verbose)
        o3_passes = _get_optimization_passes_for_level(llvm_tools, 'O3', verbose)
        
        # Convert to sets for easier comparison
        o0_set = set(o0_passes)
        o1_set = set(o1_passes)
        o2_set = set(o2_passes)
        o3_set = set(o3_passes)
        
        # Calculate differences
        o0_to_o1_added = o1_set - o0_set
        o0_to_o1_removed = o0_set - o1_set
        
        o1_to_o2_added = o2_set - o1_set
        o1_to_o2_removed = o1_set - o2_set
        
        o2_to_o3_added = o3_set - o2_set
        o2_to_o3_removed = o2_set - o3_set
        
        # Display differences in one line each
        print("O0 to O1 changes:")
        if o0_to_o1_added:
            print(f"  Added: {', '.join(sorted(o0_to_o1_added))}")
        if o0_to_o1_removed:
            print(f"  Removed: {', '.join(sorted(o0_to_o1_removed))}")
        if not o0_to_o1_added and not o0_to_o1_removed:
            print("  No changes")
        
        print("\nO1 to O2 changes:")
        if o1_to_o2_added:
            print(f"  Added: {', '.join(sorted(o1_to_o2_added))}")
        if o1_to_o2_removed:
            print(f"  Removed: {', '.join(sorted(o1_to_o2_removed))}")
        if not o1_to_o2_added and not o1_to_o2_removed:
            print("  No changes")
        
        print("\nO2 to O3 changes:")
        if o2_to_o3_added:
            print(f"  Added: {', '.join(sorted(o2_to_o3_added))}")
        if o2_to_o3_removed:
            print(f"  Removed: {', '.join(sorted(o2_to_o3_removed))}")
        if not o2_to_o3_added and not o2_to_o3_removed:
            print("  No changes")
        
        print(f"\nSummary:")
        print(f"  O0: {len(o0_passes)} passes")
        print(f"  O1: {len(o1_passes)} passes (+{len(o0_to_o1_added)}, -{len(o0_to_o1_removed)})")
        print(f"  O2: {len(o2_passes)} passes (+{len(o1_to_o2_added)}, -{len(o1_to_o2_removed)})")
        print(f"  O3: {len(o3_passes)} passes (+{len(o2_to_o3_added)}, -{len(o2_to_o3_removed)})")
        
    except Exception as e:
        print(f"Error showing incremental differences: {e}", file=sys.stderr)


def main():
    """Main entry point for the OptClang CLI."""
    parser = argparse.ArgumentParser(
        description="Compile C++ files with custom LLVM optimization passes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  %(prog)s source.cpp -c config.yaml -o optimized_program
  %(prog)s source.cpp -c config.yaml -v
  %(prog)s --list-passes
  %(prog)s --list-O2
  %(prog)s --incremental-diff
        """
    )
    
    parser.add_argument('input_file', nargs='?',
                       help='C++ source file to compile')
    parser.add_argument('-c', '--config',
                       help='YAML configuration file (required unless using --list-passes)')
    parser.add_argument('-o', '--output',
                       help='Output executable name (default: input filename without extension)')
    parser.add_argument('--output-dir',
                       help='Output directory for the executable (cannot be used with -o/--output)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--list-passes', action='store_true',
                       help='List all available LLVM optimization passes and incremental differences and exit')
    parser.add_argument('--list-O1', action='store_true',
                       help='List optimization passes used in -O1 and exit')
    parser.add_argument('--list-O2', action='store_true',
                       help='List optimization passes used in -O2 and exit')
    parser.add_argument('--list-O3', action='store_true',
                       help='List optimization passes used in -O3 and exit')
    parser.add_argument('--incremental-diff', action='store_true',
                       help='Show incremental differences between optimization levels and exit')
    
    args = parser.parse_args()
    
    # Handle list-passes option first
    if args.list_passes:
        try:
            # Handle both direct execution and module import
            try:
                from .llvm_tools import LLVMTools
            except ImportError:
                from optclang.llvm_tools import LLVMTools
            
            tools = LLVMTools()
            _list_optimization_passes(tools, args.verbose)
            print("\n" + "="*60)
            _show_incremental_differences(tools, args.verbose)
            return 0
        except Exception as e:
            print(f"Error listing optimization passes: {e}", file=sys.stderr)
            return 1
    
    # Handle incremental diff option
    if args.incremental_diff:
        try:
            # Handle both direct execution and module import
            try:
                from .llvm_tools import LLVMTools
            except ImportError:
                from optclang.llvm_tools import LLVMTools
            
            tools = LLVMTools()
            _show_incremental_differences(tools, args.verbose)
            return 0
        except Exception as e:
            print(f"Error showing incremental differences: {e}", file=sys.stderr)
            return 1
    
    # Handle optimization level listing
    if args.list_O1 or args.list_O2 or args.list_O3:
        try:
            # Handle both direct execution and module import
            try:
                from .llvm_tools import LLVMTools
            except ImportError:
                from optclang.llvm_tools import LLVMTools
            
            tools = LLVMTools()
            if args.list_O1:
                _list_optimization_level_passes(tools, "O1", args.verbose)
            elif args.list_O2:
                _list_optimization_level_passes(tools, "O2", args.verbose)
            elif args.list_O3:
                _list_optimization_level_passes(tools, "O3", args.verbose)
            return 0
        except Exception as e:
            print(f"Error listing optimization passes: {e}", file=sys.stderr)
            return 1
    
    # Validate required arguments when not listing passes
    if not args.input_file:
        print("Error: input_file is required", file=sys.stderr)
        parser.print_help()
        return 1
        
    if not args.config:
        print("Error: config file is required", file=sys.stderr)
        parser.print_help()
        return 1
    
    # Validate mutually exclusive output options
    if args.output and args.output_dir:
        print("Error: Cannot specify both --output and --output-dir", file=sys.stderr)
        return 1
    
    # Validate input file
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' does not exist", file=sys.stderr)
        return 1
    
    if input_path.suffix not in ['.cpp', '.cxx', '.cc', '.C']:
        print(f"Warning: Input file '{input_path}' doesn't have a C++ extension", file=sys.stderr)
    
    # Validate config file
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config file '{config_path}' does not exist", file=sys.stderr)
        return 1
    
    try:
        # Parse configuration
        config_parser = ConfigParser()
        config = config_parser.parse(config_path)
        
        # Determine output filename
        if args.output:
            # User specified explicit output name
            output_file = args.output
        elif args.output_dir:
            # User specified output directory
            output_dir = Path(args.output_dir)
            if not output_dir.exists():
                print(f"Creating output directory: {output_dir}")
                output_dir.mkdir(parents=True, exist_ok=True)
            elif not output_dir.is_dir():
                print(f"Error: '{output_dir}' exists but is not a directory", file=sys.stderr)
                return 1
            output_file = str(output_dir / input_path.stem)
        else:
            # Default: use input filename without extension in current directory
            output_file = input_path.stem
        
        # Create and run compiler
        compiler = CppCompiler(config, verbose=args.verbose)
        success = compiler.compile(input_path, output_file)
        
        if success:
            print(f"Successfully compiled '{input_path}' to '{output_file}'")
            return 0
        else:
            print("Compilation failed", file=sys.stderr)
            return 1
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
