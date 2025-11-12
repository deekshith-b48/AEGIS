#!/usr/bin/env python3
"""
Test Runner for Project AEGIS
Comprehensive test execution and reporting script
"""

import os
import sys
import subprocess
import argparse
import json
from datetime import datetime
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return the result"""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    return result

def run_unit_tests(coverage=True, verbose=False):
    """Run unit tests"""
    print("\n" + "="*50)
    print("RUNNING UNIT TESTS")
    print("="*50)

    cmd = ["python", "-m", "pytest"]

    # Add unit test marker
    cmd.extend(["-m", "unit or not integration"])

    # Add verbosity
    if verbose:
        cmd.append("-v")

    # Add coverage if requested
    if coverage:
        cmd.extend([
            "--cov=backend",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov/unit",
            "--cov-fail-under=80"
        ])

    # Add test files
    cmd.extend([
        "tests/test_auth.py",
        "tests/test_database.py",
        "tests/test_api.py",
        "tests/test_websocket.py"
    ])

    result = run_command(cmd)

    if result.returncode == 0:
        print("✅ Unit tests passed!")
    else:
        print("❌ Unit tests failed!")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

    return result.returncode == 0

def run_integration_tests(verbose=False):
    """Run integration tests"""
    print("\n" + "="*50)
    print("RUNNING INTEGRATION TESTS")
    print("="*50)

    cmd = ["python", "-m", "pytest"]

    # Add integration test marker
    cmd.extend(["-m", "integration"])

    # Add verbosity
    if verbose:
        cmd.append("-v")

    # Add test files
    cmd.extend([
        "tests/test_integration.py"
    ])

    result = run_command(cmd)

    if result.returncode == 0:
        print("✅ Integration tests passed!")
    else:
        print("❌ Integration tests failed!")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

    return result.returncode == 0

def run_all_tests(coverage=True, verbose=False, parallel=False):
    """Run all tests"""
    print("\n" + "="*50)
    print("RUNNING ALL TESTS")
    print("="*50)

    cmd = ["python", "-m", "pytest"]

    # Add verbosity
    if verbose:
        cmd.append("-v")

    # Add parallel execution if requested
    if parallel:
        cmd.extend(["-n", "auto"])

    # Add coverage if requested
    if coverage:
        cmd.extend([
            "--cov=backend",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov/all",
            "--cov-report=xml:coverage.xml",
            "--cov-fail-under=80"
        ])

    # Add test files
    cmd.extend(["tests/"])

    result = run_command(cmd)

    if result.returncode == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

    return result.returncode == 0

def run_performance_tests():
    """Run performance benchmarks"""
    print("\n" + "="*50)
    print("RUNNING PERFORMANCE TESTS")
    print("="*50)

    cmd = ["python", "-m", "pytest"]
    cmd.extend([
        "-m", "benchmark",
        "--benchmark-only",
        "--benchmark-json=benchmark_results.json",
        "tests/test_performance.py"  # Would need to create this
    ])

    result = run_command(cmd)

    if result.returncode == 0:
        print("✅ Performance tests completed!")
        if os.path.exists("benchmark_results.json"):
            print("📊 Benchmark results saved to benchmark_results.json")
    else:
        print("❌ Performance tests failed!")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

    return result.returncode == 0

def run_security_tests():
    """Run security tests"""
    print("\n" + "="*50)
    print("RUNNING SECURITY TESTS")
    print("="*50)

    # Run bandit security linter
    print("Running Bandit security analysis...")
    bandit_cmd = ["bandit", "-r", "backend/", "-f", "json", "-o", "bandit_report.json"]
    bandit_result = run_command(bandit_cmd)

    if bandit_result.returncode == 0:
        print("✅ No high-severity security issues found!")
    else:
        print("⚠️ Security issues detected. Check bandit_report.json")

    # Run safety check for dependencies
    print("Running Safety dependency check...")
    safety_cmd = ["safety", "check", "--json", "--output", "safety_report.json"]
    safety_result = run_command(safety_cmd)

    if safety_result.returncode == 0:
        print("✅ No known security vulnerabilities in dependencies!")
    else:
        print("⚠️ Dependency vulnerabilities detected. Check safety_report.json")

    return bandit_result.returncode == 0 and safety_result.returncode == 0

def run_code_quality_tests():
    """Run code quality tests"""
    print("\n" + "="*50)
    print("RUNNING CODE QUALITY TESTS")
    print("="*50)

    quality_passed = True

    # Run black formatting check
    print("Checking code formatting with Black...")
    black_cmd = ["black", "--check", "--diff", "backend/"]
    black_result = run_command(black_cmd)

    if black_result.returncode == 0:
        print("✅ Code formatting is correct!")
    else:
        print("❌ Code formatting issues found. Run 'black backend/' to fix.")
        quality_passed = False

    # Run isort import sorting check
    print("Checking import sorting with isort...")
    isort_cmd = ["isort", "--check-only", "--diff", "backend/"]
    isort_result = run_command(isort_cmd)

    if isort_result.returncode == 0:
        print("✅ Import sorting is correct!")
    else:
        print("❌ Import sorting issues found. Run 'isort backend/' to fix.")
        quality_passed = False

    # Run flake8 linting
    print("Running Flake8 linting...")
    flake8_cmd = ["flake8", "backend/", "--format=json", "--output-file=flake8_report.json"]
    flake8_result = run_command(flake8_cmd)

    if flake8_result.returncode == 0:
        print("✅ No linting issues found!")
    else:
        print("⚠️ Linting issues found. Check flake8_report.json")
        quality_passed = False

    # Run mypy type checking
    print("Running MyPy type checking...")
    mypy_cmd = ["mypy", "backend/", "--json-report", "mypy_report"]
    mypy_result = run_command(mypy_cmd)

    if mypy_result.returncode == 0:
        print("✅ No type issues found!")
    else:
        print("⚠️ Type issues found. Check mypy_report/index.json")
        quality_passed = False

    return quality_passed

def generate_test_report(results):
    """Generate comprehensive test report"""
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "results": results,
        "summary": {
            "total_suites": len(results),
            "passed": sum(1 for r in results.values() if r["passed"]),
            "failed": sum(1 for r in results.values() if not r["passed"]),
            "success_rate": sum(1 for r in results.values() if r["passed"]) / len(results) * 100
        }
    }

    # Save report
    with open("test_report.json", "w") as f:
        json.dump(report, f, indent=2)

    # Print summary
    print("\n" + "="*50)
    print("TEST REPORT SUMMARY")
    print("="*50)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Total Test Suites: {report['summary']['total_suites']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Success Rate: {report['summary']['success_rate']:.1f}%")

    print("\nDetailed Results:")
    for suite, result in results.items():
        status = "✅ PASSED" if result["passed"] else "❌ FAILED"
        print(f"  {suite}: {status}")

    print(f"\n📄 Full report saved to: test_report.json")

    return report

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Project AEGIS Test Runner")
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run unit tests only"
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run integration tests only"
    )
    parser.add_argument(
        "--performance",
        action="store_true",
        help="Run performance tests"
    )
    parser.add_argument(
        "--security",
        action="store_true",
        help="Run security tests"
    )
    parser.add_argument(
        "--quality",
        action="store_true",
        help="Run code quality tests"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all tests (default)"
    )
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Skip coverage reporting"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Run tests in parallel"
    )

    args = parser.parse_args()

    # Set default to run all tests if no specific test type selected
    if not any([args.unit, args.integration, args.performance, args.security, args.quality]):
        args.all = True

    # Ensure we're in the correct directory
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent
    os.chdir(backend_dir)

    print(f"🧪 Project AEGIS Test Runner")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    # Run unit tests
    if args.unit or args.all:
        results["unit_tests"] = {
            "passed": run_unit_tests(coverage=not args.no_coverage, verbose=args.verbose)
        }

    # Run integration tests
    if args.integration or args.all:
        results["integration_tests"] = {
            "passed": run_integration_tests(verbose=args.verbose)
        }

    # Run all tests together (if not already run separately)
    if args.all and not args.unit and not args.integration:
        results["all_tests"] = {
            "passed": run_all_tests(
                coverage=not args.no_coverage,
                verbose=args.verbose,
                parallel=args.parallel
            )
        }

    # Run performance tests
    if args.performance:
        results["performance_tests"] = {
            "passed": run_performance_tests()
        }

    # Run security tests
    if args.security or args.all:
        results["security_tests"] = {
            "passed": run_security_tests()
        }

    # Run code quality tests
    if args.quality or args.all:
        results["code_quality_tests"] = {
            "passed": run_code_quality_tests()
        }

    # Generate final report
    report = generate_test_report(results)

    # Exit with appropriate code
    overall_success = all(result["passed"] for result in results.values())

    if overall_success:
        print("\n🎉 All tests passed! System is ready for deployment.")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Please review the report and fix issues.")
        sys.exit(1)

if __name__ == "__main__":
    main()