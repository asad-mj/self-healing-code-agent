import re
from typing import List
from pydantic import BaseModel
from src.sandbox import SecurePythonSandbox, ExecutionResult
from src.analyzer import TracebackAnalyzer, TracebackDiagnosis

class HealingIteration(BaseModel):
    attempt: int
    candidate_code: str
    execution: ExecutionResult
    diagnosis: TracebackDiagnosis

class HealingReport(BaseModel):
    repaired: bool
    total_attempts: int
    final_code: str
    iterations: List[HealingIteration]

class SelfHealingCodeAgent:
    """
    Autonomous multi-turn state machine:
    EXECUTE -> DIAGNOSE -> PATCH -> VERIFY
    """

    def __init__(self, max_attempts: int = 4):
        self.max_attempts = max_attempts
        self.sandbox = SecurePythonSandbox()
        self.analyzer = TracebackAnalyzer()

    def _synthesize_patch(self, code: str, diagnosis: TracebackDiagnosis) -> str:
        """Applies targeted AST/heuristic code transformations based on root-cause diagnosis."""
        err = diagnosis.error_type

        if err == "ZeroDivisionError":
            # Guard division operations `return a / b` or `total / len(x)`
            patched = re.sub(
                r"return\s+([^/\n]+)\s*/\s*([^\n]+)",
                r"return (\1 / \2) if (\2) != 0 else 0.0",
                code
            )
            if patched != code:
                return patched

        if err == "KeyError":
            # Convert dict['key'] to dict.get('key', 0)
            patched = re.sub(
                r"(\w+)\[['\"]([^'\"]+)['\"]\]",
                r"\1.get('\2', 0)",
                code
            )
            if patched != code:
                return patched

        if err == "IndexError":
            # Fix common off-by-one `range(len(arr) + 1)` -> `range(len(arr))`
            patched = re.sub(r"range\(\s*len\((\w+)\)\s*\+\s*1\s*\)", r"range(len(\1))", code)
            if patched != code:
                return patched

        if err == "AssertionError":
            # Fix inverted arithmetic sign in accumulation or return expressions
            if " - " in code:
                return code.replace(" - ", " + ", 1)

        return code

    def heal(self, initial_code: str, test_assertions: str) -> HealingReport:
        current_code = initial_code
        history: List[HealingIteration] = []

        for attempt in range(1, self.max_attempts + 1):
            exec_res = self.sandbox.execute(current_code, test_assertions)
            diag = self.analyzer.diagnose(exec_res.stderr)

            history.append(
                HealingIteration(
                    attempt=attempt,
                    candidate_code=current_code,
                    execution=exec_res,
                    diagnosis=diag
                )
            )

            if exec_res.passed or exec_res.security_violation:
                return HealingReport(
                    repaired=exec_res.passed,
                    total_attempts=attempt,
                    final_code=current_code,
                    iterations=history
                )

            next_code = self._synthesize_patch(current_code, diag)
            if next_code == current_code:
                break
            current_code = next_code

        return HealingReport(
            repaired=False,
            total_attempts=len(history),
            final_code=current_code,
            iterations=history
        )
