import re
from typing import Optional
from pydantic import BaseModel

class TracebackDiagnosis(BaseModel):
    error_type: str
    error_message: str
    line_number: Optional[int] = None
    remediation_strategy: str

class TracebackAnalyzer:
    """
    Parses raw Python stderr tracebacks into structured root-cause diagnostics
    and maps exception classes to deterministic code repair strategies.
    """

    STRATEGY_MAP = {
        "ZeroDivisionError": "Guard denominator with zero-check conditional before division.",
        "IndexError": "Add bounds check or fix off-by-one range/slice indexing.",
        "KeyError": "Replace direct bracket lookup with safe `.get(key, default)` access.",
        "TypeError": "Normalize operand types or cast inputs before arithmetic/concatenation.",
        "AssertionError": "Verify algorithmic operator logic (+, -, *, /) against test specification.",
        "SyntaxError": "Repair malformed indentation, missing colons, or unclosed parentheses.",
    }

    def diagnose(self, stderr: str) -> TracebackDiagnosis:
        if not stderr.strip():
            return TracebackDiagnosis(
                error_type="None",
                error_message="No error detected.",
                line_number=None,
                remediation_strategy="No action needed."
            )

        line_match = re.findall(r"line (\d+)", stderr)
        lineno = int(line_match[-1]) if line_match else None

        lines = [line.strip() for line in stderr.strip().splitlines() if line.strip()]
        last_line = lines[-1] if lines else "RuntimeError: Unknown failure"

        if ":" in last_line:
            err_type, err_msg = last_line.split(":", 1)
            err_type = err_type.strip()
            err_msg = err_msg.strip()
        else:
            err_type = last_line.strip()
            err_msg = "Unhandled exception"

        strategy = self.STRATEGY_MAP.get(
            err_type,
            "Inspect stack frame and patch offending expression."
        )

        return TracebackDiagnosis(
            error_type=err_type,
            error_message=err_msg,
            line_number=lineno,
            remediation_strategy=strategy
        )
