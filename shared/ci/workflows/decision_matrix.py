"""
Code Duplication Decision Matrix
Determines whether to automatically fix duplicates or create issues for human review
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum


class ActionType(Enum):
    AUTOMATIC_FIX = "automatic_fix"
    HUMAN_REVIEW = "human_review"
    SKIP = "skip"


@dataclass
class Decision:
    """CTO decision matrix result for code duplication handling."""

    action: ActionType
    justification: str
    metadata: Dict[str, Any]
    confidence: str
    risk_score: float


@dataclass
class DuplicationContext:
    """Context for evaluating code duplication"""

    similarity_score: float
    file_count: int
    total_line_count: int
    symbol_types: List[str]  # ['function', 'class', 'method', 'variable']
    cross_module_impact: bool
    test_coverage_percentage: float
    cyclomatic_complexity: int
    dependency_count: int
    is_public_api: bool
    has_documentation: bool
    last_modified_days_ago: int


class DecisionMatrix:
    """
    CTO-approved decision criteria for code duplication handling

    Philosophy:
    - Favor automated fixes for low-risk, high-confidence scenarios
    - Require human review for architectural impacts or complex refactoring
    - Skip trivial duplications that don't impact maintainability
    """

    # Risk scoring weights
    RISK_WEIGHTS = {
        "cross_module": 3.0,
        "public_api": 4.0,
        "high_dependencies": 2.5,
        "low_test_coverage": 2.0,
        "high_complexity": 1.5,
        "recent_changes": 1.5,
        "large_scope": 2.0,
    }

    @classmethod
    def evaluate(cls, context: DuplicationContext) -> Decision:
        """
        Evaluate duplication context and return action decision

        Returns:
            Decision object with action, justification, metadata, confidence, and risk_score
        """

        # SKIP CRITERIA - Not worth addressing
        if cls._should_skip(context):
            return Decision(
                action=ActionType.SKIP,
                justification="Duplication below actionable threshold",
                metadata={"recommended_approach": "no_action"},
                confidence="high",
                risk_score=0.0,
            )

        # Calculate risk score
        risk_score = cls._calculate_risk_score(context)

        # Determine confidence level
        confidence = cls._calculate_confidence(context)

        # AUTOMATIC FIX CRITERIA
        if cls._can_auto_fix(context, risk_score, confidence):
            return Decision(
                action=ActionType.AUTOMATIC_FIX,
                justification=cls._get_auto_fix_rationale(
                    context, risk_score, confidence
                ),
                metadata={
                    "recommended_approach": cls._get_fix_approach(context),
                },
                confidence=confidence,
                risk_score=risk_score,
            )

        # HUMAN REVIEW CRITERIA (everything else above skip threshold)
        return Decision(
            action=ActionType.HUMAN_REVIEW,
            justification=cls._get_human_review_rationale(
                context, risk_score, confidence
            ),
            metadata={
                "concerns": cls._get_concerns(context, risk_score),
            },
            confidence=confidence,
            risk_score=risk_score,
        )

    @classmethod
    def _should_skip(cls, context: DuplicationContext) -> bool:
        """Determine if duplication should be skipped entirely"""

        # Skip trivial duplications
        if context.total_line_count < 5:
            return True

        # Skip low-similarity matches unless they're exact
        if context.similarity_score < 0.80 and context.total_line_count < 20:
            return True

        # Skip simple variable duplications
        if context.symbol_types == ["variable"] and context.total_line_count < 10:
            return True

        # Skip test fixture duplications (common and often intentional)
        if all(
            "test" in st.lower() or "fixture" in st.lower()
            for st in context.symbol_types
        ):
            return True

        return False

    @classmethod
    def _calculate_risk_score(cls, context: DuplicationContext) -> float:
        """Calculate risk score (0-100) for the refactoring"""

        risk_score = 0.0

        # Cross-module impact (highest risk)
        if context.cross_module_impact:
            risk_score += 20 * cls.RISK_WEIGHTS["cross_module"]

        # Public API changes
        if context.is_public_api:
            risk_score += 25 * cls.RISK_WEIGHTS["public_api"]

        # High dependency count (>5 dependencies)
        if context.dependency_count > 5:
            risk_score += 15 * cls.RISK_WEIGHTS["high_dependencies"]
        elif context.dependency_count > 2:
            risk_score += 8 * cls.RISK_WEIGHTS["high_dependencies"]

        # Low test coverage (<50%)
        if context.test_coverage_percentage < 50:
            risk_score += 15 * cls.RISK_WEIGHTS["low_test_coverage"]
        elif context.test_coverage_percentage < 80:
            risk_score += 8 * cls.RISK_WEIGHTS["low_test_coverage"]

        # High complexity (>10)
        if context.cyclomatic_complexity > 10:
            risk_score += 10 * cls.RISK_WEIGHTS["high_complexity"]
        elif context.cyclomatic_complexity > 5:
            risk_score += 5 * cls.RISK_WEIGHTS["high_complexity"]

        # Recent changes (touched in last 7 days)
        if context.last_modified_days_ago < 7:
            risk_score += 10 * cls.RISK_WEIGHTS["recent_changes"]
        elif context.last_modified_days_ago < 30:
            risk_score += 5 * cls.RISK_WEIGHTS["recent_changes"]

        # Large scope (many files)
        if context.file_count > 10:
            risk_score += 15 * cls.RISK_WEIGHTS["large_scope"]
        elif context.file_count > 5:
            risk_score += 8 * cls.RISK_WEIGHTS["large_scope"]

        return min(100, risk_score)  # Cap at 100

    @classmethod
    def _calculate_confidence(cls, context: DuplicationContext) -> str:
        """Calculate confidence level for the action"""

        if context.similarity_score >= 0.95:
            # Near-identical code
            if context.test_coverage_percentage >= 80:
                return "very_high"
            elif context.test_coverage_percentage >= 50:
                return "high"
            else:
                return "medium"
        elif context.similarity_score >= 0.85:
            # Very similar code
            if context.test_coverage_percentage >= 80:
                return "high"
            else:
                return "medium"
        else:
            # Moderately similar code
            return "low"

    @classmethod
    def _can_auto_fix(
        cls, context: DuplicationContext, risk_score: float, confidence: str
    ) -> bool:
        """
        Determine if automatic fix is appropriate

        CTO Criteria: Low risk, high confidence, clear extraction pattern
        """

        # Never auto-fix public APIs
        if context.is_public_api:
            return False

        # Never auto-fix cross-module impacts without high confidence
        if context.cross_module_impact and confidence != "very_high":
            return False

        # Risk threshold by confidence
        risk_thresholds = {
            "very_high": 40,  # Can handle moderate risk with very high confidence
            "high": 25,  # Only low risk with high confidence
            "medium": 15,  # Very low risk with medium confidence
            "low": 0,  # Never auto-fix with low confidence
        }

        if risk_score > risk_thresholds.get(confidence, 0):
            return False

        # Specific auto-fix scenarios (positive criteria)

        # Scenario 1: Simple internal function extraction
        if (
            context.similarity_score >= 0.90
            and "function" in context.symbol_types
            and not context.cross_module_impact
            and context.file_count <= 3
            and context.test_coverage_percentage >= 70
        ):
            return True

        # Scenario 2: Private method consolidation within same module
        if (
            context.similarity_score >= 0.85
            and "method" in context.symbol_types
            and not context.cross_module_impact
            and not context.is_public_api
            and context.dependency_count <= 3
        ):
            return True

        # Scenario 3: Variable/constant extraction
        if (
            context.similarity_score >= 0.95
            and "variable" in context.symbol_types
            and context.total_line_count <= 50
            and context.cyclomatic_complexity <= 3
        ):
            return True

        # Scenario 4: Well-tested utility extraction
        if (
            context.test_coverage_percentage >= 90
            and context.similarity_score >= 0.88
            and context.dependency_count <= 5
            and risk_score <= 20
        ):
            return True

        return False

    @classmethod
    def _get_auto_fix_rationale(
        cls, context: DuplicationContext, risk_score: float, confidence: str
    ) -> str:
        """Generate rationale for automatic fix decision"""

        rationale_parts = [
            f"Automatic fix approved: risk_score={risk_score:.1f}, confidence={confidence}."
        ]

        if context.similarity_score >= 0.95:
            rationale_parts.append("Near-identical code duplication detected.")

        if context.test_coverage_percentage >= 80:
            rationale_parts.append(
                f"Strong test coverage ({context.test_coverage_percentage:.0f}%) provides safety net."
            )

        if not context.cross_module_impact:
            rationale_parts.append("Changes isolated to single module.")

        if context.dependency_count <= 2:
            rationale_parts.append("Minimal dependency impact.")

        return " ".join(rationale_parts)

    @classmethod
    def _get_human_review_rationale(
        cls, context: DuplicationContext, risk_score: float, confidence: str
    ) -> str:
        """Generate rationale for human review decision"""

        rationale_parts = [
            f"Human review required: risk_score={risk_score:.1f}, confidence={confidence}."
        ]

        # Add primary concerns
        if context.is_public_api:
            rationale_parts.append(
                "PUBLIC API CHANGE - requires careful consideration."
            )

        if context.cross_module_impact:
            rationale_parts.append(
                "Cross-module refactoring impacts system architecture."
            )

        if context.dependency_count > 5:
            rationale_parts.append(
                f"High dependency count ({context.dependency_count}) requires impact analysis."
            )

        if context.test_coverage_percentage < 50:
            rationale_parts.append(
                f"Low test coverage ({context.test_coverage_percentage:.0f}%) increases risk."
            )

        if context.cyclomatic_complexity > 10:
            rationale_parts.append(
                f"High complexity (CC={context.cyclomatic_complexity}) suggests careful refactoring needed."
            )

        if context.file_count > 5:
            rationale_parts.append(
                f"Large scope ({context.file_count} files) requires coordinated changes."
            )

        return " ".join(rationale_parts)

    @classmethod
    def _get_fix_approach(cls, context: DuplicationContext) -> str:
        """Recommend specific fix approach for automatic fixes"""

        if "function" in context.symbol_types:
            if context.file_count == 2:
                return "extract_to_shared_utility"
            else:
                return "create_common_module"

        if "method" in context.symbol_types:
            if not context.cross_module_impact:
                return "extract_to_base_class"
            else:
                return "create_shared_mixin"

        if "variable" in context.symbol_types:
            return "extract_to_constants"

        return "refactor_to_shared_component"

    @classmethod
    def _get_concerns(cls, context: DuplicationContext, risk_score: float) -> List[str]:
        """List specific concerns for human review"""

        concerns = []

        if context.is_public_api:
            concerns.append("Breaking API changes possible")

        if context.cross_module_impact:
            concerns.append("Architectural boundaries may be violated")

        if context.dependency_count > 5:
            concerns.append("Ripple effects across multiple components")

        if context.test_coverage_percentage < 50:
            concerns.append("Insufficient test safety net")

        if context.cyclomatic_complexity > 10:
            concerns.append("Complex logic requires careful extraction")

        if context.last_modified_days_ago < 7:
            concerns.append("Recently modified code - may conflict with ongoing work")

        if risk_score > 60:
            concerns.append("High overall risk - consider phased approach")

        return concerns


# Example usage and testing
if __name__ == "__main__":
    # Test case 1: Simple function duplication - should auto-fix
    simple_dup = DuplicationContext(
        similarity_score=0.92,
        file_count=2,
        total_line_count=25,
        symbol_types=["function"],
        cross_module_impact=False,
        test_coverage_percentage=85,
        cyclomatic_complexity=3,
        dependency_count=1,
        is_public_api=False,
        has_documentation=True,
        last_modified_days_ago=45,
    )

    action, rationale, metadata = DecisionMatrix.evaluate(simple_dup)
    print(f"Simple duplication: {action.value}")
    print(f"Rationale: {rationale}")
    print(f"Metadata: {metadata}\n")

    # Test case 2: Complex cross-module - should require human review
    complex_dup = DuplicationContext(
        similarity_score=0.88,
        file_count=8,
        total_line_count=150,
        symbol_types=["class", "method"],
        cross_module_impact=True,
        test_coverage_percentage=45,
        cyclomatic_complexity=12,
        dependency_count=8,
        is_public_api=True,
        has_documentation=True,
        last_modified_days_ago=3,
    )

    action, rationale, metadata = DecisionMatrix.evaluate(complex_dup)
    print(f"Complex duplication: {action.value}")
    print(f"Rationale: {rationale}")
    print(f"Metadata: {metadata}\n")

    # Test case 3: Trivial duplication - should skip
    trivial_dup = DuplicationContext(
        similarity_score=0.78,
        file_count=2,
        total_line_count=4,
        symbol_types=["variable"],
        cross_module_impact=False,
        test_coverage_percentage=90,
        cyclomatic_complexity=1,
        dependency_count=0,
        is_public_api=False,
        has_documentation=False,
        last_modified_days_ago=180,
    )

    action, rationale, metadata = DecisionMatrix.evaluate(trivial_dup)
    print(f"Trivial duplication: {action.value}")
    print(f"Rationale: {rationale}")
    print(f"Metadata: {metadata}")
