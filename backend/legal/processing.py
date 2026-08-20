"""
Processing Layer for RAGBot-v2: NER + Claim Extraction

This module provides Named Entity Recognition (NER) and claim extraction
capabilities for processing user narratives and opponent petitions.
"""

import re
import os
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict
import json
from datetime import datetime

# Try to import spaCy, with graceful fallback
try:
    import spacy
    from spacy.language import Language
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("⚠️  spaCy not available. Install with: pip install spacy && python -m spacy download en_core_web_sm")


class NERExtractor:
    """Named Entity Recognition extractor for legal documents"""

    def __init__(self, model_name: str = "en_core_web_sm"):
        """
        Initialize NER extractor with spaCy model

        Args:
            model_name: spaCy model to use (default: en_core_web_sm)
        """
        self.model_name = model_name
        self.nlp = None

        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load(model_name)
                print(f"✅ Loaded spaCy model: {model_name}")
            except OSError:
                print(f"⚠️  spaCy model '{model_name}' not found. Downloading...")
                os.system(f"python -m spacy download {model_name}")
                try:
                    self.nlp = spacy.load(model_name)
                    print(f"✅ Loaded spaCy model: {model_name}")
                except:
                    print(f"❌ Failed to load spaCy model. Using fallback extraction.")
                    self.nlp = None

        # Legal-specific entity patterns
        self.legal_patterns = {
            'LEGAL_TERM': [
                r'\b(?:plaintiff|defendant|petitioner|respondent|appellant|appellee)\b',
                r'\b(?:arbitration|mediation|conciliation|adjudication)\b',
                r'\b(?:jurisdiction|venue|cause of action|relief|damages)\b',
                r'\b(?:breach|negligence|tort|contract|agreement|covenant)\b',
                r'\b(?:injunction|restraining order|writ|mandamus|certiorari)\b',
            ],
            'STATUTE_REF': [
                r'(?:Section|Sec\.|Article|Art\.)\s+\d+[A-Z]?(?:\(\d+\))?(?:\([a-z]\))?',
                r'(?:Chapter|Part)\s+(?:[IVXLCDM]+|\d+)',
                r'(?:Schedule|Sched\.)\s+(?:[IVXLCDM]+|\d+)',
                r'(?:Rule|Regulation)\s+\d+',
            ],
            'DATE_PATTERN': [
                r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
                r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}',
            ],
            'MONETARY': [
                r'Rs\.?\s*\d+(?:,\d{3})*(?:\.\d{2})?',
                r'PKR\s*\d+(?:,\d{3})*(?:\.\d{2})?',
                r'\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:rupees|Rupees)',
            ],
            'LOCATION': [
                r'\b(?:District|Tehsil|Union Council)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',
                r'\b(?:KP|KPK|Khyber Pakhtunkhwa|NWFP)\b',
            ]
        }

    def extract_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract named entities from text

        Args:
            text: Input text to analyze

        Returns:
            Dictionary of entity types and their occurrences
        """
        entities = defaultdict(list)

        if not text:
            return dict(entities)

        # Use spaCy if available
        if self.nlp is not None:
            doc = self.nlp(text)

            for ent in doc.ents:
                entities[ent.label_].append({
                    'text': ent.text,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'confidence': 'high'
                })

        # Add legal-specific patterns
        for entity_type, patterns in self.legal_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entities[entity_type].append({
                        'text': match.group(0),
                        'start': match.start(),
                        'end': match.end(),
                        'confidence': 'medium'
                    })

        # Deduplicate entities
        for entity_type in entities:
            seen = set()
            unique_entities = []
            for ent in entities[entity_type]:
                key = (ent['text'].lower(), ent['start'])
                if key not in seen:
                    seen.add(key)
                    unique_entities.append(ent)
            entities[entity_type] = unique_entities

        return dict(entities)

    def extract_parties(self, text: str) -> Dict[str, List[str]]:
        """
        Extract parties involved in the legal matter

        Args:
            text: Input text

        Returns:
            Dictionary with petitioner and respondent names
        """
        parties = {
            'petitioners': [],
            'respondents': [],
            'witnesses': [],
            'authorities': []
        }

        # Extract entities first
        entities = self.extract_entities(text)

        # Look for person and organization entities
        persons = entities.get('PERSON', [])
        orgs = entities.get('ORG', [])

        # Pattern matching for role identification
        text_lower = text.lower()

        for person in persons:
            person_text = person['text']
            # Check context around person mention
            start = max(0, person['start'] - 50)
            end = min(len(text), person['end'] + 50)
            context = text[start:end].lower()

            if any(role in context for role in ['petitioner', 'plaintiff', 'complainant']):
                parties['petitioners'].append(person_text)
            elif any(role in context for role in ['respondent', 'defendant', 'accused']):
                parties['respondents'].append(person_text)
            elif any(role in context for role in ['witness', 'testified']):
                parties['witnesses'].append(person_text)

        for org in orgs:
            org_text = org['text']
            start = max(0, org['start'] - 50)
            end = min(len(text), org['end'] + 50)
            context = text[start:end].lower()

            if any(auth in context for auth in ['government', 'department', 'authority', 'council']):
                parties['authorities'].append(org_text)

        # Remove duplicates
        for key in parties:
            parties[key] = list(set(parties[key]))

        return parties


class ClaimExtractor:
    """Extract legal claims and assertions from narrative and petition"""

    def __init__(self):
        """Initialize claim extractor"""
        # Claim indicator patterns
        self.claim_patterns = {
            'allegation': [
                r'(?:allegedly|accused of|charged with|blamed for)\s+(.{20,200}?)(?:\.|;|\n)',
                r'(?:it is alleged that|the allegation is that)\s+(.{20,200}?)(?:\.|;|\n)',
            ],
            'demand': [
                r'(?:demands?|seeks?|requests?|prays? for)\s+(.{20,200}?)(?:\.|;|\n)',
                r'(?:claiming|entitled to)\s+(.{20,200}?)(?:\.|;|\n)',
            ],
            'violation': [
                r'(?:violated|breached|contravened|infringed)\s+(.{20,200}?)(?:\.|;|\n)',
                r'(?:violation of|breach of|contravention of)\s+(.{20,200}?)(?:\.|;|\n)',
            ],
            'relief': [
                r'(?:relief|remedy|compensation|damages)\s+(?:sought|claimed|requested)\s+(.{20,200}?)(?:\.|;|\n)',
                r'(?:seeking|requesting)\s+(?:relief|remedy|compensation)\s+(.{20,200}?)(?:\.|;|\n)',
            ],
            'fact': [
                r'(?:on|dated?|at)\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+(.{20,200}?)(?:\.|;|\n)',
                r'(?:fact that|factually|in fact)\s+(.{20,200}?)(?:\.|;|\n)',
            ]
        }

        # Temporal indicators
        self.temporal_patterns = [
            r'(?:on|dated?|at|during|from|to|until|since|before|after)\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})',
        ]

    def extract_claims(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract legal claims from text

        Args:
            text: Input text (narrative or petition)

        Returns:
            List of extracted claims with metadata
        """
        claims = []

        if not text:
            return claims

        for claim_type, patterns in self.claim_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    claim_text = match.group(1) if match.lastindex else match.group(0)
                    claims.append({
                        'type': claim_type,
                        'text': claim_text.strip(),
                        'position': match.start(),
                        'confidence': 0.8,
                        'extracted_at': datetime.now().isoformat()
                    })

        return claims

    def extract_chronology(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract chronological events from text

        Args:
            text: Input text

        Returns:
            List of events with dates and descriptions
        """
        events = []

        for pattern in self.temporal_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Extract date
                date_text = match.group(1) if match.lastindex else match.group(0)

                # Extract surrounding context (event description)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 150)
                context = text[start:end].strip()

                events.append({
                    'date': date_text,
                    'description': context,
                    'position': match.start()
                })

        # Sort by position in text (chronological order as presented)
        events.sort(key=lambda x: x['position'])

        return events

    def identify_inconsistencies(
        self,
        narrative: str,
        petition: str
    ) -> List[Dict[str, Any]]:
        """
        Identify potential inconsistencies between narrative and petition

        Args:
            narrative: User's narrative text
            petition: Opponent's petition text

        Returns:
            List of potential inconsistencies
        """
        inconsistencies = []

        # Extract claims from both documents
        narrative_claims = self.extract_claims(narrative)
        petition_claims = self.extract_claims(petition)

        # Extract chronologies
        narrative_events = self.extract_chronology(narrative)
        petition_events = self.extract_chronology(petition)

        # Compare factual claims
        narrative_facts = [c for c in narrative_claims if c['type'] == 'fact']
        petition_facts = [c for c in petition_claims if c['type'] == 'fact']

        # Check for contradictory dates
        narrative_dates = {e['date'] for e in narrative_events}
        petition_dates = {e['date'] for e in petition_events}

        if narrative_dates and petition_dates:
            # Look for date mismatches (simple heuristic)
            if len(narrative_dates.symmetric_difference(petition_dates)) > 0:
                inconsistencies.append({
                    'type': 'date_mismatch',
                    'description': 'Dates mentioned in narrative differ from petition',
                    'narrative_dates': list(narrative_dates),
                    'petition_dates': list(petition_dates),
                    'severity': 'medium'
                })

        # Check for contradictory allegations
        narrative_allegations = [c['text'] for c in narrative_claims if c['type'] == 'allegation']
        petition_allegations = [c['text'] for c in petition_claims if c['type'] == 'allegation']

        if len(narrative_allegations) < len(petition_allegations) // 2:
            inconsistencies.append({
                'type': 'missing_counter_allegations',
                'description': 'Narrative addresses fewer allegations than presented in petition',
                'petition_count': len(petition_allegations),
                'narrative_count': len(narrative_allegations),
                'severity': 'high'
            })

        return inconsistencies

    def extract_demands(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract specific demands/relief sought

        Args:
            text: Input text

        Returns:
            List of demands with classification
        """
        demands = []

        # Look for prayer/relief sections
        prayer_match = re.search(
            r'(?:PRAYER|RELIEF|WHEREFORE|DEMANDS?)[\s:]+(.+?)(?=\n\n|\Z)',
            text,
            re.IGNORECASE | re.DOTALL
        )

        if prayer_match:
            prayer_text = prayer_match.group(1)

            # Extract numbered demands
            numbered_demands = re.finditer(
                r'(?:^|\n)\s*(?:\d+\.|[a-z]\))\s*(.+?)(?=\n\s*(?:\d+\.|[a-z]\))|$)',
                prayer_text,
                re.MULTILINE | re.DOTALL
            )

            for match in numbered_demands:
                demand_text = match.group(1).strip()
                demands.append({
                    'text': demand_text,
                    'category': self._categorize_demand(demand_text),
                    'source': 'prayer_section'
                })

        # Also extract demands from main text
        claim_demands = [c for c in self.extract_claims(text) if c['type'] in ['demand', 'relief']]
        for claim in claim_demands:
            demands.append({
                'text': claim['text'],
                'category': self._categorize_demand(claim['text']),
                'source': 'main_text'
            })

        return demands

    def _categorize_demand(self, demand_text: str) -> str:
        """Categorize demand by type"""
        text_lower = demand_text.lower()

        if any(word in text_lower for word in ['compensat', 'damag', 'money', 'rs', 'amount']):
            return 'monetary'
        elif any(word in text_lower for word in ['injunction', 'restrain', 'prohibit', 'cease']):
            return 'injunctive'
        elif any(word in text_lower for word in ['declaration', 'declar']):
            return 'declaratory'
        elif any(word in text_lower for word in ['specific performance', 'compel', 'enforce']):
            return 'specific_performance'
        else:
            return 'other'


class DocumentProcessor:
    """Main processor that combines NER and Claim extraction"""

    def __init__(self):
        """Initialize document processor"""
        self.ner_extractor = NERExtractor()
        self.claim_extractor = ClaimExtractor()

    def process_narrative(self, narrative: str) -> Dict[str, Any]:
        """
        Process user's narrative

        Args:
            narrative: User's narrative text

        Returns:
            Structured data with entities, claims, and chronology
        """
        return {
            'entities': self.ner_extractor.extract_entities(narrative),
            'parties': self.ner_extractor.extract_parties(narrative),
            'claims': self.claim_extractor.extract_claims(narrative),
            'chronology': self.claim_extractor.extract_chronology(narrative),
            'demands': self.claim_extractor.extract_demands(narrative),
            'processed_at': datetime.now().isoformat()
        }

    def process_petition(self, petition: str) -> Dict[str, Any]:
        """
        Process opponent's petition

        Args:
            petition: Opponent's petition text

        Returns:
            Structured data with entities, claims, and demands
        """
        return {
            'entities': self.ner_extractor.extract_entities(petition),
            'parties': self.ner_extractor.extract_parties(petition),
            'claims': self.claim_extractor.extract_claims(petition),
            'chronology': self.claim_extractor.extract_chronology(petition),
            'demands': self.claim_extractor.extract_demands(petition),
            'processed_at': datetime.now().isoformat()
        }

    def process_case(
        self,
        narrative: str,
        petition: str
    ) -> Dict[str, Any]:
        """
        Process complete case (narrative + petition)

        Args:
            narrative: User's narrative
            petition: Opponent's petition

        Returns:
            Combined analysis with inconsistencies highlighted
        """
        narrative_data = self.process_narrative(narrative)
        petition_data = self.process_petition(petition)
        inconsistencies = self.claim_extractor.identify_inconsistencies(narrative, petition)

        return {
            'narrative': narrative_data,
            'petition': petition_data,
            'inconsistencies': inconsistencies,
            'analysis': {
                'narrative_claim_count': len(narrative_data['claims']),
                'petition_claim_count': len(petition_data['claims']),
                'inconsistency_count': len(inconsistencies),
                'critical_inconsistencies': [i for i in inconsistencies if i.get('severity') == 'high']
            },
            'processed_at': datetime.now().isoformat()
        }

    def export_json(self, data: Dict[str, Any], filepath: str) -> None:
        """Export processed data to JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_json(self, filepath: str) -> Dict[str, Any]:
        """Load processed data from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)


# Convenience functions for quick access
def extract_entities(text: str) -> Dict[str, List[Dict[str, Any]]]:
    """Quick entity extraction"""
    extractor = NERExtractor()
    return extractor.extract_entities(text)


def extract_claims(text: str) -> List[Dict[str, Any]]:
    """Quick claim extraction"""
    extractor = ClaimExtractor()
    return extractor.extract_claims(text)


def process_case(narrative: str, petition: str) -> Dict[str, Any]:
    """Quick case processing"""
    processor = DocumentProcessor()
    return processor.process_case(narrative, petition)
