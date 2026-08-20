"""
Smart Retriever: Context-aware statute retrieval with section_type scoring

Implements:
- Dual query expansion (precision + recall)
- Section_type prior weighting
- Hard filters for topic relevance
- Sanity checks to exclude irrelevant sections
"""

from typing import Dict, List, Any, Tuple
from collections import defaultdict
import re


class SmartRetriever:
    """Context-aware retrieval with section_type scoring and hard filters"""

    def __init__(self, vector_store):
        """
        Initialize smart retriever

        Args:
            vector_store: EnhancedQdrantVectorStore instance
        """
        self.vector_store = vector_store

        # Section type priority weights
        self.section_type_priors = {
            'definition': 0.6,
            'schedule': 0.6,
            'power': 0.4,
            'function': 0.4,
            'budget_finance': 0.4,
            'procedure': 0.3,
            'administrative': 0.3,
            'offence': -0.6,  # Negative weight to demote
            'election': -0.6,  # Negative weight to demote
            'general': 0.0
        }

    def retrieve_for_issue(
        self,
        issue: Dict[str, Any],
        narrative_text: str,
        petition_text: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant statutes for a single issue

        Args:
            issue: Legal issue dictionary
            narrative_text: Full narrative text
            petition_text: Full petition text
            limit: Maximum results per query

        Returns:
            List of relevant statute sections with scores
        """
        # Build dual queries
        precision_query, recall_query = self._build_dual_queries(
            issue, narrative_text, petition_text
        )

        # Execute precision query
        precision_results = self._query_with_type_scoring(
            precision_query,
            issue,
            limit=limit
        )

        # Execute recall query
        recall_results = self._query_with_type_scoring(
            recall_query,
            issue,
            limit=limit
        )

        # Merge and deduplicate
        combined = self._merge_results(precision_results, recall_results)

        # Apply hard filters
        filtered = self._apply_hard_filters(combined, issue)

        # Sanity checks
        filtered = self._sanity_check(filtered, issue)

        return filtered[:limit]

    def _build_dual_queries(
        self,
        issue: Dict[str, Any],
        narrative: str,
        petition: str
    ) -> Tuple[str, str]:
        """
        Build precision and recall queries

        Args:
            issue: Legal issue
            narrative: Narrative text
            petition: Petition text

        Returns:
            (precision_query, recall_query) tuple
        """
        issue_desc = issue.get('description', '') or issue.get('question', '')
        issue_type = self._classify_issue_type(issue_desc)

        # Precision query: specific terms from issue
        precision_parts = [issue_desc]

        # Extract section references from issue
        section_refs = re.findall(r'§\s*(\d+[A-Z]?(?:\([a-z]\))?)', issue_desc)
        if section_refs:
            precision_parts.append(f"section {' '.join(section_refs)}")

        # Add specific legal terms
        legal_terms = self._extract_legal_terms(issue_desc)
        if legal_terms:
            precision_parts.append(' '.join(legal_terms[:3]))

        precision_query = ' '.join(precision_parts)

        # Recall query: broader topic keywords
        recall_parts = []

        if issue_type == 'budget':
            recall_parts.extend([
                'budget', 'development plan', 'allocation', 'funds',
                'municipal services', 'expenditure', 'functions'
            ])
        elif issue_type == 'authority':
            recall_parts.extend([
                'powers', 'functions', 'duties', 'authority',
                'competence', 'jurisdiction', 'tehsil council'
            ])
        elif issue_type == 'election':
            recall_parts.extend([
                'election', 'electoral', 'delimitation',
                'constituency', 'voting', 'poll'
            ])
        else:
            recall_parts.extend([
                'local government', 'council', 'district',
                'functions', 'powers'
            ])

        # Add schedule hints
        recall_parts.append('First Schedule Second Schedule Fourth Schedule')

        recall_query = ' '.join(recall_parts)

        return precision_query, recall_query

    def _query_with_type_scoring(
        self,
        query: str,
        issue: Dict[str, Any],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Execute query with section_type prior scoring

        Args:
            query: Search query
            issue: Legal issue context
            limit: Max results

        Returns:
            Scored results
        """
        # Get base search results
        base_results = self.vector_store.smart_search(query, limit=limit * 2)

        issue_type = self._classify_issue_type(
            issue.get('description', '') or issue.get('question', '')
        )

        # Rescore with section_type priors
        rescored = []
        for result in base_results:
            section_type = result.get('metadata', {}).get('section_type', 'general')
            base_score = result.get('score', 0.0)

            # Get prior weight
            prior = self.section_type_priors.get(section_type, 0.0)

            # Adjust for issue type
            if issue_type in ['budget', 'authority']:
                # Boost definitions and schedules, penalize offences/elections
                if section_type in ['definition', 'schedule']:
                    prior += 0.2
                elif section_type in ['offence', 'election']:
                    prior = -1.0  # Strong penalty

            # Compute final score: BM25/embedding + prior
            final_score = base_score + prior

            result['adjusted_score'] = final_score
            result['section_type_prior'] = prior

            rescored.append(result)

        # Sort by adjusted score
        rescored.sort(key=lambda x: x.get('adjusted_score', 0.0), reverse=True)

        return rescored[:limit]

    def _merge_results(
        self,
        precision: List[Dict[str, Any]],
        recall: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Merge precision and recall results, deduplicating

        Args:
            precision: Precision query results
            recall: Recall query results

        Returns:
            Merged and deduplicated results
        """
        seen_keys = set()
        merged = []

        # Precision results first
        for result in precision:
            key = self._get_result_key(result)
            if key not in seen_keys:
                seen_keys.add(key)
                merged.append(result)

        # Then recall results
        for result in recall:
            key = self._get_result_key(result)
            if key not in seen_keys:
                seen_keys.add(key)
                # Lower priority for recall-only results
                result['adjusted_score'] = result.get('adjusted_score', 0.0) * 0.8
                merged.append(result)

        # Re-sort
        merged.sort(key=lambda x: x.get('adjusted_score', 0.0), reverse=True)

        return merged

    def _get_result_key(self, result: Dict[str, Any]) -> str:
        """Generate unique key for result deduplication"""
        metadata = result.get('metadata', {})
        section_num = metadata.get('section_number')
        schedule_ref = metadata.get('schedule_ref')

        if section_num:
            return f"section_{section_num}"
        elif schedule_ref:
            return f"schedule_{schedule_ref}"
        else:
            return f"hash_{hash(result.get('text', ''))}"

    def _apply_hard_filters(
        self,
        results: List[Dict[str, Any]],
        issue: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Apply hard filters to exclude irrelevant sections

        Args:
            results: Search results
            issue: Legal issue

        Returns:
            Filtered results
        """
        issue_type = self._classify_issue_type(
            issue.get('description', '') or issue.get('question', '')
        )

        filtered = []

        for result in results:
            metadata = result.get('metadata', {})
            section_type = metadata.get('section_type', 'general')
            heading = metadata.get('title', '') or metadata.get('section', '')

            # Hard exclusion rules
            if issue_type in ['budget', 'authority', 'administrative']:
                # Exclude offences and elections
                if section_type in ['offence', 'election']:
                    continue
                # Exclude by heading
                if any(kw in heading.lower() for kw in ['offence', 'penalty', 'fine', 'election']):
                    continue

            elif issue_type == 'election':
                # Exclude offences and budget
                if section_type in ['offence', 'budget_finance']:
                    continue

            # Sanity check: heading must mention relevant terms
            text_sample = (heading + ' ' + result.get('text', '')[:200]).lower()
            relevant_terms = self._get_relevant_terms(issue_type)

            # Require at least one relevant term for non-definition/schedule sections
            if section_type not in ['definition', 'schedule']:
                if not any(term in text_sample for term in relevant_terms):
                    continue

            filtered.append(result)

        return filtered

    def _get_relevant_terms(self, issue_type: str) -> List[str]:
        """Get relevant terms for issue type"""
        term_map = {
            'budget': ['budget', 'plan', 'fund', 'development', 'municipal', 'service', 'allocation', 'scheme'],
            'authority': ['power', 'function', 'duty', 'authority', 'competence', 'council', 'jurisdiction'],
            'election': ['election', 'electoral', 'delimitation', 'voting', 'constituency'],
            'offence': ['offence', 'penalty', 'fine', 'punishment', 'violation'],
            'general': ['government', 'council', 'district', 'local', 'provision']
        }
        return term_map.get(issue_type, term_map['general'])

    def _sanity_check(
        self,
        results: List[Dict[str, Any]],
        issue: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Final sanity check to catch obvious mismatches

        Args:
            results: Filtered results
            issue: Legal issue

        Returns:
            Sanity-checked results
        """
        issue_desc = issue.get('description', '') or issue.get('question', '')
        issue_lower = issue_desc.lower()

        # If issue is about encroachments, only keep relevant sections
        if 'encroachment' in issue_lower:
            results = [r for r in results if 'encroachment' in r.get('text', '').lower()[:500]]

        # If issue is about elections, filter aggressively
        if any(kw in issue_lower for kw in ['election', 'electoral', 'voting']):
            results = [
                r for r in results
                if r.get('metadata', {}).get('section_type') in ['election', 'definition', 'schedule', 'procedure']
            ]

        return results

    def _classify_issue_type(self, issue_text: str) -> str:
        """Classify issue type"""
        text_lower = issue_text.lower()

        if any(kw in text_lower for kw in ['budget', 'fund', 'allocation', 'expenditure', 'development plan']):
            return 'budget'
        elif any(kw in text_lower for kw in ['power', 'authority', 'jurisdiction', 'competence', 'ultra vires']):
            return 'authority'
        elif any(kw in text_lower for kw in ['election', 'electoral', 'voting', 'delimitation']):
            return 'election'
        elif any(kw in text_lower for kw in ['offence', 'penalty', 'fine', 'punishment']):
            return 'offence'
        else:
            return 'general'

    def _extract_legal_terms(self, text: str) -> List[str]:
        """Extract key legal terms"""
        patterns = [
            r'\b(council|committee|government|district|union|local)\b',
            r'\b(power|function|duty|authority|jurisdiction)\b',
            r'\b(budget|fund|finance|allocation)\b',
            r'\b(election|electoral|delimitation)\b',
            r'\b(municipal|service|development|plan)\b'
        ]

        terms = []
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            terms.extend(matches)

        return list(set(terms))
