#!/usr/bin/env python3
"""
Test runner script with coverage support.
"""

import subprocess
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def run_tests(coverage=True):
    """Run tests with optional coverage."""
    
    # Change to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Ensure .coveragerc exists
    if not Path('.coveragerc').exists():
        print("Creating .coveragerc...")
        create_coveragerc()
    
    # Base pytest command
    cmd = [sys.executable, '-m', 'pytest', 'tests']
    
    if coverage:
        # Add coverage options
        cmd.extend([
            '--cov=.',
            '--cov-config=.coveragerc',
            '--cov-report=html:htmlcov',
            '--cov-report=term-missing',
            '--cov-report=xml',
            '--cov-fail-under=70'
        ])
    
    # Add other options
    cmd.extend([
        '--timeout=300',
        '-v',
        '--tb=short'
    ])
    
    # Add any additional arguments
    if len(sys.argv) > 1:
        if '--coverage' not in sys.argv:
            cmd.extend(sys.argv[1:])
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

def create_coveragerc():
    """Create default .coveragerc file."""
    content = """[run]
branch = True
source = .
omit =
    */tests/*
    test_*.py
    */test_*.py
    */__pycache__/*
    */venv/*
    */env/*
    */.venv/*
    setup.py
    run_tests.py
    conftest.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
"""
    with open('.coveragerc', 'w') as f:
        f.write(content)

if __name__ == '__main__':
    # Check if --coverage flag is present
    use_coverage = '--coverage' in sys.argv or len(sys.argv) == 1
    sys.exit(run_tests(coverage=use_coverage))
