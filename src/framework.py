from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class FrameworkPillar:
    name: str
    decision_line: str


@dataclass(frozen=True)
class OrchestrationFramework:
    strategy: FrameworkPillar
    architecture: FrameworkPillar
    governance: FrameworkPillar
    economics: FrameworkPillar
    risk: FrameworkPillar


def build_framework(mode: str, topic: str, signals: Iterable[str]) -> OrchestrationFramework:
    corpus = " ".join(signal.lower() for signal in signals)
    expanded = mode in {"weekly", "autopsy"}

    strategy = "Align AI scope with one measurable business outcome and one decision owner."
    architecture = "Favor composable components and explicit integration boundaries with existing systems."
    governance = "Set ownership across data, model, security, and compliance before scale-up."
    economics = "Anchor funding on unit economics and build-vs-buy break-even scenarios."
    risk = "Track lock-in, model drift, and technical debt as first-class portfolio risks."

    if any(token in corpus for token in ["forecast", "demand", "stock", "planning"]):
        strategy = "Prioritize planning use cases that improve service level and cash cycle simultaneously."
        economics = "Tie investment release to forecast accuracy gains and working-capital impact."

    if any(token in corpus for token in ["warehouse", "robot", "automation", "last mile", "transport"]):
        architecture = "Synchronize physical operations data with AI decision loops to avoid local optimization."
        risk = "Model and process coupling can create hidden bottlenecks if interfaces are not stabilized early."

    if expanded:
        strategy += " Frame this as a portfolio thesis, not an isolated pilot."
        architecture += " Define migration paths and failure containment rules."
        governance += " Include escalation paths for policy breaches and model incidents."
        economics += " Include FinOps guardrails for inference, storage, and platform overhead."
        risk += " Force quarterly risk reviews with architecture and finance stakeholders."

    return OrchestrationFramework(
        strategy=FrameworkPillar("Strategy", strategy),
        architecture=FrameworkPillar("Architecture", architecture),
        governance=FrameworkPillar("Governance", governance),
        economics=FrameworkPillar("Economics", economics),
        risk=FrameworkPillar("Risk", risk),
    )


def framework_rows(framework: OrchestrationFramework) -> list[tuple[str, str]]:
    return [
        (framework.strategy.name, framework.strategy.decision_line),
        (framework.architecture.name, framework.architecture.decision_line),
        (framework.governance.name, framework.governance.decision_line),
        (framework.economics.name, framework.economics.decision_line),
        (framework.risk.name, framework.risk.decision_line),
    ]
