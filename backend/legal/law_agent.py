"""
Law Agent for RAGBot-v2: Legal Retrieval and Mapping

This agent queries the law corpus (Qdrant) for relevant statutory sections
based on case issues and maps them to legal arguments.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re

# Import existing vector store infrastructure
from .vector_store import EnhancedQdrantVectorStore


class LawAgent:
    """
    Law Agent: Retrieves and maps relevant law sections to case issues
    """

    def __init__(self, vector_store: EnhancedQdrantVectorStore):
        """
        Initialize Law Agent

        Args:
            vector_store: Initialized EnhancedQdrantVectorStore instance
        """
        self.vector_store = vector_store

        # Issue-to-law mapping heuristics
        self.issue_law_hints = {
            'jurisdictional': [
                'jurisdiction', 'powers', 'authority', 'competence',
                'territorial', 'local government', 'district', 'union council'
            ],
            'procedural': [
                'procedure', 'process', 'notice', 'hearing', 'time limit',
                'appeal', 'review', 'rule', 'regulation'
            ],
            'substantive': [
                'rights', 'duties', 'functions', 'obligations', 'powers',
                'responsibilities', 'authority', 'scope'
            ],
            'constitutional': [
                'fundamental', 'constitutional', 'writ', 'article',
                'charter', 'basic rights'
            ],
            'administrative': [
                'administrative', 'executive', 'discretion', 'natural justice',
                'fair', 'reasonable', 'arbitrary', 'mala fide'
            ],
            'financial': [
                'budget', 'fund', 'finance', 'tax', 'fee', 'grant',
                'allocation', 'accounts', 'audit', 'expenditure', 'revenue'
            ],
            'electoral': [
                'election', 'delimitation', 'constituency', 'ward',
                'nomination', 'voting', 'ballot', 'electoral', 'poll'
            ]
        }

    def retrieve_relevant_law(
        self,
        case_issues: List[Dict[str, Any]],
        max_sections_per_issue: int = 3
    ) -> Dict[str, Any]:
        """
        Main retrieval method: Query law corpus for relevant sections

        Args:
            case_issues: List of legal issues from CaseAgent
            max_sections_per_issue: Maximum law sections to retrieve per issue

        Returns:
            Dictionary mapping issues to relevant law sections
        """
        issue_law_mapping = []
        all_law_sections = []

        for issue in case_issues:
            # Build enhanced query from issue
            query = self._build_law_query(issue)

            # Retrieve relevant law sections
            law_sections = self._query_law_corpus(
                query,
                issue_category=issue.get('category', 'general'),
                limit=max_sections_per_issue
            )

            # Map issue to law sections
            mapping_entry = {
                'issue_id': issue['id'],
                'issue_description': issue['description'],
                'issue_category': issue.get('category', 'general'),
                'relevant_sections': law_sections,
                'retrieval_confidence': self._calculate_confidence(law_sections),
                'retrieved_at': datetime.now().isoformat()
            }

            issue_law_mapping.append(mapping_entry)
            all_law_sections.extend(law_sections)

        # Deduplicate law sections across all issues
        unique_sections = self._deduplicate_law_sections(all_law_sections)

        # Rank sections by aggregate relevance
        ranked_sections = self._rank_law_sections(unique_sections, case_issues)

        return {
            'issue_law_mapping': issue_law_mapping,
            'all_relevant_sections': ranked_sections,
            'metadata': {
                'total_issues': len(case_issues),
                'total_unique_sections': len(ranked_sections),
                'avg_sections_per_issue': len(all_law_sections) / len(case_issues) if case_issues else 0,
                'retrieved_at': datetime.now().isoformat()
            }
        }

    def _build_law_query(self, issue: Dict[str, Any]) -> str:
        """
        Build optimized query for law corpus based on issue

        Args:
            issue: Legal issue dictionary

        Returns:
            Optimized query string
        """
        description = issue.get('description', '')
        category = issue.get('category', 'general')
        issue_type = issue.get('type', 'unknown')

        # Extract key legal terms from description
        legal_terms = self._extract_legal_terms(description)

        # Add category-specific keywords
        category_keywords = self.issue_law_hints.get(category, [])

        # Build query components
        query_parts = [description]

        # Add focused keywords
        if legal_terms:
            query_parts.append(' '.join(legal_terms[:5]))

        # Add category hint
        if category != 'general' and category_keywords:
            query_parts.append(' '.join(category_keywords[:3]))

        # Combine query parts
        query = ' '.join(query_parts)

        return query

    def _extract_legal_terms(self, text: str) -> List[str]:
        """Extract key legal terms from text"""
        # Common legal terms in local government context
        legal_terms_patterns = [
            r'\b(council|committee|government|district|union|local)\b',
            r'\b(power|function|duty|authority|jurisdiction|responsibility)\b',
            r'\b(election|electoral|delimitation|constituency|ward)\b',
            r'\b(budget|fund|finance|tax|fee|grant|allocation)\b',
            r'\b(procedure|process|rule|regulation|notification)\b',
            r'\b(appeal|review|revision|dispute|conflict|resolution)\b',
            r'\b(audit|accounts|expenditure|revenue|treasury)\b',
        ]

        terms = []
        for pattern in legal_terms_patterns:
            matches = re.findall(pattern, text.lower())
            terms.extend(matches)

        # Deduplicate while preserving order
        seen = set()
        unique_terms = []
        for term in terms:
            if term not in seen:
                seen.add(term)
                unique_terms.append(term)

        return unique_terms

    def _query_law_corpus(
        self,
        query: str,
        issue_category: str = 'general',
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Query the law corpus (Qdrant vector store)

        Args:
            query: Search query
            issue_category: Category of the issue
            limit: Maximum results to return

        Returns:
            List of relevant law sections with metadata
        """
        try:
            # Use smart search for best retrieval strategy
            results = self.vector_store.smart_search(query, limit=limit)

            # Format results for law agent
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'text': result.get('text', ''),
                    'sliced_text': result.get('sliced_text', ''),  # Pinpoint snippet
                    'score': float(result.get('score', 0.0)),
                    'metadata': result.get('metadata', {}),
                    'section_number': result.get('metadata', {}).get('section_number'),
                    'section_title': result.get('metadata', {}).get('title') or result.get('metadata', {}).get('section'),
                    'schedule_ref': result.get('metadata', {}).get('schedule_ref'),
                    'citation': self._format_citation(result.get('metadata', {})),
                    'relevance_reason': result.get('search_strategy', {}).get('query_type', 'semantic_match')
                })

            return formatted_results

        except Exception as e:
            print(f"⚠️  Law retrieval error: {e}")
            # Fallback: return empty results
            return []

    def _format_citation(self, metadata: Dict[str, Any]) -> str:
        """Format citation from metadata"""
        if metadata.get('section_number'):
            citation = f"Section {metadata['section_number']}"
            title = metadata.get('title') or metadata.get('section')
            if title:
                citation += f": {title}"
            return citation

        elif metadata.get('schedule_ref'):
            return metadata['schedule_ref']

        elif metadata.get('article_number'):
            return f"Article {metadata['article_number']}"

        elif metadata.get('chapter_number'):
            return f"Chapter {metadata['chapter_number']}"

        else:
            return "General Provision"

    def _calculate_confidence(self, law_sections: List[Dict[str, Any]]) -> str:
        """Calculate retrieval confidence based on scores"""
        if not law_sections:
            return 'none'

        avg_score = sum(s['score'] for s in law_sections) / len(law_sections)

        if avg_score >= 0.7:
            return 'high'
        elif avg_score >= 0.4:
            return 'medium'
        else:
            return 'low'

    def _deduplicate_law_sections(
        self,
        sections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Deduplicate law sections by section number or text hash

        Args:
            sections: List of law sections

        Returns:
            Deduplicated list
        """
        seen_keys = set()
        unique_sections = []

        for section in sections:
            # Create unique key from section number or text hash
            section_num = section.get('section_number')
            schedule_ref = section.get('schedule_ref')

            if section_num:
                key = f"section_{section_num}"
            elif schedule_ref:
                key = f"schedule_{schedule_ref}"
            else:
                key = f"hash_{hash(section.get('text', ''))}"

            if key not in seen_keys:
                seen_keys.add(key)
                unique_sections.append(section)

        return unique_sections

    def _rank_law_sections(
        self,
        sections: List[Dict[str, Any]],
        issues: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Rank law sections by aggregate relevance across all issues

        Args:
            sections: List of law sections
            issues: List of case issues

        Returns:
            Ranked list of law sections
        """
        # Count how many issues each section is relevant to
        section_issue_counts = {}

        for section in sections:
            section_key = section.get('section_number') or section.get('schedule_ref') or hash(section.get('text', ''))

            if section_key not in section_issue_counts:
                section_issue_counts[section_key] = {
                    'section': section,
                    'count': 0,
                    'total_score': 0.0
                }

            section_issue_counts[section_key]['count'] += 1
            section_issue_counts[section_key]['total_score'] += section['score']

        # Sort by: 1) number of issues addressed, 2) total score
        ranked = sorted(
            section_issue_counts.values(),
            key=lambda x: (x['count'], x['total_score']),
            reverse=True
        )

        # Extract sections and add rank metadata
        ranked_sections = []
        for idx, entry in enumerate(ranked):
            section = entry['section']
            section['rank'] = idx + 1
            section['addresses_issue_count'] = entry['count']
            ranked_sections.append(section)

        return ranked_sections

    def explain_relevance(
        self,
        issue: Dict[str, Any],
        law_section: Dict[str, Any]
    ) -> str:
        """
        Generate explanation for why a law section is relevant to an issue

        Args:
            issue: Legal issue
            law_section: Retrieved law section

        Returns:
            Human-readable explanation
        """
        section_text = law_section.get('sliced_text') or law_section.get('text', '')
        issue_desc = issue.get('description', '')

        # Extract overlapping terms
        issue_terms = set(self._extract_legal_terms(issue_desc))
        section_terms = set(self._extract_legal_terms(section_text))
        common_terms = issue_terms & section_terms

        citation = law_section.get('citation', 'this provision')

        if common_terms:
            terms_str = ', '.join(list(common_terms)[:5])
            return f"{citation} is relevant because it addresses: {terms_str}"
        else:
            return f"{citation} may be relevant to this issue based on semantic similarity"

    def map_issues_to_sections(
        self,
        case_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Convenience method: Map all case issues to law sections

        Args:
            case_analysis: Output from CaseAgent

        Returns:
            Issue-to-law mapping
        """
        issues = case_analysis.get('legal_issues', [])
        return self.retrieve_relevant_law(issues)

    def get_fallback_sections(
        self,
        issue_category: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get fallback law sections based on issue category (BM25-only)

        Args:
            issue_category: Category of issue
            limit: Maximum results

        Returns:
            List of law sections
        """
        # Use category keywords for simple keyword search
        keywords = self.issue_law_hints.get(issue_category, ['local government'])
        query = ' '.join(keywords[:5])

        try:
            # Use hybrid search with high keyword weight as fallback
            results = self.vector_store.hybrid_search_method(
                query,
                limit=limit,
                search_weights={'semantic': 0.2, 'keyword': 0.5, 'tfidf': 0.2, 'entity': 0.1}
            )

            formatted_results = []
            for result in results:
                formatted_results.append({
                    'text': result.get('text', ''),
                    'score': float(result.get('score', 0.0)),
                    'metadata': result.get('metadata', {}),
                    'section_number': result.get('metadata', {}).get('section_number'),
                    'citation': self._format_citation(result.get('metadata', {})),
                    'relevance_reason': 'category_fallback'
                })

            return formatted_results

        except Exception as e:
            print(f"⚠️  Fallback retrieval error: {e}")
            return []


def retrieve_law_for_issues(
    issues: List[Dict[str, Any]],
    vector_store: EnhancedQdrantVectorStore
) -> Dict[str, Any]:
    """
    Convenience function for quick law retrieval

    Args:
        issues: List of legal issues
        vector_store: Initialized vector store

    Returns:
        Issue-to-law mapping
    """
    agent = LawAgent(vector_store)
    return agent.retrieve_relevant_law(issues)
