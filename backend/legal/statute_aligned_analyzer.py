"""
Statute-Aligned Legal Analyzer

Main orchestrator for statute-grounded legal analysis.
Integrates: smart retrieval, first-principles reasoning, validation, and dual output.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import re

from .statute_parser import StatuteParser, classify_issue_type
from .smart_retriever import SmartRetriever
from .legal_reasoner import LegalReasoner
from .citation_validator import CitationValidator
from .legal_output_renderer import LegalOutputRenderer
from .vector_store import EnhancedQdrantVectorStore
from .gemini_client import EnhancedGeminiClient


class StatuteAlignedAnalyzer:
    """
    Statute-aligned legal analyzer for cases under known statutes

    Non-negotiable constraints:
    - No chain-of-thought output
    - Every conclusion cites specific section/clause/schedule
    - No irrelevant law (hard filters applied)
    - Definitions & Schedules prioritized
    - Explicit about missing evidence
    """

    def __init__(
        self,
        vector_store: EnhancedQdrantVectorStore,
        gemini_client: Optional[EnhancedGeminiClient] = None
    ):
        """
        Initialize analyzer

        Args:
            vector_store: Vector store with statute corpus
            gemini_client: Optional Gemini client for AI-enhanced analysis
        """
        self.vector_store = vector_store
        self.gemini_client = gemini_client

        # Initialize components
        self.statute_parser = StatuteParser()
        self.smart_retriever = SmartRetriever(vector_store)
        self.reasoner = LegalReasoner()
        self.validator = CitationValidator()
        self.renderer = LegalOutputRenderer()

    def analyze(
        self,
        narrative_text: str,
        petition_text: str,
        statute_name: str = "Khyber Pakhtunkhwa Local Government Act, 2013",
        facts: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main analysis entry point

        Args:
            narrative_text: Respondent's narrative/defense
            petition_text: Petitioner's/Applicant's filing
            statute_name: Name of governing statute
            facts: Optional additional facts/annexures

        Returns:
            Complete analysis with human-readable + JSON output
        """
        print(f"\n🔍 Starting Statute-Aligned Analysis")
        print(f"📜 Statute: {statute_name}")
        print(f"📄 Narrative length: {len(narrative_text)} chars")
        print(f"📋 Petition length: {len(petition_text)} chars")

        # Step 1: Identify legal questions from petition
        issues = self._identify_issues(petition_text, narrative_text)
        print(f"\n✅ Identified {len(issues)} legal issue(s)")

        # Step 2: Smart retrieval for each issue
        controlling_law = self._retrieve_controlling_law(
            issues, narrative_text, petition_text
        )
        print(f"✅ Retrieved {len(controlling_law)} controlling law section(s)")

        # Step 3: First-principles reasoning
        facts_to_elements, holdings = self._apply_first_principles(
            issues, controlling_law, narrative_text, petition_text, facts
        )
        print(f"✅ Analyzed {len(facts_to_elements)} legal element(s)")

        # Step 4: Validation
        validation_result = self._validate_analysis(
            issues, controlling_law, holdings, facts_to_elements
        )
        print(f"✅ Validation: {validation_result['error_count']} error(s), "
              f"{validation_result['warning_count']} warning(s)")

        # Step 5: Generate missing material list
        missing_material = self.reasoner.generate_missing_material_list()

        # Step 6: Suggest remedies (if applicable)
        remedies = self._suggest_remedies(holdings)

        # Step 7: Render outputs
        output = self.renderer.render_both(
            issues=issues,
            controlling_law=controlling_law,
            facts_to_elements=facts_to_elements,
            holdings=holdings,
            missing_material=missing_material,
            remedies=remedies
        )

        print(f"\n✅ Analysis complete. Output ready.")

        return {
            'human_readable': output['human_readable'],
            'json': output['json'],
            'validation': validation_result,
            'metadata': {
                'statute': statute_name,
                'analyzed_at': datetime.now().isoformat(),
                'issues_count': len(issues),
                'controlling_law_count': len(controlling_law),
                'validation_passed': validation_result['valid']
            }
        }

    def _identify_issues(
        self,
        petition_text: str,
        narrative_text: str
    ) -> List[Dict[str, Any]]:
        """
        Identify legal questions from petition

        Args:
            petition_text: Petition filing
            narrative_text: Narrative response

        Returns:
            List of legal issues
        """
        issues = []

        # Pattern 1: Look for explicit claims in petition
        # "The applicant contends that..."
        contention_pattern = r'(?:applicant|petitioner)\s+(?:contends|alleges|claims)\s+that\s+([^.]+\.)'
        for match in re.finditer(contention_pattern, petition_text, re.IGNORECASE):
            claim = match.group(1).strip()
            if len(claim) > 30:
                issues.append({
                    'id': f'ISSUE-{len(issues)+1}',
                    'question': f"Is {claim}",
                    'description': claim,
                    'statutes': [],
                    'source': 'petition'
                })

        # Pattern 2: Prayer/relief sought
        prayer_pattern = r'(?:prayer|relief|order)\s*:?\s*([^.]+\.)'
        for match in re.finditer(prayer_pattern, petition_text, re.IGNORECASE):
            prayer = match.group(1).strip()
            if len(prayer) > 30:
                issues.append({
                    'id': f'ISSUE-{len(issues)+1}',
                    'question': f"Is the petitioner entitled to: {prayer}",
                    'description': prayer,
                    'statutes': [],
                    'source': 'petition_prayer'
                })

        # Pattern 3: Extract section references and create issues
        section_refs = re.findall(
            r'(?:section|§)\s+(\d+[A-Z]?(?:\([a-z]\))?)',
            petition_text,
            re.IGNORECASE
        )

        # Fallback: If no explicit issues found, create generic ones
        if not issues:
            issues.append({
                'id': 'ISSUE-1',
                'question': 'Whether the actions described in the petition comply with applicable statutory provisions',
                'description': 'Compliance with statute',
                'statutes': [f"§{ref}" for ref in section_refs[:5]],
                'source': 'generic'
            })

        # Add section references to issues
        for issue in issues:
            if not issue.get('statutes'):
                issue['statutes'] = [f"§{ref}" for ref in section_refs[:3]]

        return issues[:5]  # Limit to top 5 issues

    def _retrieve_controlling_law(
        self,
        issues: List[Dict[str, Any]],
        narrative: str,
        petition: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieve controlling law for all issues

        Args:
            issues: Legal issues
            narrative: Narrative text
            petition: Petition text

        Returns:
            List of controlling law sections (deduplicated)
        """
        all_sections = []
        seen_keys = set()

        for issue in issues:
            # Smart retrieval for this issue
            sections = self.smart_retriever.retrieve_for_issue(
                issue, narrative, petition, limit=3
            )

            # Deduplicate
            for section in sections:
                key = self._get_section_key(section)
                if key not in seen_keys:
                    seen_keys.add(key)

                    # Format for controlling_law list
                    metadata = section.get('metadata', {})
                    all_sections.append({
                        'section': self._format_section_citation(metadata),
                        'text_snippet': section.get('text', '')[:300],
                        'why_relevant': self._explain_relevance(section, issue),
                        'section_type': metadata.get('section_type', 'general'),
                        'metadata': metadata
                    })

        return all_sections

    def _get_section_key(self, section: Dict[str, Any]) -> str:
        """Generate unique key for section"""
        metadata = section.get('metadata', {})
        section_num = metadata.get('section_number')
        schedule_ref = metadata.get('schedule_ref')

        if section_num:
            return f"section_{section_num}"
        elif schedule_ref:
            return f"schedule_{schedule_ref}"
        else:
            return f"hash_{hash(section.get('text', ''))}"

    def _format_section_citation(self, metadata: Dict[str, Any]) -> str:
        """Format section citation"""
        if metadata.get('section_number'):
            section_num = metadata['section_number']
            title = metadata.get('title', '')
            return f"§{section_num}: {title}" if title else f"§{section_num}"
        elif metadata.get('schedule_ref'):
            return metadata['schedule_ref']
        else:
            return "General provision"

    def _explain_relevance(
        self,
        section: Dict[str, Any],
        issue: Dict[str, Any]
    ) -> str:
        """Explain why section is relevant to issue"""
        section_type = section.get('metadata', {}).get('section_type', 'general')

        if section_type == 'definition':
            return "Defines key terms used in the issue"
        elif section_type == 'schedule':
            return "Enumerates applicable provisions"
        elif section_type == 'power':
            return "Governs powers and authority"
        elif section_type == 'function':
            return "Defines functions and duties"
        else:
            return "Addresses substantive legal question"

    def _apply_first_principles(
        self,
        issues: List[Dict[str, Any]],
        controlling_law: List[Dict[str, Any]],
        narrative: str,
        petition: str,
        facts: Optional[Dict[str, Any]]
    ) -> tuple:
        """
        Apply first-principles reasoning

        Returns:
            (facts_to_elements, holdings) tuple
        """
        # Parse narrative and petition for facts
        from .processing import DocumentProcessor
        processor = DocumentProcessor()
        processed = processor.process_case(narrative, petition)

        narrative_facts = processed['narrative']
        petition_facts = processed['petition']

        facts_to_elements = []
        holdings = []

        for issue in issues:
            # Get relevant controlling law for this issue
            issue_law = [
                law for law in controlling_law
                if any(statute in law['section'] for statute in issue.get('statutes', []))
            ]

            # If no specific law matched, use all controlling law
            if not issue_law:
                issue_law = controlling_law

            # Analyze with reasoner
            analysis = self.reasoner.analyze_issue(
                issue=issue,
                controlling_law=issue_law,
                narrative_facts=narrative_facts,
                petition_facts=petition_facts
            )

            # Extract facts_to_elements
            for elem in analysis['elements_analysis']:
                facts_to_elements.append({
                    'issue_id': issue['id'],
                    'element': elem['element'],
                    'support': elem.get('supporting_facts', ['Not shown'])[0] if elem.get('supporting_facts') else 'Not shown',
                    'evidence': elem.get('evidence', []),
                    'status': 'SATISFIED' if elem['satisfied'] else 'NOT_SATISFIED'
                })

            # Extract holding
            holdings.append({
                'issue_id': issue['id'],
                'decision': analysis['decision'],
                'rationale': analysis['rationale']
            })

        return facts_to_elements, holdings

    def _validate_analysis(
        self,
        issues: List[Dict[str, Any]],
        controlling_law: List[Dict[str, Any]],
        holdings: List[Dict[str, Any]],
        facts_to_elements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate analysis for correctness

        Returns:
            Validation result
        """
        return self.validator.validate_analysis(
            issues=issues,
            controlling_law=controlling_law,
            holdings=holdings,
            facts_to_elements=facts_to_elements
        )

    def _suggest_remedies(self, holdings: List[Dict[str, Any]]) -> List[str]:
        """Suggest remedies based on holdings"""
        remedies = []

        for holding in holdings:
            if holding['decision'] == 'SUSTAINED':
                remedies.append("Set aside impugned action and remand for reconsideration")
            elif holding['decision'] == 'NOT_SUSTAINED':
                remedies.append("Dismiss petition with no order as to costs")
            elif holding['decision'] == 'PARTLY_SUSTAINED':
                remedies.append("Grant partial relief and direct compliance")

        return list(set(remedies))


def analyze_legal_case(
    narrative: str,
    petition: str,
    vector_store: EnhancedQdrantVectorStore,
    statute_name: str = "KPK Local Government Act, 2013"
) -> Dict[str, Any]:
    """
    Convenience function for quick analysis

    Args:
        narrative: Respondent's narrative
        petition: Petitioner's filing
        vector_store: Initialized vector store with statute corpus
        statute_name: Governing statute name

    Returns:
        Analysis result with dual output
    """
    analyzer = StatuteAlignedAnalyzer(vector_store)
    return analyzer.analyze(narrative, petition, statute_name)
