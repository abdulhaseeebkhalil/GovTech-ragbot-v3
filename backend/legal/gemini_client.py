import google.generativeai as genai
from typing import List, Dict, Any, Tuple
import re
import json
import os

class EnhancedGeminiClient:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        model_name = os.getenv('GEMINI_MODEL', 'gemini-3.6-flash')
        self.model = genai.GenerativeModel(model_name)
        try:
            self.max_citations = int(os.getenv('RAGBOT_MAX_CITATIONS', '4'))
        except Exception:
            self.max_citations = 4
        
        # Legal document analysis templates
        self.legal_analysis_prompts = {
            'definition': """You are a legal expert analyzing the Khyber Pakhtunkhwa Local Government Act 2013. 
            Provide precise definitions and explanations based on the provided context. Always cite specific sections, articles, or clauses when available.""",
            
            'process': """You are a legal expert explaining procedures and processes from the Khyber Pakhtunkhwa Local Government Act 2013. 
            Break down complex processes into clear, step-by-step instructions. Reference specific legal provisions.""",
            
            'authority': """You are a legal expert explaining powers, authorities, and jurisdictions under the Khyber Pakhtunkhwa Local Government Act 2013. 
            Clearly delineate who has what authority and under which circumstances.""",
            
            'requirements': """You are a legal expert explaining requirements, conditions, and compliance matters under the Khyber Pakhtunkhwa Local Government Act 2013. 
            List all requirements clearly and specify any conditions or exceptions."""
        }
        
    def analyze_query_type(self, query: str) -> str:
        """Analyze query to determine the most appropriate response type"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['what is', 'define', 'definition', 'meaning']):
            return 'definition'
        elif any(word in query_lower for word in ['how to', 'process', 'procedure', 'steps', 'method']):
            return 'process'
        elif any(word in query_lower for word in ['power', 'authority', 'jurisdiction', 'responsibility', 'who can']):
            return 'authority'
        elif any(word in query_lower for word in ['requirement', 'condition', 'must', 'shall', 'need to']):
            return 'requirements'
        else:
            return 'definition'  # Default
    
    def extract_citations(self, context: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Extract and organize citations with pinpoint preference.

        Returns dict including 'precise' list (e.g., Section 55(1)(c)) when
        pinpoint labels are available, else falls back to section-level.
        Enhanced to handle schedule citations with word forms and references.
        """
        citations = {
            'precise': [],
            'sections': [],
            'chapters': [],
            'articles': [],
            'parts': [],
            'schedules': []
        }

        for doc in context:
            metadata = doc.get('metadata', {}) or {}
            labels = doc.get('pinpoint_labels', []) or []

            if metadata.get('section_number'):
                sec_no = str(metadata.get('section_number'))
                if labels:
                    # Join first 2 labels to form nested pinpoint like (1)(a)
                    chain = labels[:2]
                    nested = ''.join([f"({x})" for x in chain])
                    citations['precise'].append(f"Section {sec_no}{nested}")
                # Always add the base section reference once
                sec_ref = f"Section {sec_no}"
                title = metadata.get('section') or metadata.get('title')
                if title:
                    sec_ref += f": {title}"
                citations['sections'].append(sec_ref)

            if metadata.get('chapter_number'):
                chapter_ref = f"Chapter {metadata['chapter_number']}"
                if metadata.get('chapter'):
                    chapter_ref += f": {metadata['chapter']}"
                citations['chapters'].append(chapter_ref)

            if metadata.get('article_number'):
                article_ref = f"Article {metadata['article_number']}"
                if metadata.get('article'):
                    article_ref += f": {metadata['article']}"
                citations['articles'].append(article_ref)

            if metadata.get('part_number'):
                part_ref = f"Part {metadata['part_number']}"
                if metadata.get('part'):
                    part_ref += f": {metadata['part']}"
                citations['parts'].append(part_ref)

            # Enhanced schedule citation extraction
            if metadata.get('schedule_ref'):
                # schedule_ref already contains formatted reference (e.g., "Fifth Schedule [See section 66]")
                sched = metadata['schedule_ref']
                # Add title if present and not already in ref
                title = metadata.get('title', '').strip()
                if title and title not in sched:
                    sched += f": {title}"
                citations['schedules'].append(sched)
            elif metadata.get('schedule_number'):
                # Build schedule reference from components
                schedule_num = metadata['schedule_number']
                schedule_word = metadata.get('schedule_word', '')

                if schedule_word:
                    # Use word form (e.g., "Fifth Schedule")
                    sched = f"{schedule_word.title()} Schedule"
                else:
                    sched = f"Schedule {schedule_num}"

                # Add section reference if available
                section_ref = metadata.get('section_reference', '')
                if section_ref:
                    sched += f" [See section {section_ref}]"

                # Add title if available
                title = metadata.get('schedule') or metadata.get('title')
                if title:
                    sched += f": {title}"

                citations['schedules'].append(sched)

            # Handle schedule parts
            if metadata.get('is_schedule_part'):
                parent_num = metadata.get('schedule_number')
                parent_word = metadata.get('schedule_word', '')
                part_id = metadata.get('part_id', '')

                if parent_word:
                    sched = f"{parent_word.title()} Schedule - {part_id}"
                elif parent_num:
                    sched = f"Schedule {parent_num} - {part_id}"
                else:
                    sched = part_id

                part_title = metadata.get('part_title', '')
                if part_title:
                    sched += f": {part_title}"

                citations['schedules'].append(sched)

        # Remove duplicates while preserving order
        for key in citations:
            citations[key] = list(dict.fromkeys(citations[key]))

        return citations
    
    def create_enhanced_context(self, context: List[Dict[str, Any]]) -> Tuple[str, Dict]:
        """Create enhanced context with metadata and citations"""
        context_parts = []
        all_metadata = []
        
        for i, doc in enumerate(context):
            metadata = doc.get('metadata', {})
            text = doc.get('text', '')
            score = doc.get('score', 0)
            
            # Create structured context entry
            context_entry = f"Section {i+1} (Relevance: {score:.3f})"
            
            # Add metadata information
            if metadata:
                meta_parts = []
                if metadata.get('chapter'):
                    meta_parts.append(f"Chapter: {metadata['chapter']}")
                if metadata.get('part'):
                    meta_parts.append(f"Part: {metadata['part']}")
                # Section with number if available
                if metadata.get('section') or metadata.get('section_number'):
                    sec_num = metadata.get('section_number')
                    sec_title = metadata.get('section') or metadata.get('title')
                    if sec_num and sec_title:
                        meta_parts.append(f"Section {sec_num}: {sec_title}")
                    elif sec_num:
                        meta_parts.append(f"Section {sec_num}")
                    elif sec_title:
                        meta_parts.append(f"Section: {sec_title}")
                if metadata.get('article'):
                    meta_parts.append(f"Article: {metadata['article']}")
                # Schedule - enhanced display
                if metadata.get('schedule_ref'):
                    # Use pre-formatted schedule reference
                    meta_parts.append(metadata['schedule_ref'])
                elif metadata.get('schedule_number'):
                    sched_num = metadata.get('schedule_number')
                    sched_word = metadata.get('schedule_word', '')
                    sched_title = metadata.get('schedule') or metadata.get('title')
                    section_ref = metadata.get('section_reference', '')

                    if sched_word:
                        sched_display = f"{sched_word.title()} Schedule"
                    else:
                        sched_display = f"Schedule {sched_num}"

                    if section_ref:
                        sched_display += f" [See section {section_ref}]"

                    if sched_title:
                        sched_display += f": {sched_title}"

                    meta_parts.append(sched_display)

                # Schedule part
                if metadata.get('is_schedule_part'):
                    part_id = metadata.get('part_id', '')
                    if part_id:
                        meta_parts.append(f"Part: {part_id}")

                if meta_parts:
                    context_entry += f" - {', '.join(meta_parts)}"
            
            # Prefer a pre-sliced snippet when available to keep grounding tight
            snippet = doc.get('sliced_text') or text
            context_entry += f"\n{snippet}\n"
            context_parts.append(context_entry)
            all_metadata.append(metadata)
        
        context_text = "\n".join(context_parts)
        citations = self.extract_citations(context)
        
        return context_text, citations
    
    def _extract_focus_terms(self, query: str) -> List[str]:
        q = (query or '').lower()
        base = [t for t in re.findall(r"\b\w+\b", q) if len(t) > 2]
        clusters = []
        if any(t in q for t in ['dispute','conflict','resolution','arbitration','mediation','appeal','complaint','grievance']):
            clusters += ['dispute','conflict','resolution','arbitration','mediation','appeal','complaint','grievance','conciliation']
        return list(dict.fromkeys(base + clusters))

    def _gap_awareness(self, query: str, context: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Detect if explicit mechanisms asked are absent in the provided context."""
        focus = self._extract_focus_terms(query)
        need_arbitration = any(k in focus for k in ['arbitration','mediator','mediation','ombudsman','independent'])
        hay = ' '.join([(doc.get('sliced_text') or doc.get('text') or '').lower() for doc in context])
        has_arb = any(k in hay for k in ['arbitration','mediator','mediation','conciliation','ombudsman'])
        return {
            'ask_alt_mechanism': need_arbitration and not has_arb
        }

    def generate_response(self, query: str, context: List[Dict[str, Any]]) -> str:
        """Generate enhanced response using Gemini with advanced RAG context"""
        
        if not context:
            return "I don't have sufficient information from the KPK Local Government Act 2013 to answer your question. Please try rephrasing your query or ask about specific topics covered in the act."
        
        # Analyze query type for appropriate prompting
        query_type = self.analyze_query_type(query)
        base_prompt = self.legal_analysis_prompts.get(query_type, self.legal_analysis_prompts['definition'])
        
        # Create enhanced context with metadata
        context_text, citations = self.create_enhanced_context(context)

        # Gap awareness detection
        gaps = self._gap_awareness(query, context)
        
        # Build comprehensive prompt
        prompt = f"""{base_prompt}

RELEVANT SECTIONS FROM KPK LOCAL GOVERNMENT ACT 2013:
{context_text}

USER QUESTION: {query}

RESPONSE REQUIREMENTS:
1. Base the answer strictly on provided sections. Do not include unrelated provisions.
2. Use pinpoint statutory citations where possible (e.g., Section 55(1)(c)), not chapter-level.
3. Enforce a max of {self.max_citations} citations; select only the most relevant sections.
4. If the Act lacks an explicit mechanism asked by the user{', e.g., independent arbitration' if gaps.get('ask_alt_mechanism') else ''}, state this absence clearly instead of padding.
5. Organize succinctly; avoid filler. Prefer direct rules over summaries.
6. If multiple provisions apply, explain the relationship briefly.

RESPONSE FORMAT:
- Start with a direct answer to the question
- Provide detailed explanation based on the sections
- Include relevant citations in format: (Section X, Clause/Article Y)
- End with any important caveats or related information

ANSWER:"""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Post-process response to add citation summary (capped)
            citation_summary = self.create_citation_summary(citations)
            if citation_summary:
                response_text += f"\n\n**LEGAL REFERENCES:**\n{citation_summary}"
            
            return response_text
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def create_citation_summary(self, citations: Dict[str, List[str]]) -> str:
        """Create a summary of legal citations"""
        summary_parts = []

        # Prefer precise citations first
        precise = citations.get('precise', [])
        sections = citations.get('sections', [])

        ordered: List[str] = []
        ordered.extend(precise)
        # Include base section refs only if we have room after precise
        if len(ordered) < self.max_citations:
            for s in sections:
                if s not in ordered:
                    ordered.append(s)
                    if len(ordered) >= self.max_citations:
                        break

        if ordered:
            summary_parts.append(f"• **Sections**: {', '.join(ordered[:self.max_citations])}")

        # Add other containers only if still under cap and present
        remaining_slots = max(0, self.max_citations - len(ordered))
        for bucket in ('schedules', 'articles', 'parts', 'chapters'):
            if remaining_slots <= 0:
                break
            bucket_refs = citations.get(bucket, [])
            if bucket_refs:
                take = bucket_refs[:remaining_slots]
                summary_parts.append(f"• **{bucket.capitalize()}**: {', '.join(take)}")
                remaining_slots -= len(take)

        return '\n'.join(summary_parts) if summary_parts else ""
    
    def generate_detailed_analysis(self, query: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate detailed analysis with structured output"""
        response_text = self.generate_response(query, context)
        
        # Extract key information
        analysis = {
            'response': response_text,
            'query_type': self.analyze_query_type(query),
            'citations': self.extract_citations(context),
            'context_quality': {
                'num_sources': len(context),
                'avg_relevance': sum(doc.get('score', 0) for doc in context) / len(context) if context else 0,
                'has_metadata': any(doc.get('metadata') for doc in context)
            },
            'coverage_analysis': self.analyze_coverage(query, context)
        }
        
        return analysis
    
    def analyze_coverage(self, query: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze how well the context covers the query"""
        query_terms = set(query.lower().split())
        
        coverage_stats = {
            'query_terms_found': 0,
            'total_query_terms': len(query_terms),
            'sources_with_matches': 0,
            'key_terms_coverage': {}
        }
        
        key_legal_terms = [
            'government', 'council', 'committee', 'district', 'union',
            'power', 'function', 'duty', 'authority', 'election',
            'budget', 'planning', 'development', 'service'
        ]
        
        for term in key_legal_terms:
            if term in query.lower():
                coverage_stats['key_terms_coverage'][term] = 0
                for doc in context:
                    if term in doc.get('text', '').lower():
                        coverage_stats['key_terms_coverage'][term] += 1
        
        # Count query terms found in context
        found_terms = set()
        sources_with_matches = 0
        
        for doc in context:
            doc_text = doc.get('text', '').lower()
            doc_has_match = False
            
            for term in query_terms:
                if term in doc_text:
                    found_terms.add(term)
                    doc_has_match = True
            
            if doc_has_match:
                sources_with_matches += 1
        
        coverage_stats['query_terms_found'] = len(found_terms)
        coverage_stats['sources_with_matches'] = sources_with_matches
        coverage_stats['coverage_percentage'] = (len(found_terms) / len(query_terms)) * 100 if query_terms else 0
        
        return coverage_stats
    
    def generate_summary(self, text: str, max_length: int = 200) -> str:
        """Generate a summary of the given text"""
        prompt = f"""Please provide a concise summary of the following text in approximately {max_length} words:

{text}

Summary:"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def extract_key_topics(self, text: str) -> List[str]:
        """Extract key topics from the text"""
        prompt = f"""Extract the main topics and themes from this legal document. 
Provide a bulleted list of key topics covered:

{text}

Key Topics:"""
        
        try:
            response = self.model.generate_content(prompt)
            # Parse the response to extract topics
            topics = []
            for line in response.text.split('\n'):
                if line.strip().startswith('-') or line.strip().startswith('•'):
                    topics.append(line.strip()[1:].strip())
            return topics
        except Exception as e:
            return [f"Error extracting topics: {str(e)}"]

# For backward compatibility
GeminiClient = EnhancedGeminiClient
