# 🤖 self-healing-code-agent: Autonomous Sandboxed Program Repair

[![Self-Healing Agent CI](https://github.com/asad-mj/self-healing-code-agent/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/asad-mj/self-healing-code-agent/actions/workflows/ci-cd.yml)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)](https://python.org)
[![AST Sandbox](https://img.shields.io/badge/Security-AST_Verified-success?style=flat-square)](src/sandbox.py)

An autonomous program synthesis and self-debugging agent that executes untrusted code inside a **two-stage AST + subprocess sandbox**, parses runtime tracebacks into structured diagnostics, and iteratively synthesizes patches until unit test assertions pass.

---

## 🏗️ Autonomous State Machine Architecture

```text
Candidate Code ──► [AST Static Security Gate] ──► [Isolated Subprocess Runner]
                                                               │
                   ┌───────────────────────────────────────────┴───────────┐
                   ▼ (Exit Code != 0)                                      ▼ (Exit Code == 0)
        [Traceback Root-Cause Parser]                           [Verified Production Code]
                   │
                   ▼
        [Iterative Patch Synthesizer] ──► (Loop Back to AST Gate)
