import ast
import sys
import subprocess
import tempfile
import os
import time
from typing import Set, Tuple
from pydantic import BaseModel

class ExecutionResult(BaseModel):
    passed: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: float
    security_violation: bool = False

class SecurePythonSandbox:
    """
    Two-stage sandbox:
    1. Static Abstract Syntax Tree (AST) inspection blocking dangerous modules and builtins.
    2. Isolated subprocess execution with strict wall-clock timeout enforcement.
    """

    FORBIDDEN_MODULES: Set[str] = {
        "os", "sys", "subprocess", "shutil", "socket",
        "urllib", "requests", "http", "ftplib", "pickle", "ctypes"
    }

    FORBIDDEN_BUILTINS: Set[str] = {
        "eval", "exec", "compile", "__import__", "open"
    }

    def __init__(self, timeout_seconds: float = 3.0):
        self.timeout_seconds = timeout_seconds

    def validate_ast(self, source_code: str) -> Tuple[bool, str]:
        """Statically parses Python code to block unsafe imports or calls before execution."""
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            return False, f"SyntaxError at line {e.lineno}: {e.msg}"

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_mod = alias.name.split(".")[0]
                    if root_mod in self.FORBIDDEN_MODULES:
                        return False, f"SecurityViolation: Import of '{root_mod}' is prohibited in sandbox."
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_mod = node.module.split(".")[0]
                    if root_mod in self.FORBIDDEN_MODULES:
                        return False, f"SecurityViolation: Import from '{root_mod}' is prohibited in sandbox."
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in self.FORBIDDEN_BUILTINS:
                    return False, f"SecurityViolation: Built-in call '{node.func.id}()' is prohibited."

        return True, "AST security verification passed."

    def execute(self, code: str, test_assertions: str = "") -> ExecutionResult:
        full_script = f"{code.strip()}\n\n# --- Unit Assertions ---\n{test_assertions.strip()}\n"
        is_safe, message = self.validate_ast(full_script)

        if not is_safe:
            is_sec = message.startswith("SecurityViolation")
            return ExecutionResult(
                passed=False,
                stdout="",
                stderr=message,
                exit_code=1,
                execution_time_ms=0.0,
                security_violation=is_sec
            )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as tmp:
            tmp.write(full_script)
            tmp_path = tmp.name

        t0 = time.perf_counter()
        try:
            proc = subprocess.run(
                [sys.executable, "-I", tmp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            return ExecutionResult(
                passed=(proc.returncode == 0),
                stdout=proc.stdout.strip(),
                stderr=proc.stderr.strip(),
                exit_code=proc.returncode,
                execution_time_ms=round(elapsed_ms, 2),
                security_violation=False
            )
        except subprocess.TimeoutExpired:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            return ExecutionResult(
                passed=False,
                stdout="",
                stderr=f"TimeoutError: Execution exceeded {self.timeout_seconds}s limit.",
                exit_code=124,
                execution_time_ms=round(elapsed_ms, 2),
                security_violation=False
            )
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
