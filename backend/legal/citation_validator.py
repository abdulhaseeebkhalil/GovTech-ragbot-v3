"""
Citation Validator: Ensures statute citations are relevant and properly used

Validates that:
1. Every cited statute appears in controlling_law
2. Citations match the issue topic (no offences for budget disputes)
3. Definitions are included when terms are disputed
4. No freewheeling conclusions without statutory basis
"""

from typing import Dict, List, Any, Tuple
import re


class CitationValidator:
    """Validates legal citations for relevance and correctness"""

    def __init__(self):
        self.validation_errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []

    def validate_analysis(
        self,
        issues: List[Dict[str, Any]],
        controlling_law: List[Dict[str, Any]],
        holdings: List[Dict[str, Any]],
        facts_to_elements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Run all validation checks on legal analysis

        Args:
            issues: List of legal issues
            controlling_law: List of cited statute sections
            holdings: List of legal holdings/decisions
            facts_to_elements: Element-wise analysis

        Returns:
            Validation result with errors and warnings
        """
        self.validation_errors = []
        self.warnings = []

        # Rule 1: Citation Relevance
        self._validate_citation_relevance(controlling_law, holdings)

        # Rule 2: Topic Match
        self._validate_topic_match(issues, controlling_law)

        # Rule 3: Definitions First
        self._validate_definitions(issues, controlling_law)

        # Rule 4: No Freewheeling
        self._validate_statutory_basis(holdings, controlling_law)

        # Rule 5: Gaps Reporting
        self._validate_gaps_reporting(facts_to_elements, holdings)

        return {
            'valid': len(self.validation_errors) == 0,
            'errors': self.validation_errors,
            'warnings': self.warnings,
            'error_count': len(self.validation_errors),
            'warning_count': len(self.warnings)
        }

    def _validate_citation_relevance(
        self,
        controlling_law: List[Dict[str, Any]],
        holdings: List[Dict[str, Any]]
    ):
        """
        Validate that each statute cited appears in controlling_law
        and is referenced in analysis
        """
        # Extract all citations from controlling law
        controlling_citations = set()
        for law in controlling_law:
            section = law.get('section', '')
            if section:
                controlling_citations.add(section)

        # Check each holding references a controlling law citation
        for holding in holdings:
            holding_citations = holding.get('controlling_law', [])

            if not holding_citations:
                self.validation_errors.append({
                    'rule': 'CITATION_RELEVANCE',
                    'message': f"Holding for issue {holding.get('issue_id')} has no controlling law citations",
                    'severity': 'error'
                })

            # Verify citations are in controlling_law
            for citation in holding_citations:
                # Normalize citation
                normalized = self._normalize_citation(citation)
                if not any(self._normalize_citation(c) in normalized for c in controlling_citations):
                    self.warnings.append({
                        'rule': 'CITATION_RELEVANCE',
                        'message': f"Citation '{citation}' in holding not found in controlling_law list",
                        'severity': 'warning'
                    })

    def _validate_topic_match(
        self,
        issues: List[Dict[str, Any]],
        controlling_law: List[Dict[str, Any]]
    ):
        """
        Validate that cited sections match the issue topic
        (e.g., no offences/elections sections for budget disputes)
        """
        for issue in issues:
            issue_desc = issue.get('question', '') or issue.get('description', '')
            issue_type = self._classify_issue_type(issue_desc)

            # Check controlling law for topic mismatches
            for law in controlling_law:
                section_type = law.get('section_type', 'general')
                section = law.get('section', '')

                # Hard exclusions
                if issue_type in ['budget', 'authority']:
                    if section_type in ['offence', 'election']:
                        self.validation_errors.append({
                            'rule': 'TOPIC_MATCH',
                            'message': f"Issue is about {issue_type} but section '{section}' is type '{section_type}'",
                            'severity': 'error',
                            'issue_id': issue.get('id')
                        })

                elif issue_type == 'election':
                    if section_type in ['offence', 'budget_finance']:
                        self.validation_errors.append({
                            'rule': 'TOPIC_MATCH',
                            'message': f"Issue is about election but section '{section}' is type '{section_type}'",
                            'severity': 'error',
                            'issue_id': issue.get('id')
                        })

    def _validate_definitions(
        self,
        issues: List[Dict[str, Any]],
        controlling_law: List[Dict[str, Any]]
    ):
        """
        Validate that definitions are included when terms are disputed
        """
        # Extract key terms from issues
        key_terms = set()
        for issue in issues:
            question = issue.get('question', '') or issue.get('description', '')
            # Look for quoted terms or terms after "meaning of"
            quoted_terms = re.findall(r'["""]([^"""]+)["""]', question)
            key_terms.update([t.lower() for t in quoted_terms])

            meaning_terms = re.findall(r'meaning of\s+(\w+)', question, re.IGNORECASE)
            key_terms.update([t.lower() for t in meaning_terms])

        # Check if definitions are in controlling law for these terms
        if key_terms:
            has_definition_section = any(
                law.get('section_type') == 'definition'
                for law in controlling_law
            )

            if not has_definition_section:
                self.warnings.append({
                    'rule': 'DEFINITIONS_FIRST',
                    'message': f"Terms {list(key_terms)[:3]} appear disputed but no definition section in controlling_law",
                    'severity': 'warning'
                })

    def _validate_statutory_basis(
        self,
        holdings: List[Dict[str, Any]],
        controlling_law: List[Dict[str, Any]]
    ):
        """
        Validate that every conclusion has a paired statute citation
        """
        for holding in holdings:
            rationale = holding.get('rationale', '')
            citations = holding.get('controlling_law', [])

            if rationale and not citations:
                self.validation_errors.append({
                    'rule': 'NO_FREEWHEELING',
                    'message': f"Holding has rationale but no controlling law citation",
                    'severity': 'error',
                    'issue_id': holding.get('issue_id'),
                    'insufficient_basis': True
                })

    def _validate_gaps_reporting(
        self,
        facts_to_elements: List[Dict[str, Any]],
        holdings: List[Dict[str, Any]]
    ):
        """
        Validate that gaps are reported in missing_material
        """
        # Collect all elements with NOT_SATISFIED status
        unsatisfied_elements = [
            elem for elem in facts_to_elements
            if elem.get('status') == 'NOT_SATISFIED' or elem.get('status') == 'NOT_SHOWN'
        ]

        if unsatisfied_elements:
            # These should trigger gap warnings
            for elem in unsatisfied_elements:
                if not elem.get('gap') and not elem.get('evidence'):
                    self.warnings.append({
                        'rule': 'GAPS_REPORT',
                        'message': f"Element '{elem.get('element')}' not satisfied but no gap explanation",
                        'severity': 'warning'
                    })

    def _classify_issue_type(self, issue_text: str) -> str:
        """Classify issue type from description"""
        text_lower = issue_text.lower()

        if any(kw in text_lower for kw in ['budget', 'fund', 'allocation', 'expenditure', 'finance']):
            return 'budget'
        elif any(kw in text_lower for kw in ['power', 'authority', 'jurisdiction', 'competence']):
            return 'authority'
        elif any(kw in text_lower for kw in ['election', 'electoral', 'voting', 'delimitation']):
            return 'election'
        elif any(kw in text_lower for kw in ['offence', 'penalty', 'fine', 'punishment']):
            return 'offence'
        else:
            return 'general'

    def _normalize_citation(self, citation: str) -> str:
        """Normalize citation for comparison"""
        # Extract section number
        match = re.search(r'(?:§|section\s+)?(\d+[A-Z]?(?:\(\d+\))?)', citation, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return citation.lower()

    def get_validation_summary(self) -> str:
        """Get human-readable validation summary"""
        if not self.validation_errors and not self.warnings:
            return "✅ All validation checks passed"

        summary = []

        if self.validation_errors:
            summary.append(f"❌ {len(self.validation_errors)} validation error(s):")
            for error in self.validation_errors[:5]:
                summary.append(f"  - {error['rule']}: {error['message']}")

        if self.warnings:
            summary.append(f"⚠️  {len(self.warnings)} warning(s):")
            for warning in self.warnings[:5]:
                summary.append(f"  - {warning['rule']}: {warning['message']}")

        return '\n'.join(summary)
