#!/bin/bash
# Setup script for OptClang

echo "Setting up OptClang for Python 3..."

# Check Python 3 version
python3 --version
if [ $? -ne 0 ]; then
    echo "Error: Python 3 is required but not found"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Run tests
echo "Running tests..."
PYTHONPATH=src python3 -m pytest tests/ -v

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Setup complete! OptClang is ready to use with Python 3."
    echo ""
    echo "Usage examples:"
    echo "  ./optclang_cli.py examples/sample.cpp -c examples/basic_config.yaml -o optimized_sample"
    echo "  python3 src/optclang/main.py examples/sample.cpp -c examples/basic_config.yaml -v"
    echo "  PYTHONPATH=src python3 -m optclang.main examples/sample.cpp -c examples/basic_config.yaml -o output"
else
    echo "❌ Some tests failed. Please check the output above."
    exit 1
fi
