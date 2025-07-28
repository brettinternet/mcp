"""Command execution utilities for mise operations."""

import subprocess
from typing import Any, Dict, List, Optional


async def run_mise_command(args: List[str], cwd: Optional[str] = None) -> Dict[str, Any]:
    """Run a mise command and return the result."""
    try:
        # Get mise environment variables
        env_result = subprocess.run(
            ["mise", "env", "-s", "bash"],
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        
        # Parse environment variables from mise
        import os
        env = os.environ.copy()
        if env_result.returncode == 0:
            for line in env_result.stdout.strip().split('\n'):
                if line.startswith('export '):
                    # Parse export VAR=value or export VAR="value"
                    line = line[7:]  # Remove 'export '
                    if '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        env[key] = value
        
        result = subprocess.run(
            ["mise"] + args,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30,
            env=env,
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Command timed out after 30 seconds",
            "returncode": -1,
        }
    except FileNotFoundError:
        return {
            "success": False,
            "stdout": "",
            "stderr": "mise command not found. Please ensure mise is installed and in PATH.",
            "returncode": -1,
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Error running command: {str(e)}",
            "returncode": -1,
        }


async def run_command_with_mise_env(command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
    """Run a command with mise environment variables loaded."""
    try:
        # Get mise environment variables
        env_result = subprocess.run(
            ["mise", "env", "-s", "bash"],
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        
        # Parse environment variables from mise
        import os
        env = os.environ.copy()
        if env_result.returncode == 0:
            for line in env_result.stdout.strip().split('\n'):
                if line.startswith('export '):
                    # Parse export VAR=value or export VAR="value"
                    line = line[7:]  # Remove 'export '
                    if '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        env[key] = value
        
        # Run the command with mise environment
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30,
            env=env,
            shell=True,
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Command timed out after 30 seconds",
            "returncode": -1,
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Error running command: {str(e)}",
            "returncode": -1,
        }
