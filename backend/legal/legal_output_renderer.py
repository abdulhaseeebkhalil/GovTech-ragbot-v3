"""
Legal Output Renderer: Generates human-readable briefs and strict JSON output

Produces:
A) Human-readable brief with Issues, Controlling Law, Application, Findings
B) Machine-readable JSON conforming to strict schema
"""

import json
from typing import Dict, List, Any
from datetime import datetime


class LegalOutputRenderer:
    """Renders legal analysis in dual format: human-readable + JSON"""

    def render_human_readable(
        self,
        issues: List[Dict[str, Any]],
        controlling_law: List[Dict[str, Any]],
        facts_to_elements: List[Dict[str, Any]],
        holdings: List[Dict[str, Any]],
        missing_material: List[str]
    ) -> str:
        """
        Generate human-readable legal brief

        Args:
            issues: Legal issues
            controlling_law: Controlling law sections
            facts_to_elements: Element-wise analysis
            holdings: Legal holdings/decisions
            missing_material: Missing documents/evidence

        Returns:
            Formatted legal brief as markdown
        """
        sections = []

        # Header
        sections.append("# LEGAL ANALYSIS BRIEF")
        sections.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        sections.append("")

        # Issues
        sections.append("## ISSUES")
        sections.append("")
        for i, issue in enumerate(issues, 1):
            question = issue.get('question', '') or issue.get('description', '')
            statutes = ', '.join(issue.get('statutes', []))
            sections.append(f"**{i}. {question}**")
            if statutes:
                sections.append(f"   *Applicable provisions:* {statutes}")
            sections.append("")

        # Controlling Law
        sections.append("## CONTROLLING LAW")
        sections.append("")
        for i, law in enumerate(controlling_law, 1):
            section = law.get('section', '')
            snippet = law.get('text_snippet', '')[:200]
            why_relevant = law.get('why_relevant', '')

            sections.append(f"**{i}. {section}**")
            if snippet:
                sections.append(f"   > {snippet}...")
            if why_relevant:
                sections.append(f"   *Relevance:* {why_relevant}")
            sections.append("")

        # Application (Element-wise)
        sections.append("## APPLICATION")
        sections.append("")

        for elem in facts_to_elements:
            issue_id = elem.get('issue_id', '')
            element = elem.get('element', '')
            support = elem.get('support', '')
            status = elem.get('status', '')
            evidence = elem.get('evidence', [])

            sections.append(f"**Element:** {element}")
            sections.append(f"**Finding:** {support}")

            if evidence:
                sections.append(f"**Evidence:** {', '.join(evidence[:3])}")

            sections.append(f"**Status:** {status}")
            sections.append("")

        # Findings
        sections.append("## FINDINGS")
        sections.append("")

        for holding in holdings:
            issue_id = holding.get('issue_id', '')
            decision = holding.get('decision', '')
            rationale = holding.get('rationale', '')

            # Find corresponding issue
            issue = next((iss for iss in issues if iss.get('id') == issue_id), None)
            issue_text = issue.get('question', '') or issue.get('description', '') if issue else issue_id

            sections.append(f"**Issue:** {issue_text}")
            sections.append(f"**Decision:** {decision}")
            sections.append(f"**Rationale:** {rationale}")
            sections.append("")

        # Missing Material
        if missing_material:
            sections.append("## MISSING MATERIAL")
            sections.append("")
            sections.append("*The following documents/evidence would materially affect the outcome:*")
            sections.append("")
            for i, item in enumerate(missing_material, 1):
                sections.append(f"{i}. {item}")
            sections.append("")

        # Disclaimer
        sections.append("---")
        sections.append("*This analysis is generated based on statutory provisions and submitted pleadings. "
                       "It does not constitute legal advice. Consult with qualified legal counsel for specific guidance.*")

        return '\n'.join(sections)

    def render_json(
        self,
        issues: List[Dict[str, Any]],
        controlling_law: List[Dict[str, Any]],
        facts_to_elements: List[Dict[str, Any]],
        holdings: List[Dict[str, Any]],
        missing_material: List[str],
        remedies: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate strict JSON output

        Args:
            issues: Legal issues
            controlling_law: Controlling law sections
            facts_to_elements: Element-wise analysis
            holdings: Legal holdings
            missing_material: Missing evidence
            remedies: Suggested remedies (optional)

        Returns:
            JSON-serializable dictionary
        """
        return {
            "issues": [
                {
                    "id": issue.get('id', f"ISSUE-{i+1}"),
                    "question": issue.get('question', '') or issue.get('description', ''),
                    "statutes": issue.get('statutes', [])
                }
                for i, issue in enumerate(issues)
            ],
            "controlling_law": [
                {
                    "section": law.get('section', ''),
                    "text_snippet": law.get('text_snippet', '')[:300],
                    "why_relevant": law.get('why_relevant', '')
                }
                for law in controlling_law
            ],
            "facts_to_elements": [
                {
                    "issue_id": elem.get('issue_id', ''),
                    "element": elem.get('element', ''),
                    "support": elem.get('support', ''),
                    "evidence": elem.get('evidence', []),
                    "status": elem.get('status', '')
                }
                for elem in facts_to_elements
            ],
            "holdings": [
                {
                    "issue_id": holding.get('issue_id', ''),
                    "decision": holding.get('decision', ''),
                    "rationale": holding.get('rationale', '')
                }
                for holding in holdings
            ],
            "remedies": remedies or [],
            "missing_material": missing_material,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "issues_count": len(issues),
                "controlling_law_count": len(controlling_law),
                "analysis_version": "2.0-statute-aligned"
            }
        }

    def render_both(
        self,
        issues: List[Dict[str, Any]],
        controlling_law: List[Dict[str, Any]],
        facts_to_elements: List[Dict[str, Any]],
        holdings: List[Dict[str, Any]],
        missing_material: List[str],
        remedies: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate both formats

        Returns:
            Dictionary with 'human_readable' and 'json' keys
        """
        return {
            'human_readable': self.render_human_readable(
                issues, controlling_law, facts_to_elements,
                holdings, missing_material
            ),
            'json': self.render_json(
                issues, controlling_law, facts_to_elements,
                holdings, missing_material, remedies
            )
        }

    def save_outputs(
        self,
        output: Dict[str, Any],
        case_id: str,
        output_dir: str = "legal_analyses"
    ):
        """
        Save both outputs to files

        Args:
            output: Output from render_both()
            case_id: Case identifier
            output_dir: Output directory
        """
        import os

        os.makedirs(output_dir, exist_ok=True)

        # Save markdown
        md_path = os.path.join(output_dir, f"{case_id}_analysis.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(output['human_readable'])

        # Save JSON
        json_path = os.path.join(output_dir, f"{case_id}_analysis.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(output['json'], f, indent=2, ensure_ascii=False)

        return {
            'markdown_path': md_path,
            'json_path': json_path
        }
