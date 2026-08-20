"""
Legal Reasoner: First-principles analysis with element-wise fact-to-law mapping

Performs statute-grounded reasoning without chain-of-thought output.
Maps facts to legal elements, identifies gaps, and produces tightly scoped conclusions.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class LegalElement:
    """Represents a single element of a legal rule"""
    element_name: str
    requirement: str
    satisfied: bool = False
    supporting_facts: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    gap: Optional[str] = None


@dataclass
class LegalHolding:
    """Represents a legal conclusion on an issue"""
    issue_id: str
    decision: str  # SUSTAINED | NOT_SUSTAINED | PARTLY_SUSTAINED
    rationale: str
    controlling_law: List[str]
    elements: List[LegalElement]


class LegalReasoner:
    """
    First-principles legal reasoner for statute-aligned analysis

    Performs element-wise fact-to-law mapping without exposing reasoning chains
    """

    def __init__(self):
        self.holdings: List[LegalHolding] = []

    def analyze_issue(
        self,
        issue: Dict[str, Any],
        controlling_law: List[Dict[str, Any]],
        narrative_facts: Dict[str, Any],
        petition_facts: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a single legal issue using first-principles reasoning

        Args:
            issue: Legal issue to analyze
            controlling_law: Relevant statute sections
            narrative_facts: Facts from narrative
            petition_facts: Facts from petition

        Returns:
            Analysis result with element-wise mapping
        """
        issue_description = issue.get('description', '')
        issue_id = issue.get('id', 'unknown')

        # Step 1: Decompose the legal rule from controlling law
        elements = self._decompose_legal_rule(controlling_law, issue_description)

        # Step 2: Map facts to elements
        elements = self._map_facts_to_elements(
            elements,
            narrative_facts,
            petition_facts,
            issue_description
        )

        # Step 3: Resolve conflicts and identify gaps
        elements = self._resolve_conflicts(elements)

        # Step 4: Determine holding (satisfied/not satisfied/partly)
        decision, rationale = self._determine_decision(elements, issue_description)

        # Build holding
        holding = LegalHolding(
            issue_id=issue_id,
            decision=decision,
            rationale=rationale,
            controlling_law=[self._format_citation(law) for law in controlling_law],
            elements=elements
        )

        self.holdings.append(holding)

        return {
            'issue_id': issue_id,
            'decision': decision,
            'rationale': rationale,
            'elements_analysis': [
                {
                    'element': elem.element_name,
                    'requirement': elem.requirement,
                    'satisfied': elem.satisfied,
                    'supporting_facts': elem.supporting_facts,
                    'evidence': elem.evidence,
                    'gap': elem.gap
                }
                for elem in elements
            ],
            'controlling_law_citations': holding.controlling_law
        }

    def _decompose_legal_rule(
        self,
        law_sections: List[Dict[str, Any]],
        issue_description: str
    ) -> List[LegalElement]:
        """
        Decompose statutory text into legal elements

        Args:
            law_sections: Relevant statute sections
            issue_description: Issue being analyzed

        Returns:
            List of LegalElements
        """
        elements = []

        for law_section in law_sections:
            text = law_section.get('text', '') or law_section.get('sliced_text', '')
            citation = self._format_citation(law_section)

            # Extract elements from statutory conditions
            # Pattern 1: "shall/must" + verb + object
            shall_pattern = r'(?:shall|must)[\s]+([^;.]+?)(?:[;.]|$)'
            for match in re.finditer(shall_pattern, text, re.IGNORECASE):
                requirement = match.group(1).strip()
                if len(requirement) > 10:  # Meaningful requirements only
                    elements.append(LegalElement(
                        element_name=f"Requirement from {citation}",
                        requirement=requirement,
                        satisfied=False
                    ))

            # Pattern 2: "subject to" conditions
            subject_to_pattern = r'subject to[\s]+([^;.]+?)(?:[;.]|$)'
            for match in re.finditer(subject_to_pattern, text, re.IGNORECASE):
                condition = match.group(1).strip()
                if len(condition) > 10:
                    elements.append(LegalElement(
                        element_name=f"Condition from {citation}",
                        requirement=condition,
                        satisfied=False
                    ))

            # Pattern 3: Negative constraints ("shall not", "prohibited")
            shall_not_pattern = r'(?:shall not|prohibited|forbidden|ultra vires)[\s]+([^;.]+?)(?:[;.]|$)'
            for match in re.finditer(shall_not_pattern, text, re.IGNORECASE):
                prohibition = match.group(1).strip()
                if len(prohibition) > 10:
                    elements.append(LegalElement(
                        element_name=f"Prohibition from {citation}",
                        requirement=f"Must not {prohibition}",
                        satisfied=False
                    ))

        # If no elements extracted, create generic element from issue
        if not elements:
            elements.append(LegalElement(
                element_name="Statutory compliance",
                requirement="Action must comply with applicable statutory provisions",
                satisfied=False
            ))

        return elements

    def _map_facts_to_elements(
        self,
        elements: List[LegalElement],
        narrative_facts: Dict[str, Any],
        petition_facts: Dict[str, Any],
        issue_description: str
    ) -> List[LegalElement]:
        """
        Map facts from narrative/petition to legal elements

        Args:
            elements: Legal elements to check
            narrative_facts: Facts from narrative
            petition_facts: Facts from petition
            issue_description: Issue context

        Returns:
            Elements with fact mappings
        """
        # Extract relevant facts from narrative
        narrative_claims = narrative_facts.get('claims', [])
        narrative_entities = narrative_facts.get('entities', {})

        # Extract relevant facts from petition
        petition_claims = petition_facts.get('claims', [])
        petition_entities = petition_facts.get('entities', {})

        for element in elements:
            requirement_lower = element.requirement.lower()

            # Check narrative for supporting facts
            for claim in narrative_claims:
                claim_text = claim.get('text', '').lower()
                if self._text_overlap(requirement_lower, claim_text) > 0.3:
                    element.supporting_facts.append(claim.get('text', ''))

            # Check petition for contradicting facts
            for claim in petition_claims:
                claim_text = claim.get('text', '').lower()
                if self._text_overlap(requirement_lower, claim_text) > 0.3:
                    element.evidence.append(f"Petition claim: {claim.get('text', '')}")

            # Determine if element is satisfied based on facts
            if element.supporting_facts:
                element.satisfied = True
            else:
                element.satisfied = False
                element.gap = f"No evidence shown for: {element.requirement}"

        return elements

    def _text_overlap(self, text1: str, text2: str) -> float:
        """
        Calculate text overlap ratio between two strings

        Args:
            text1: First text
            text2: Second text

        Returns:
            Overlap ratio (0.0 to 1.0)
        """
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def _resolve_conflicts(self, elements: List[LegalElement]) -> List[LegalElement]:
        """
        Resolve conflicting facts or identify evidentiary issues

        Args:
            elements: Legal elements with fact mappings

        Returns:
            Elements with conflicts resolved
        """
        for element in elements:
            # If both supporting and contradicting evidence exists
            if element.supporting_facts and element.evidence:
                # Mark as contested
                element.gap = "Factual dispute: contradicting evidence from parties"
                element.satisfied = False

        return elements

    def _determine_decision(
        self,
        elements: List[LegalElement],
        issue_description: str
    ) -> Tuple[str, str]:
        """
        Determine decision on issue based on element satisfaction

        Args:
            elements: Analyzed legal elements
            issue_description: Issue description

        Returns:
            (decision, rationale) tuple
        """
        if not elements:
            return "INSUFFICIENT_BASIS", "No controlling law elements identified"

        satisfied_count = sum(1 for e in elements if e.satisfied)
        total_count = len(elements)

        # All elements satisfied
        if satisfied_count == total_count:
            return "NOT_SUSTAINED", "All statutory requirements satisfied; petitioner's claim not established"

        # No elements satisfied
        elif satisfied_count == 0:
            gaps = [e.gap for e in elements if e.gap]
            rationale = f"Petitioner's claim sustained: {gaps[0] if gaps else 'statutory requirements not met'}"
            return "SUSTAINED", rationale

        # Partial satisfaction
        else:
            gaps = [e.gap for e in elements if e.gap and not e.satisfied]
            rationale = f"Partial compliance: {gaps[0] if gaps else 'some requirements met, others not shown'}"
            return "PARTLY_SUSTAINED", rationale

    def _format_citation(self, law_section: Dict[str, Any]) -> str:
        """Format citation from law section metadata"""
        metadata = law_section.get('metadata', {})

        if metadata.get('section_number'):
            return f"§{metadata['section_number']}"
        elif metadata.get('schedule_ref'):
            return metadata['schedule_ref']
        elif law_section.get('citation'):
            return law_section['citation']
        else:
            return "General provision"

    def generate_missing_material_list(self) -> List[str]:
        """
        Generate list of missing material that would change outcome

        Returns:
            List of missing documents/evidence
        """
        missing = []

        for holding in self.holdings:
            for element in holding.elements:
                if element.gap and not element.satisfied:
                    missing.append(element.gap)

        # Deduplicate
        return list(set(missing))

    def get_holdings_summary(self) -> List[Dict[str, Any]]:
        """
        Get summary of all holdings

        Returns:
            List of holding summaries
        """
        return [
            {
                'issue_id': holding.issue_id,
                'decision': holding.decision,
                'rationale': holding.rationale,
                'controlling_law': holding.controlling_law
            }
            for holding in self.holdings
        ]
