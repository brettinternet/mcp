#!/usr/bin/env python3
"""Quick test runner to verify the MCP server setup."""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and print the result."""
    print(f"\n🔍 {description}")
    print("=" * 50)

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )

        if result.returncode == 0:
            print(f"✅ Success: {description}")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ Failed: {description}")
            if result.stderr:
                print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False

    return True


def main():
    """Run tests and validation."""
    print("🚀 MCP Standup Server - Test Runner")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Error: Please run this from the mcp-standup-server directory")
        sys.exit(1)

    success = True

    # Install dependencies in development mode
    success &= run_command(
        "uv pip install -e .[dev]",
        "Installing development dependencies"
    )

    # Run linting
    success &= run_command(
        "python -m ruff check src tests --fix",
        "Running code linting (ruff)"
    )

    # Run code formatting
    success &= run_command(
        "python -m ruff format src tests --check",
        "Checking code formatting (ruff)"
    )

    # Run tests
    success &= run_command(
        "python -m pytest tests/ -v --tb=short",
        "Running test suite"
    )

    # Test basic imports
    success &= run_command(
        "python -c 'from standup_server.server import main; print(\"✅ Server imports work\")'",
        "Testing basic imports"
    )

    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! The MCP server is ready to use.")
        print("\nNext steps:")
        print("1. Set GITHUB_TOKEN and GITHUB_ORG environment variables")
        print("2. Start Claude with the MCP server configured")
        print("3. Use the standup tools to generate reports")
    else:
        print("❌ Some tests failed. Please check the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
