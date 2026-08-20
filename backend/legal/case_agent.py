"""
Case Agent for RAGBot-v2: Legal Issue Extraction and Case Analysis

This agent analyzes user narratives and opponent petitions to extract
structured legal issues and case summaries.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

# Import processing module
from .processing import DocumentProcessor


class CaseAgent:
    """
    Case Agent: Extracts and structures legal issues from narrative and petition
    """

    def __init__(self, gemini_client=None):
        """
        Initialize Case Agent

        Args:
            gemini_client: Optional Gemini client for advanced analysis
        """
        self.processor = DocumentProcessor()
        self.gemini_client = gemini_client

        # Issue classification keywords
        self.issue_categories = {
            'jurisdictional': [
                'jurisdiction', 'venue', 'territorial', 'competent authority',
                'power to adjudicate', 'forum'
            ],
            'procedural': [
                'procedure', 'process', 'notice', 'hearing', 'time limit',
                'statute of limitations', 'laches', 'waiver', 'estoppel'
            ],
            'substantive': [
                'rights', 'duties', 'obligations', 'breach', 'violation',
                'contravention', 'ultra vires', 'legitimate', 'lawful'
            ],
            'constitutional': [
                'fundamental right', 'constitutional', 'article', 'writ',
                'mandamus', 'certiorari', 'prohibition', 'quo warranto'
            ],
            'administrative': [
                'administrative action', 'discretion', 'natural justice',
                'fair hearing', 'reasonableness', 'mala fide', 'arbitrary'
            ],
            'financial': [
                'budget', 'fund', 'tax', 'fee', 'grant', 'allocation',
                'financial powers', 'audit', 'accounts'
            ],
            'electoral': [
                'election', 'delimitation', 'constituency', 'nomination',
                'disqualification', 'electoral process', 'voting'
            ]
        }

    def analyze_case(
        self,
        narrative: str,
        petition: str,
        extracted_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main analysis method: Extract structured case information

        Args:
            narrative: User's narrative text
            petition: Opponent's petition text
            extracted_data: Pre-processed data from DocumentProcessor (optional)

        Returns:
            Structured case analysis with legal issues
        """
        # Process documents if not already done
        if extracted_data is None:
            extracted_data = self.processor.process_case(narrative, petition)

        # Extract legal issues
        issues = self.extract_issues(narrative, petition, extracted_data)

        # Identify strengths and weaknesses
        strengths = self.identify_strengths(narrative, extracted_data)
        weaknesses = self.identify_weaknesses(narrative, petition, extracted_data)

        # Create case summary
        case_summary = self.create_case_summary(
            narrative, petition, extracted_data, issues
        )

        # Generate recommendations
        recommendations = self.generate_recommendations(
            issues, strengths, weaknesses, extracted_data
        )

        return {
            'case_summary': case_summary,
            'legal_issues': issues,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'recommendations': recommendations,
            'metadata': {
                'analyzed_at': datetime.now().isoformat(),
                'narrative_length': len(narrative),
                'petition_length': len(petition),
                'issue_count': len(issues),
                'inconsistency_count': len(extracted_data.get('inconsistencies', []))
            }
        }

    def extract_issues(
        self,
        narrative: str,
        petition: str,
        extracted_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract legal issues from narrative and petition

        Args:
            narrative: User's narrative
            petition: Opponent's petition
            extracted_data: Processed data with claims and entities

        Returns:
            List of structured legal issues
        """
        issues = []

        # Extract from petition claims (these are typically the issues raised)
        petition_claims = extracted_data['petition']['claims']

        for claim in petition_claims:
            issue = self._claim_to_issue(claim, source='petition')
            if issue:
                issues.append(issue)

        # Extract from petition demands (often frame the legal questions)
        petition_demands = extracted_data['petition']['demands']

        for demand in petition_demands:
            issue = self._demand_to_issue(demand, source='petition')
            if issue:
                issues.append(issue)

        # Extract issues from narrative counter-claims
        narrative_claims = extracted_data['narrative']['claims']

        for claim in narrative_claims:
            if claim['type'] in ['violation', 'allegation']:
                issue = self._claim_to_issue(claim, source='narrative')
                if issue:
                    issues.append(issue)

        # Identify gaps (issues raised in petition not addressed in narrative)
        petition_issue_texts = {self._normalize_text(i['description']) for i in issues if i['source'] == 'petition'}
        narrative_issue_texts = {self._normalize_text(i['description']) for i in issues if i['source'] == 'narrative'}

        unaddressed = petition_issue_texts - narrative_issue_texts
        if unaddressed:
            for unaddressed_issue in unaddressed:
                issues.append({
                    'id': f"issue_{len(issues) + 1}",
                    'description': f"Unaddressed allegation: {unaddressed_issue[:100]}...",
                    'category': 'unaddressed',
                    'source': 'gap_analysis',
                    'severity': 'high',
                    'requires_response': True
                })

        # Categorize all issues
        for issue in issues:
            if issue.get('category') != 'unaddressed':
                issue['category'] = self._categorize_issue(issue['description'])

        # Deduplicate and sort by severity
        issues = self._deduplicate_issues(issues)
        issues.sort(key=lambda x: {'high': 0, 'medium': 1, 'low': 2}.get(x.get('severity', 'low'), 2))

        # FALLBACK: If no issues extracted, create generic issues from narrative/petition
        if not issues:
            print("⚠️  Warning: No issues extracted. Creating fallback generic issues...")
            issues = self._create_fallback_issues(narrative, petition)

        return issues

    def _claim_to_issue(self, claim: Dict[str, Any], source: str) -> Optional[Dict[str, Any]]:
        """Convert a claim to a legal issue"""
        claim_text = claim.get('text', '').strip()

        if not claim_text or len(claim_text) < 20:
            return None

        return {
            'id': f"issue_{claim.get('type', 'unknown')}_{hash(claim_text) % 1000}",
            'description': claim_text,
            'type': claim.get('type', 'unknown'),
            'source': source,
            'severity': 'medium',
            'requires_response': source == 'petition'
        }

    def _demand_to_issue(self, demand: Dict[str, Any], source: str) -> Optional[Dict[str, Any]]:
        """Convert a demand to a legal issue"""
        demand_text = demand.get('text', '').strip()
        category = demand.get('category', 'other')

        if not demand_text or len(demand_text) < 20:
            return None

        return {
            'id': f"issue_demand_{category}_{hash(demand_text) % 1000}",
            'description': f"Relief sought: {demand_text}",
            'type': 'relief',
            'category': category,
            'source': source,
            'severity': 'high' if category in ['monetary', 'injunctive'] else 'medium',
            'requires_response': True
        }

    def _categorize_issue(self, issue_text: str) -> str:
        """Categorize issue based on keywords"""
        text_lower = issue_text.lower()

        best_category = 'general'
        max_matches = 0

        for category, keywords in self.issue_categories.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > max_matches:
                max_matches = matches
                best_category = category

        return best_category

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        return re.sub(r'\s+', ' ', text.lower().strip())

    def _deduplicate_issues(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate issues based on description similarity"""
        unique_issues = []
        seen_descriptions = set()

        for issue in issues:
            normalized = self._normalize_text(issue['description'])[:100]
            if normalized not in seen_descriptions:
                seen_descriptions.add(normalized)
                unique_issues.append(issue)

        return unique_issues

    def _create_fallback_issues(self, narrative: str, petition: str) -> List[Dict[str, Any]]:
        """
        Create generic fallback issues when extraction fails

        Args:
            narrative: User's narrative
            petition: Opponent's petition

        Returns:
            List of generic issues
        """
        fallback_issues = []

        # Generic issue 1: Main dispute
        if narrative and len(narrative) > 50:
            fallback_issues.append({
                'id': 'issue_fallback_1',
                'description': 'Dispute regarding the facts and circumstances described in the narrative',
                'category': 'substantive',
                'source': 'fallback',
                'severity': 'high',
                'requires_response': True
            })

        # Generic issue 2: Petition claims
        if petition and len(petition) > 50:
            fallback_issues.append({
                'id': 'issue_fallback_2',
                'description': 'Legal challenges raised in the opponent\'s petition',
                'category': 'procedural',
                'source': 'fallback',
                'severity': 'high',
                'requires_response': True
            })

        # Generic issue 3: Jurisdictional
        fallback_issues.append({
            'id': 'issue_fallback_3',
            'description': 'Jurisdiction and competence of the court to adjudicate this matter',
            'category': 'jurisdictional',
            'source': 'fallback',
            'severity': 'medium',
            'requires_response': False
        })

        # Generic issue 4: Relief sought
        fallback_issues.append({
            'id': 'issue_fallback_4',
            'description': 'Appropriateness and legal basis for the relief sought',
            'category': 'substantive',
            'source': 'fallback',
            'severity': 'medium',
            'requires_response': True
        })

        print(f"  Created {len(fallback_issues)} fallback generic issues")
        return fallback_issues

    def identify_strengths(
        self,
        narrative: str,
        extracted_data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Identify strengths in the user's position

        Args:
            narrative: User's narrative
            extracted_data: Processed data

        Returns:
            List of identified strengths
        """
        strengths = []

        narrative_data = extracted_data['narrative']

        # Well-documented chronology
        if len(narrative_data['chronology']) >= 3:
            strengths.append({
                'category': 'documentation',
                'description': f"Detailed chronology with {len(narrative_data['chronology'])} dated events",
                'impact': 'high'
            })

        # Strong statutory references
        statute_refs = [e for e in narrative_data['entities'].get('STATUTE_REF', [])]
        if len(statute_refs) >= 2:
            strengths.append({
                'category': 'legal_grounding',
                'description': f"Multiple statutory references cited ({len(statute_refs)} references)",
                'impact': 'high'
            })

        # Clear demands
        if len(narrative_data['demands']) >= 1:
            strengths.append({
                'category': 'clarity',
                'description': f"Clear relief sought with {len(narrative_data['demands'])} specific demand(s)",
                'impact': 'medium'
            })

        # Evidence of jurisdiction
        if any('jurisdiction' in str(e).lower() for e in narrative_data['entities'].values()):
            strengths.append({
                'category': 'jurisdiction',
                'description': "Jurisdictional authority explicitly addressed",
                'impact': 'high'
            })

        return strengths

    def identify_weaknesses(
        self,
        narrative: str,
        petition: str,
        extracted_data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Identify weaknesses or gaps in the user's position

        Args:
            narrative: User's narrative
            petition: Opponent's petition
            extracted_data: Processed data

        Returns:
            List of identified weaknesses
        """
        weaknesses = []

        narrative_data = extracted_data['narrative']
        petition_data = extracted_data['petition']
        inconsistencies = extracted_data['inconsistencies']

        # Critical inconsistencies
        critical_inconsistencies = extracted_data['analysis']['critical_inconsistencies']
        if critical_inconsistencies:
            for inc in critical_inconsistencies:
                weaknesses.append({
                    'category': 'inconsistency',
                    'description': inc['description'],
                    'severity': inc.get('severity', 'high'),
                    'impact': 'high'
                })

        # Missing counter-claims
        petition_claim_count = len(petition_data['claims'])
        narrative_claim_count = len(narrative_data['claims'])

        if petition_claim_count > narrative_claim_count * 1.5:
            weaknesses.append({
                'category': 'incomplete_response',
                'description': f"Narrative addresses {narrative_claim_count} points vs {petition_claim_count} allegations in petition",
                'severity': 'high',
                'impact': 'high'
            })

        # Lack of statutory backing
        narrative_statute_refs = narrative_data['entities'].get('STATUTE_REF', [])
        if len(narrative_statute_refs) < 2:
            weaknesses.append({
                'category': 'legal_grounding',
                'description': "Limited statutory references to support position",
                'severity': 'medium',
                'impact': 'medium'
            })

        # Missing chronology
        if len(narrative_data['chronology']) < 2:
            weaknesses.append({
                'category': 'documentation',
                'description': "Weak chronological documentation of events",
                'severity': 'medium',
                'impact': 'medium'
            })

        # Date inconsistencies
        if any(inc['type'] == 'date_mismatch' for inc in inconsistencies):
            weaknesses.append({
                'category': 'factual_inconsistency',
                'description': "Date mismatches between narrative and petition",
                'severity': 'high',
                'impact': 'high'
            })

        return weaknesses

    def create_case_summary(
        self,
        narrative: str,
        petition: str,
        extracted_data: Dict[str, Any],
        issues: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create structured case summary

        Args:
            narrative: User's narrative
            petition: Opponent's petition
            extracted_data: Processed data
            issues: Extracted legal issues

        Returns:
            Structured case summary
        """
        narrative_data = extracted_data['narrative']
        petition_data = extracted_data['petition']

        # Extract key parties
        parties = {
            'user_party': narrative_data['parties'].get('petitioners', ['User'])[0] if narrative_data['parties'].get('petitioners') else 'User',
            'opponent_party': petition_data['parties'].get('petitioners', ['Opponent'])[0] if petition_data['parties'].get('petitioners') else 'Opponent',
            'authorities_involved': list(set(
                narrative_data['parties'].get('authorities', []) +
                petition_data['parties'].get('authorities', [])
            ))
        }

        # Summarize issues by category
        issue_breakdown = {}
        for issue in issues:
            category = issue.get('category', 'general')
            if category not in issue_breakdown:
                issue_breakdown[category] = []
            issue_breakdown[category].append(issue['description'][:100])

        # Key dates
        all_dates = list(set(
            [e['date'] for e in narrative_data['chronology']] +
            [e['date'] for e in petition_data['chronology']]
        ))

        return {
            'parties': parties,
            'issue_count': len(issues),
            'issue_breakdown': issue_breakdown,
            'key_dates': all_dates[:10],  # Top 10 dates
            'primary_relief_sought': petition_data['demands'][0]['text'] if petition_data['demands'] else 'Not specified',
            'dispute_type': self._infer_dispute_type(issues),
            'complexity': self._assess_complexity(issues, extracted_data),
            'summary_generated_at': datetime.now().isoformat()
        }

    def _infer_dispute_type(self, issues: List[Dict[str, Any]]) -> str:
        """Infer the type of legal dispute"""
        categories = [issue.get('category', 'general') for issue in issues]

        category_counts = {}
        for cat in categories:
            category_counts[cat] = category_counts.get(cat, 0) + 1

        if not category_counts:
            return 'general'

        dominant_category = max(category_counts.items(), key=lambda x: x[1])[0]

        # Map to dispute types
        dispute_map = {
            'financial': 'Financial/Budgetary Dispute',
            'electoral': 'Electoral Dispute',
            'administrative': 'Administrative Law Dispute',
            'jurisdictional': 'Jurisdictional Challenge',
            'constitutional': 'Constitutional Matter',
            'procedural': 'Procedural Challenge',
            'substantive': 'Substantive Rights Dispute'
        }

        return dispute_map.get(dominant_category, 'General Legal Dispute')

    def _assess_complexity(
        self,
        issues: List[Dict[str, Any]],
        extracted_data: Dict[str, Any]
    ) -> str:
        """Assess case complexity"""
        score = 0

        # Number of issues
        score += len(issues) * 2

        # Number of inconsistencies
        score += len(extracted_data['inconsistencies']) * 3

        # Statutory references
        score += len(extracted_data['narrative']['entities'].get('STATUTE_REF', [])) * 1
        score += len(extracted_data['petition']['entities'].get('STATUTE_REF', [])) * 1

        # Multiple parties
        if len(extracted_data['narrative']['parties'].get('authorities', [])) > 2:
            score += 5

        if score < 10:
            return 'low'
        elif score < 25:
            return 'medium'
        else:
            return 'high'

    def generate_recommendations(
        self,
        issues: List[Dict[str, Any]],
        strengths: List[Dict[str, str]],
        weaknesses: List[Dict[str, str]],
        extracted_data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Generate strategic recommendations

        Args:
            issues: Legal issues
            strengths: Identified strengths
            weaknesses: Identified weaknesses
            extracted_data: Processed data

        Returns:
            List of recommendations
        """
        recommendations = []

        # Address critical weaknesses
        high_severity_weaknesses = [w for w in weaknesses if w.get('severity') == 'high']

        for weakness in high_severity_weaknesses:
            if weakness['category'] == 'inconsistency':
                recommendations.append({
                    'priority': 'high',
                    'action': 'Reconcile factual inconsistencies',
                    'details': weakness['description'],
                    'rationale': 'Factual inconsistencies can undermine credibility'
                })

            elif weakness['category'] == 'incomplete_response':
                recommendations.append({
                    'priority': 'high',
                    'action': 'Address all allegations from petition',
                    'details': weakness['description'],
                    'rationale': 'Unaddressed allegations may be deemed admitted'
                })

        # Strengthen legal grounding
        if any(w['category'] == 'legal_grounding' for w in weaknesses):
            recommendations.append({
                'priority': 'high',
                'action': 'Strengthen statutory backing',
                'details': 'Cite specific sections of KPK Local Government Act 2013',
                'rationale': 'Statutory grounding is essential for legal arguments'
            })

        # Leverage strengths
        if any(s['category'] == 'documentation' for s in strengths):
            recommendations.append({
                'priority': 'medium',
                'action': 'Emphasize documented chronology in arguments',
                'details': 'Use dated evidence to establish timeline',
                'rationale': 'Strong documentation supports factual claims'
            })

        # Address unaddressed issues
        unaddressed_issues = [i for i in issues if i.get('category') == 'unaddressed']
        if unaddressed_issues:
            for issue in unaddressed_issues[:3]:  # Top 3
                recommendations.append({
                    'priority': 'high',
                    'action': 'Respond to unaddressed allegation',
                    'details': issue['description'],
                    'rationale': 'Silence may be construed as admission'
                })

        # Procedural recommendations
        recommendations.append({
            'priority': 'medium',
            'action': 'Verify jurisdictional grounds',
            'details': 'Ensure proper forum and authority for dispute resolution',
            'rationale': 'Jurisdictional defects can be fatal to proceedings'
        })

        return recommendations[:8]  # Return top 8 recommendations


def analyze_case(narrative: str, petition: str, gemini_client=None) -> Dict[str, Any]:
    """
    Convenience function for quick case analysis

    Args:
        narrative: User's narrative
        petition: Opponent's petition
        gemini_client: Optional Gemini client

    Returns:
        Structured case analysis
    """
    agent = CaseAgent(gemini_client=gemini_client)
    return agent.analyze_case(narrative, petition)
