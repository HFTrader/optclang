"""
LLVM tools detection and management.
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Dict


class LLVMTools:
    """Manages LLVM tool detection and paths."""
    
    def __init__(self, cxx_path: Optional[str] = None):
        self.cxx_path = cxx_path or os.environ.get("CXX", "clang++")
        self.tools = {}
        self._detect_tools()
    
    def _detect_tools(self) -> None:
        """Detect LLVM tools based on CXX path."""
        # Extract directory from CXX path
        cxx_dir = Path(self.cxx_path).parent if "/" in self.cxx_path else None
        
        tools_to_find = {
            "clang++": self.cxx_path,
            "clang": None,
            "opt": None,
            "llc": None,
            "llvm-link": None,
            "llvm-dis": None
        }
        
        for tool, known_path in tools_to_find.items():
            if known_path:
                self.tools[tool] = known_path
                continue
                
            # Try to find in same directory as CXX
            if cxx_dir:
                tool_path = cxx_dir / tool
                if tool_path.exists():
                    self.tools[tool] = str(tool_path)
                    continue
            
            # Try to find in PATH
            found_path = shutil.which(tool)
            if found_path:
                self.tools[tool] = found_path
            else:
                # Derive from clang++ name
                if tool == "clang" and "clang++" in self.tools:
                    clang_path = self.tools["clang++"].replace("clang++", "clang")
                    if Path(clang_path).exists():
                        self.tools[tool] = clang_path
    
    def get_tool(self, tool_name: str) -> str:
        """Get the path to a specific LLVM tool."""
        if tool_name not in self.tools:
            raise RuntimeError(f"LLVM tool '{tool_name}' not found")
        return self.tools[tool_name]
    
    def list_tools(self) -> Dict[str, str]:
        """Return a dictionary of all found tools."""
        return self.tools.copy()
    
    def has_tool(self, tool_name: str) -> bool:
        """Check if a specific tool is available."""
        return tool_name in self.tools
