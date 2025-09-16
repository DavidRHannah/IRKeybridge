#!/usr/bin/env python3
"""
Test runner script for IR Remote Controller.

This script provides various testing options including coverage reports,
specific test selection, and different output formats.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, check=True):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        if check:
            raise
        return e


def install_dependencies():
    """Install test dependencies."""
    print("Installing test dependencies...")
    cmd = [sys.executable, "-m", "pip", "install", "-r", "test_requirements.txt"]
    run_command(cmd)


def run_tests(args):
    """Run the test suite with specified options."""
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add verbosity
    if args.verbose:
        cmd.append("-v")
    elif args.quiet:
        cmd.append("-q")
    
    # Add coverage options
    if args.coverage:
        cmd.extend([
            "--cov=.",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-report=xml",
            f"--cov-fail-under={args.min_coverage}"
        ])
    
    # Add specific test selection
    if args.test_file:
        cmd.append(args.test_file)
    elif args.test_function:
        cmd.extend(["-k", args.test_function])
    elif args.markers:
        cmd.extend(["-m", args.markers])
    
    # Add parallel execution
    if args.parallel:
        cmd.extend(["-n", "auto"])
    
    # Add output format
    if args.html_report:
        cmd.extend(["--html=test_report.html", "--self-contained-html"])
    
    if args.json_report:
        cmd.append("--json-report")
    
    # Add timeout
    if args.timeout:
        cmd.extend(["--timeout", str(args.timeout)])
    
    # Add benchmark
    if args.benchmark:
        cmd.append("--benchmark-only")
    
    # Run the tests
    result = run_command(cmd, check=False)
    return result.returncode


def run_lint():
    """Run code linting."""
    print("\nRunning code linting...")
    
    commands = [
        [sys.executable, "-m", "flake8", ".", "--count", "--statistics"],
        [sys.executable, "-m", "black", "--check", "."],
        [sys.executable, "-m", "isort", "--check-only", "."],
    ]
    
    all_passed = True
    for cmd in commands:
        try:
            run_command(cmd)
        except subprocess.CalledProcessError:
            all_passed = False
    
    return all_passed


def run_type_check():
    """Run type checking with mypy."""
    print("\nRunning type checking...")
    cmd = [sys.executable, "-m", "mypy", ".", "--ignore-missing-imports"]
    try:
        run_command(cmd)
        return True
    except subprocess.CalledProcessError:
        return False


def generate_coverage_report():
    """Generate and display coverage report."""
    print("\nGenerating coverage report...")
    
    # Generate HTML report
    cmd = [sys.executable, "-m", "coverage", "html"]
    run_command(cmd, check=False)
    
    # Generate console report
    cmd = [sys.executable, "-m", "coverage", "report"]
    result = run_command(cmd, check=False)
    
    # Show coverage percentage
    cmd = [sys.executable, "-m", "coverage", "report", "--format=total"]
    total_result = run_command(cmd, check=False)
    
    if total_result.returncode == 0:
        coverage_pct = float(total_result.stdout.strip())
        print(f"\nTotal Coverage: {coverage_pct:.1f}%")
        
        if coverage_pct >= 70:
            print("✓ Coverage target achieved!")
        else:
            print(f"✗ Coverage below target (70%). Need {70 - coverage_pct:.1f}% more.")
    
    print(f"\nHTML coverage report generated: {Path.cwd() / 'htmlcov' / 'index.html'}")


def clean_cache():
    """Clean test and coverage cache files."""
    print("Cleaning cache files...")
    
    cache_dirs = [
        ".pytest_cache",
        "__pycache__",
        ".coverage",
        "htmlcov",
        "test_report.html",
        "coverage.xml",
        ".mypy_cache"
    ]
    
    for cache_item in cache_dirs:
        path = Path(cache_item)
        if path.is_file():
            path.unlink()
            print(f"Removed file: {cache_item}")
        elif path.is_dir():
            import shutil
            shutil.rmtree(path)
            print(f"Removed directory: {cache_item}")
    
    # Clean __pycache__ recursively
    for pycache in Path(".").rglob("__pycache__"):
        import shutil
        shutil.rmtree(pycache)
        print(f"Removed: {pycache}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Test runner for IR Remote Controller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                        # Run all tests
  python run_tests.py --coverage             # Run with coverage
  python run_tests.py --test-file test_config_manager.py  # Run specific file
  python run_tests.py --markers unit         # Run unit tests only
  python run_tests.py --lint                 # Run linting only
  python run_tests.py --install-deps         # Install dependencies
  python run_tests.py --clean                # Clean cache files
        """
    )
    
    # Test execution options
    parser.add_argument("--coverage", action="store_true", 
                       help="Run tests with coverage reporting")
    parser.add_argument("--min-coverage", type=int, default=70,
                       help="Minimum coverage percentage (default: 70)")
    parser.add_argument("--parallel", action="store_true",
                       help="Run tests in parallel")
    parser.add_argument("--timeout", type=int, default=300,
                       help="Test timeout in seconds (default: 300)")
    
    # Test selection
    parser.add_argument("--test-file", type=str,
                       help="Run specific test file")
    parser.add_argument("--test-function", type=str,
                       help="Run tests matching function name pattern")
    parser.add_argument("--markers", type=str,
                       help="Run tests with specific markers (unit, integration, slow)")
    
    # Output options
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    parser.add_argument("--quiet", "-q", action="store_true",
                       help="Quiet output")
    parser.add_argument("--html-report", action="store_true",
                       help="Generate HTML test report")
    parser.add_argument("--json-report", action="store_true",
                       help="Generate JSON test report")
    
    # Additional tools
    parser.add_argument("--lint", action="store_true",
                       help="Run code linting (flake8, black, isort)")
    parser.add_argument("--type-check", action="store_true",
                       help="Run type checking with mypy")
    parser.add_argument("--benchmark", action="store_true",
                       help="Run benchmark tests only")
    
    # Utility options
    parser.add_argument("--install-deps", action="store_true",
                       help="Install test dependencies")
    parser.add_argument("--clean", action="store_true",
                       help="Clean cache files and coverage data")
    parser.add_argument("--coverage-report", action="store_true",
                       help="Generate coverage report from existing data")
    
    args = parser.parse_args()
    
    # Handle utility commands first
    if args.install_deps:
        install_dependencies()
        return 0
    
    if args.clean:
        clean_cache()
        return 0
    
    if args.coverage_report:
        generate_coverage_report()
        return 0
    
    # Run tests
    exit_code = 0
    
    if not args.lint and not args.type_check:
        # Run the main test suite
        exit_code = run_tests(args)
        
        # Generate coverage report if coverage was enabled
        if args.coverage and exit_code == 0:
            generate_coverage_report()
    
    # Run additional checks if requested
    if args.lint:
        if not run_lint():
            exit_code = 1
    
    if args.type_check:
        if not run_type_check():
            exit_code = 1
    
    if exit_code == 0:
        print("\n✓ All checks passed!")
    else:
        print("\n✗ Some checks failed!")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())