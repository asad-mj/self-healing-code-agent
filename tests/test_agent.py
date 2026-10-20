from fastapi.testclient import TestClient
from main import app
from src.sandbox import SecurePythonSandbox
from src.healer import SelfHealingCodeAgent

def test_api_health():
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"

def test_ast_security_blocks_forbidden_imports():
    sandbox = SecurePythonSandbox()
    malicious_code = "import os\nos.listdir('.')"
    res = sandbox.execute(malicious_code)
    assert res.passed is False
    assert res.security_violation is True
    assert "SecurityViolation" in res.stderr

def test_self_healing_zero_division_repair():
    agent = SelfHealingCodeAgent(max_attempts=3)
    buggy = "def avg(nums):\n    return sum(nums) / len(nums)"
    assertions = "assert avg([2, 4]) == 3.0\nassert avg([]) == 0.0"

    report = agent.heal(initial_code=buggy, test_assertions=assertions)
    assert report.repaired is True
    assert report.total_attempts == 2
    assert "if (len(nums)) != 0 else 0.0" in report.final_code

def test_self_healing_index_error_repair():
    agent = SelfHealingCodeAgent(max_attempts=3)
    buggy = "def total(arr):\n    s = 0\n    for i in range(len(arr) + 1):\n        s += arr[i]\n    return s"
    assertions = "assert total([1, 2, 3]) == 6"

    report = agent.heal(initial_code=buggy, test_assertions=assertions)
    assert report.repaired is True
    assert report.total_attempts == 2

def test_api_heal_endpoint():
    with TestClient(app) as client:
        payload = {
            "buggy_code": "def get_Port(cfg):\n    return cfg['port']",
            "test_assertions": "assert get_Port({'port': 8080}) == 8080\nassert get_Port({}) == 0"
        }
        res = client.post("/heal", json=payload)
        assert res.status_code == 200
        body = res.json()
        assert body["repaired"] is True
