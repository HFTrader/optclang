#!/usr/bin/env python3
"""
Entry point script for OptClang when installed as a package.
"""

import sys
import os

# Add src to path if running from development directory
if os.path.exists(os.path.join(os.path.dirname(__file__), 'src', 'optclang')):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from optclang.main import main

if __name__ == "__main__":
    sys.exit(main())
