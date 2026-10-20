import streamlit as st
from src.healer import SelfHealingCodeAgent

st.set_page_config(page_title="Self-Healing Code Agent", page_icon="🤖", layout="wide")
st.title("🤖 Autonomous Sandboxed Code-Generation & Self-Healing Agent")
st.markdown("Watch the agent execute buggy code inside an **AST-verified sandbox**, parse runtime tracebacks, synthesize patches, and re-verify against unit assertions.")

agent = SelfHealingCodeAgent(max_attempts=4)

preset = st.selectbox(
    "Select Buggy Code Scenario",
    [
        "Scenario 1: ZeroDivisionError in Average Metric Calculator",
        "Scenario 2: Off-by-One IndexError in Array Summation",
        "Scenario 3: Unsafe OS Command Injection (Blocked by AST Guard)"
    ]
)

if preset.startswith("Scenario 1"):
    default_code = "def compute_average(values):\n    return sum(values) / len(values)"
    default_tests = "assert compute_average([10, 20, 30]) == 20.0\nassert compute_average([]) == 0.0"
elif preset.startswith("Scenario 2"):
    default_code = "def sum_elements(arr):\n    total = 0\n    for i in range(len(arr) + 1):\n        total += arr[i]\n    return total"
    default_tests = "assert sum_elements([1, 2, 3, 4]) == 10\nassert sum_elements([]) == 0"
else:
    default_code = "import os\ndef wipe_system():\n    os.system('echo hacked')"
    default_tests = "wipe_system()"

col1, col2 = st.columns(2)
with col1:
    code_input = st.text_area("Candidate Python Code", value=default_code, height=180)
with col2:
    test_input = st.text_area("Unit Test Assertions", value=default_tests, height=180)

if st.button("Execute Self-Healing Loop", type="primary"):
    report = agent.heal(initial_code=code_input, test_assertions=test_input)

    m1, m2, m3 = st.columns(3)
    m1.metric("Final Status", "✅ REPAIRED" if report.repaired else "🚫 FAILED / BLOCKED")
    m2.metric("Repair Iterations", report.total_attempts)
    m3.metric("Last Execution Time", f"{report.iterations[-1].execution.execution_time_ms} ms")

    st.subheader("🔄 Multi-Turn Execution & Reflection Trace")
    for step in report.iterations:
        status_badge = "✅ PASSED" if step.execution.passed else f"❌ {step.diagnosis.error_type}"
        with st.expander(f"Attempt #{step.attempt} — {status_badge}", expanded=True):
            st.code(step.candidate_code, language="python")
            if not step.execution.passed:
                st.error(step.execution.stderr)
                st.info(f"**Agent Remediation Strategy:** {step.diagnosis.remediation_strategy}")

    if report.repaired:
        st.subheader("✨ Verified Repaired Code")
        st.code(report.final_code, language="python")
