"""Canonical risk classification enums — single source of truth for domain and infrastructure."""

from enum import Enum


class RiskLevel(str, Enum):
    """Categorical risk classification labels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AnalysisMode(str, Enum):
    """Risk analysis execution mode."""

    rule = "rule"
    ml = "ml"
