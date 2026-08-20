"""
Statute Parser: Enhanced structure extraction with section_type classification

Classifies statutory sections into types (definitions, powers, functions, schedules,
offences, elections, procedures) to enable smart filtering during retrieval.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict


class StatuteParser:
    """Parse statutory documents with enhanced section_type classification"""

    def __init__(self):
        # Section type classification keywords
        self.section_type_patterns = {
            'definition': [
                r'\bdefinition', r'\binterpretation\b', r'\bmeans\b', r'\bincludes\b',
                r'\bshall mean\b', r'\bdefined as\b', r'\bfor purposes of\b'
            ],
            'power': [
                r'\bpowers?\b', r'\bauthority\b', r'\bmay\b.*\bexercise\b',
                r'\bentitled to\b', r'\bempowered\b', r'\bauthori[zs]ed\b'
            ],
            'function': [
                r'\bfunctions?\b', r'\bduties\b', r'\bresponsibilit(?:y|ies)\b',
                r'\bshall\b.*\b(?:perform|discharge|carry out)\b',
                r'\bobligation\b', r'\bsubject to\b'
            ],
            'schedule': [
                r'schedule', r'\blist of\b', r'\benumerat', r'\bappendix\b'
            ],
            'offence': [
                r'\boffence', r'\bpenalty\b', r'\bfine\b', r'\bpunishment\b',
                r'\bconviction\b', r'\bimprisonment\b', r'\bviolation\b.*\bpunishable\b'
            ],
            'election': [
                r'\belection', r'\belectoral\b', r'\bvoting\b', r'\bballot\b',
                r'\bdelimitation\b', r'\bconstituency\b', r'\bnomination\b',
                r'\bward\b', r'\bpoll\b', r'\bcandidate\b'
            ],
            'procedure': [
                r'\bprocedure', r'\bprocess\b', r'\bnotice\b', r'\bhearing\b',
                r'\btime[\s-]?limit\b', r'\bappeal\b', r'\breview\b',
                r'\bapplication\b', r'\bmanner of\b'
            ],
            'budget_finance': [
                r'\bbudget', r'\bfund', r'\bfinance', r'\bexpenditure\b',
                r'\brevenue\b', r'\btax', r'\bgrant\b', r'\baccounts?\b',
                r'\baudit\b', r'\ballocation\b', r'\bappropriation\b'
            ],
            'administrative': [
                r'\badministrative', r'\bexecutive\b', r'\bgovernment\b',
                r'\bofficial\b', r'\badministrator\b', r'\bappoint', r'\bterm of office\b'
            ]
        }

        # Schedule ordinal mapping
        self.schedule_word_to_num = {
            'FIRST': '1', 'SECOND': '2', 'THIRD': '3', 'FOURTH': '4',
            'FIFTH': '5', 'SIXTH': '6', 'SEVENTH': '7', 'EIGHTH': '8',
            'NINTH': '9', 'TENTH': '10', 'ELEVENTH': '11', 'TWELFTH': '12'
        }

    def classify_section_type(self, section_text: str, section_title: str = "") -> str:
        """
        Classify section into type based on content and title

        Args:
            section_text: Full section text
            section_title: Section title/heading

        Returns:
            Section type (definition|power|function|schedule|offence|election|procedure|general)
        """
        combined_text = (section_title + " " + section_text[:500]).lower()

        # Score each type
        type_scores = defaultdict(int)

        for section_type, patterns in self.section_type_patterns.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, combined_text, re.IGNORECASE))
                type_scores[section_type] += matches

        # Special handling for schedules
        if re.search(r'schedule', combined_text, re.IGNORECASE):
            return 'schedule'

        # Return type with highest score, or 'general' if no matches
        if not type_scores:
            return 'general'

        best_type = max(type_scores.items(), key=lambda x: x[1])[0]

        # Minimum threshold: require at least 2 matches
        if type_scores[best_type] < 2:
            return 'general'

        return best_type

    def classify_schedule_type(self, schedule_text: str, schedule_title: str = "") -> str:
        """
        Classify schedule subtype

        Args:
            schedule_text: Schedule content
            schedule_title: Schedule title

        Returns:
            Schedule subtype
        """
        text_lower = (schedule_text + ' ' + schedule_title).lower()

        if any(word in text_lower for word in ['offence', 'offense', 'penalty', 'fine', 'violation']):
            return 'offences_penalties'
        elif any(word in text_lower for word in ['form', 'format', 'template', 'ticket']):
            return 'forms'
        elif any(word in text_lower for word in ['rule', 'regulation', 'bye-law', 'bylaw']):
            return 'rules'
        elif any(word in text_lower for word in ['office', 'devolve', 'department', 'function']):
            return 'administrative'
        elif any(word in text_lower for word in ['composition', 'member', 'council', 'elect']):
            return 'composition'
        elif any(word in text_lower for word in ['municipal service', 'water', 'sanitation', 'infrastructure']):
            return 'municipal_services'
        elif any(word in text_lower for word in ['delimitation', 'boundary', 'district']):
            return 'delimitation'
        else:
            return 'general'

    def extract_definitions(self, text: str) -> Dict[str, str]:
        """
        Extract definitions from statutory text

        Args:
            text: Statute text

        Returns:
            Dictionary mapping terms to definitions
        """
        definitions = {}

        # Pattern: "term" means ...
        pattern1 = re.compile(
            r'["""]([^"""]+)["""][\s]+means[\s]+([^;.]+[;.])',
            re.IGNORECASE
        )

        # Pattern: (r) "term" means ...
        pattern2 = re.compile(
            r'\([a-z]+\)[\s]*["""]([^"""]+)["""][\s]+means[\s]+([^;.]+[;.])',
            re.IGNORECASE
        )

        for pattern in [pattern1, pattern2]:
            for match in pattern.finditer(text):
                term = match.group(1).strip()
                definition = match.group(2).strip()
                definitions[term] = definition

        return definitions

    def is_relevant_to_topic(
        self,
        section_text: str,
        section_type: str,
        topic_keywords: List[str]
    ) -> bool:
        """
        Check if section is relevant to given topic

        Args:
            section_text: Section content
            section_type: Section type classification
            topic_keywords: Keywords defining the topic

        Returns:
            True if relevant, False otherwise
        """
        # Definitions and schedules are always potentially relevant
        if section_type in ['definition', 'schedule']:
            return True

        # For other types, check keyword overlap
        text_lower = section_text.lower()

        # Count keyword matches
        matches = sum(1 for kw in topic_keywords if kw.lower() in text_lower)

        # Require at least 1 keyword match for relevance
        return matches > 0

    def hard_filter_sections(
        self,
        sections: List[Dict[str, Any]],
        issue_type: str
    ) -> List[Dict[str, Any]]:
        """
        Apply hard filters to exclude irrelevant sections

        Args:
            sections: List of statute sections
            issue_type: Type of legal issue (budget|authority|election|offence)

        Returns:
            Filtered list
        """
        filtered = []

        for section in sections:
            section_type = section.get('section_type', 'general')

            # Hard exclusion rules
            if issue_type in ['budget', 'authority', 'administrative']:
                # Exclude offences and elections for budget/authority issues
                if section_type in ['offence', 'election']:
                    continue

            elif issue_type == 'election':
                # For election issues, exclude offences and budget
                if section_type in ['offence', 'budget_finance']:
                    continue

            elif issue_type == 'offence':
                # For offence issues, exclude elections and budget
                if section_type in ['election', 'budget_finance']:
                    continue

            filtered.append(section)

        return filtered

    def enrich_metadata_with_types(
        self,
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enrich chunk metadata with section_type classification

        Args:
            chunks: List of document chunks with metadata

        Returns:
            Enriched chunks
        """
        for chunk in chunks:
            text = chunk.get('text', '')
            metadata = chunk.get('metadata', {})

            # Get title from metadata
            title = (
                metadata.get('title', '') or
                metadata.get('section', '') or
                metadata.get('schedule_ref', '')
            )

            # Classify section type
            section_type = self.classify_section_type(text, title)

            # Add to metadata
            metadata['section_type'] = section_type

            # For schedules, add schedule subtype
            if metadata.get('schedule_ref') or section_type == 'schedule':
                schedule_subtype = self.classify_schedule_type(text, title)
                metadata['schedule_type'] = schedule_subtype

            # Extract definitions if it's a definition section
            if section_type == 'definition':
                definitions = self.extract_definitions(text)
                if definitions:
                    metadata['extracted_definitions'] = list(definitions.keys())

            chunk['metadata'] = metadata

        return chunks


def classify_issue_type(issue_description: str) -> str:
    """
    Classify the type of legal issue to guide retrieval filtering

    Args:
        issue_description: Description of the legal issue

    Returns:
        Issue type (budget|authority|election|offence|general)
    """
    desc_lower = issue_description.lower()

    if any(kw in desc_lower for kw in ['budget', 'fund', 'allocation', 'expenditure', 'finance']):
        return 'budget'
    elif any(kw in desc_lower for kw in ['power', 'authority', 'jurisdiction', 'competence']):
        return 'authority'
    elif any(kw in desc_lower for kw in ['election', 'electoral', 'voting', 'delimitation']):
        return 'election'
    elif any(kw in desc_lower for kw in ['offence', 'penalty', 'fine', 'punishment']):
        return 'offence'
    else:
        return 'general'
