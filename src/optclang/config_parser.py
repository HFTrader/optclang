"""
Configuration parser for YAML config files.
"""

from pathlib import Path
from typing import Dict, List, Any

try:
    import yaml
except ImportError:
    raise ImportError("PyYAML is required. Install with: pip3 install PyYAML")


class ConfigParser:
    """Parses YAML configuration files for compilation settings."""
    
    def parse(self, config_path: Path) -> Dict[str, Any]:
        """Parse a YAML configuration file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")
        except Exception as e:
            raise ValueError(f"Error reading config file: {e}")
        
        # Validate configuration
        self._validate_config(config)
        
        return config
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Validate the configuration structure."""
        if not isinstance(config, dict):
            raise ValueError("Configuration must be a dictionary")
        
        # Check if using new base_optimization + incremental_changes format
        has_base_opt = 'base_optimization' in config
        has_incremental = 'incremental_changes' in config
        has_optimization_passes = 'optimization_passes' in config
        
        if has_base_opt or has_incremental:
            # New format validation
            if has_optimization_passes:
                raise ValueError("Cannot use both 'optimization_passes' and 'base_optimization'/'incremental_changes' format")
            
            if has_base_opt:
                if not isinstance(config['base_optimization'], str):
                    raise ValueError("base_optimization must be a string")
                if config['base_optimization'] not in ['s', '0', '1', '2', '3']:
                    raise ValueError("base_optimization must be one of: 's', '0', '1', '2', '3'")
            
            if has_incremental:
                if isinstance(config['incremental_changes'], str):
                    # Convert comma-separated string to list
                    config['incremental_changes'] = [x.strip() for x in config['incremental_changes'].split(',') if x.strip()]
                
                if not isinstance(config['incremental_changes'], list):
                    raise ValueError("incremental_changes must be a list or comma-separated string")
                
                # Validate each incremental change
                for change in config['incremental_changes']:
                    if not isinstance(change, str):
                        raise ValueError("Each incremental change must be a string")
                    if not (change.startswith('+') or change.startswith('-')):
                        raise ValueError(f"Incremental change '{change}' must start with '+' or '-'")
                    if len(change) < 2:
                        raise ValueError(f"Incremental change '{change}' must have a pass name after '+' or '-'")
        else:
            # Legacy format validation
            if 'optimization_passes' in config:
                if not isinstance(config['optimization_passes'], list):
                    raise ValueError("optimization_passes must be a list")
        
        # compiler_flags is optional but if present must be a list
        if 'compiler_flags' in config:
            if not isinstance(config['compiler_flags'], list):
                raise ValueError("compiler_flags must be a list")
        
        # linker_flags is optional but if present must be a list
        if 'linker_flags' in config:
            if not isinstance(config['linker_flags'], list):
                raise ValueError("linker_flags must be a list")
        
        # cxx_path is optional but if present must be a string
        if 'cxx_path' in config:
            if not isinstance(config['cxx_path'], str):
                raise ValueError("cxx_path must be a string")
