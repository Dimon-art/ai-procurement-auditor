from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from apps.documents.models import Document


@dataclass
class RuleResult:
    """
    Normalized result returned by a business rule.
    """

    rule_id: str
    rule_name: str
    status: str
    severity: str
    weight: int
    message: str
    details: dict[str, Any] = field(default_factory=dict)


class Rule(ABC):
    """
    Base interface for document business rules.
    """

    rule_id: str
    rule_name: str
    severity: str
    weight: int

    @abstractmethod
    def evaluate(self, document: Document) -> RuleResult:
        """
        Evaluate a document and return a normalized rule result.
        """
        raise NotImplementedError