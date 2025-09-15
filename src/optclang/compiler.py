"""
C++ compiler with custom LLVM optimization passes.
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any

from .llvm_tools import LLVMTools


class CppCompiler:
    """Compiles C++ files with custom LLVM optimization passes."""
    
    def __init__(self, config: Dict[str, Any], verbose: bool = False):
        self.config = config
        self.verbose = verbose
        self.llvm_tools = LLVMTools(config.get("cxx_path"))
        
        # Resolve optimization passes from config
        self.optimization_passes = self._resolve_optimization_passes()
        
        if self.verbose:
            print("Available LLVM tools:")
            for tool, path in self.llvm_tools.list_tools().items():
                print(f"  {tool}: {path}")
            
            if self.optimization_passes:
                print(f"Resolved optimization passes: {len(self.optimization_passes)} passes")
    
    def _resolve_optimization_passes(self) -> List[str]:
        """Resolve optimization passes from configuration."""
        # Check if using new base_optimization + incremental_changes format
        if 'base_optimization' in self.config or 'incremental_changes' in self.config:
            return self._resolve_incremental_passes()
        elif 'optimization_passes' in self.config:
            # Legacy format
            return self.config['optimization_passes']
        else:
            # No optimization passes specified
            return []
    
    def _resolve_incremental_passes(self) -> List[str]:
        """Resolve optimization passes using base level + incremental changes."""
        base_level = self.config.get('base_optimization', '0')
        incremental_changes = self.config.get('incremental_changes', [])
        
        # Store base level for new pass manager
        self.base_optimization_level = base_level
        self.incremental_changes = incremental_changes
        
        if self.verbose:
            print(f"Base optimization level: -{base_level}")
            print(f"Incremental changes: {incremental_changes}")
        
        # Get base passes for the optimization level
        base_passes = self._get_base_passes_for_level(base_level)
        
        if self.verbose:
            print(f"Base passes: {len(base_passes)} passes")
        
        # Apply incremental changes
        final_passes = base_passes.copy()
        
        for change in incremental_changes:
            change = change.strip()
            if change.startswith('+'):
                pass_to_add = change[1:]
                if pass_to_add not in final_passes:
                    final_passes.append(pass_to_add)
                    if self.verbose:
                        print(f"  Added: {pass_to_add}")
            elif change.startswith('-'):
                pass_to_remove = change[1:]
                if pass_to_remove in final_passes:
                    final_passes.remove(pass_to_remove)
                    if self.verbose:
                        print(f"  Removed: {pass_to_remove}")
                elif self.verbose:
                    print(f"  Warning: {pass_to_remove} not in base passes, cannot remove")
        
        if self.verbose:
            print(f"Final passes: {len(final_passes)} passes")
        
        return final_passes
    
    def _get_base_passes_for_level(self, level: str) -> List[str]:
        """Get base optimization passes for a given level."""
        if level == 's':  # -Os (size optimization)
            return [
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
                'strip-dead-prototypes', 'constmerge'
            ]
        elif level == '0':  # -O0
            return ['verify', 'ee-instrument', 'write-bitcode']
        elif level == '1':  # -O1
            return [
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
        elif level == '2':  # -O2
            return [
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
        elif level == '3':  # -O3
            return [
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
        else:
            return []
        
    def compile(self, input_file: Path, output_file: str) -> bool:
        """Compile a C++ file with the specified optimization passes."""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                if self.verbose:
                    print(f"Using temporary directory: {temp_path}")
                
                # Step 1: Compile to LLVM IR
                ir_file = temp_path / "output.ll"
                if not self._compile_to_ir(input_file, ir_file):
                    return False
                
                # Step 2: Apply optimization passes if specified
                if self.optimization_passes:
                    optimized_ir = temp_path / "optimized.ll"
                    if not self._apply_optimizations(ir_file, optimized_ir):
                        return False
                    final_ir = optimized_ir
                else:
                    if self.verbose:
                        print("No optimization passes specified")
                    final_ir = ir_file
                
                # Step 3: Compile IR to executable
                if not self._compile_ir_to_executable(final_ir, output_file):
                    return False
                
                return True
                
        except Exception as e:
            print(f"Compilation failed: {e}")
            return False
    
    def _compile_to_ir(self, input_file: Path, ir_file: Path) -> bool:
        """Compile C++ source to LLVM IR."""
        clang = self.llvm_tools.get_tool("clang++")
        
        cmd = [
            clang,
            "-S", "-emit-llvm",
            "-o", str(ir_file),
            str(input_file)
        ]
        
        # Add compiler flags from config
        if "compiler_flags" in self.config:
            cmd.extend(self.config["compiler_flags"])
        
        return self._run_command(cmd, "Compiling to IR")
    
    def _apply_optimizations(self, ir_file: Path, output_file: Path) -> bool:
        """Apply optimization passes to LLVM IR."""
        opt = self.llvm_tools.get_tool("opt")
        
        # Check if we should use new pass manager syntax
        if self._uses_new_pass_manager():
            # For new pass manager, handle base optimization + incremental changes differently
            if hasattr(self, 'base_optimization_level') and self.base_optimization_level:
                return self._apply_new_pass_manager_optimizations(ir_file, output_file)
            else:
                # Legacy configuration with explicit pass list - use new syntax
                cmd = [opt, "-S"]
                passes_str = ",".join(self.optimization_passes)
                cmd.extend(["-passes", passes_str])
                cmd.extend(["-o", str(output_file), str(ir_file)])
        else:
            # Legacy pass manager syntax: -pass1 -pass2 -pass3
            cmd = [opt, "-S"]
            
            # Add optimization passes from resolved list
            for pass_name in self.optimization_passes:
                if not pass_name.startswith("-"):
                    pass_name = f"-{pass_name}"
                cmd.append(pass_name)
            
            cmd.extend(["-o", str(output_file), str(ir_file)])
        
        return self._run_command(cmd, "Applying optimizations")
    
    def _apply_new_pass_manager_optimizations(self, ir_file: Path, output_file: Path) -> bool:
        """Apply optimizations using new pass manager with base level + incremental changes."""
        opt = self.llvm_tools.get_tool("opt")
        
        # Map our base levels to new pass manager syntax
        base_level_map = {
            's': 'default<Os>',
            '0': 'default<O0>',
            '1': 'default<O1>',
            '2': 'default<O2>',
            '3': 'default<O3>'
        }
        
        base_pipeline = base_level_map.get(self.base_optimization_level, 'default<O2>')
        
        # For now, with the new pass manager, we'll use the base optimization level
        # and warn about incremental changes not being fully supported yet
        if hasattr(self, 'incremental_changes') and self.incremental_changes:
            if self.verbose:
                print(f"Warning: Incremental changes not fully supported with LLVM 19+ new pass manager.")
                print(f"Using base optimization level '{self.base_optimization_level}' only.")
        
        cmd = [opt, "-S", "-passes", base_pipeline]
        cmd.extend(["-o", str(output_file), str(ir_file)])
        
        return self._run_command(cmd, "Applying optimizations")
    
    def _uses_new_pass_manager(self) -> bool:
        """Check if the LLVM installation uses the new pass manager."""
        try:
            opt = self.llvm_tools.get_tool("opt")
            result = subprocess.run(
                [opt, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Extract version number from output like "LLVM version 19.1.6"
            for line in result.stdout.split('\n'):
                if 'LLVM version' in line:
                    import re
                    version_match = re.search(r'LLVM version (\d+)\.(\d+)', line)
                    if version_match:
                        major = int(version_match.group(1))
                        # LLVM 15+ uses new pass manager by default
                        return major >= 15
            
            # If we can't determine version, try to detect by running a simple test
            test_result = subprocess.run(
                [opt, "-mem2reg", "--help"],
                capture_output=True,
                text=True
            )
            # If legacy syntax shows an error about new pass manager, we know it's new
            return "new pass manager" in test_result.stderr
            
        except Exception:
            # Default to legacy if we can't determine
            return False
    
    def _compile_ir_to_executable(self, ir_file: Path, output_file: str) -> bool:
        """Compile LLVM IR to executable."""
        clang = self.llvm_tools.get_tool("clang++")
        
        cmd = [
            clang,
            "-o", output_file,
            str(ir_file)
        ]
        
        # Add linker flags from config
        if "linker_flags" in self.config:
            cmd.extend(self.config["linker_flags"])
        
        return self._run_command(cmd, "Linking executable")
    
    def _run_command(self, cmd: List[str], description: str) -> bool:
        """Run a command and handle output."""
        if self.verbose:
            print(f"{description}: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                check=True
            )
            
            if self.verbose and result.stdout:
                # Try to decode as UTF-8, fall back to binary representation if needed
                try:
                    stdout_text = result.stdout.decode('utf-8')
                    if stdout_text.strip():
                        print(stdout_text)
                except UnicodeDecodeError:
                    # If UTF-8 decoding fails, just print that output was generated
                    print(f"[Binary output generated, {len(result.stdout)} bytes]")
                
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error during {description}:")
            print(f"Command: {' '.join(cmd)}")
            print(f"Return code: {e.returncode}")
            
            # Handle stdout/stderr with proper encoding
            if e.stdout:
                try:
                    stdout_text = e.stdout.decode('utf-8')
                    print(f"Stdout: {stdout_text}")
                except UnicodeDecodeError:
                    print(f"Stdout: [Binary data, {len(e.stdout)} bytes]")
                    
            if e.stderr:
                try:
                    stderr_text = e.stderr.decode('utf-8')
                    print(f"Stderr: {stderr_text}")
                except UnicodeDecodeError:
                    print(f"Stderr: [Binary data, {len(e.stderr)} bytes]")
                    
            return False
