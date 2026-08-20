import PyPDF2
import pdfplumber
import fitz  # PyMuPDF
from typing import Dict, Any, List, Optional, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re
from collections import defaultdict

"""
Note: Removed NLTK dependency.
The processor previously ensured NLTK tokenizers were present, but the
implementation does not use NLTK anywhere else. Keeping NLTK imported can
trigger heavy optional imports (e.g., scikit-learn) and cause binary
incompatibility issues in some environments. This file now operates
independently of NLTK.
"""


class AdvancedPDFProcessor:
    def __init__(self, chunk_size: int = 900, chunk_overlap: int = 350):
        # Use slightly larger defaults to keep dense legal clauses together.
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Multiple text splitters for different strategies and granularities.
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        self.semantic_splitter = RecursiveCharacterTextSplitter(
            chunk_size=int(chunk_size * 1.75),
            chunk_overlap=int(chunk_overlap * 1.5),
            length_function=len,
            separators=["\n\nCHAPTER", "\n\nARTICLE", "\n\nSECTION", "\n\nPART", "\n\n", "\n", ". ", " "]
        )

        # Clause-level splitter keeps sub-clauses intact for targeted lookups.
        self.clause_splitter = RecursiveCharacterTextSplitter(
            chunk_size=int(chunk_size * 0.75),
            chunk_overlap=int(chunk_overlap / 2),
            length_function=len,
            separators=["\n\n", "\n", "; ", ". ", " "]
        )

        # Structure patterns for legal documents (extended for schedules and rules).
        self.structure_patterns = {
            'chapter': re.compile(r'^CHAPTER\s+([IVXLCDM]+|\d+)[\s\-–—]+(.+?)(?=\n|$)', re.IGNORECASE | re.MULTILINE),
            # Section headings come in multiple styles across Acts.
            # 1) "SECTION 15 — Title" or "SEC. 15: Title"
            # 2) "15. Title" at the start of a line (common in PK Acts)
            # Use a single alternation-based pattern with named groups to ease extraction.
            'section': re.compile(
                r'^(?:\s*(?:SECTION|SEC\.?)\s+(?P<section_num1>\d+[A-Z]?(?:-\d+)?)\s*[\-–—:]\s*(?P<section_title1>.+?)\s*$)'
                r'|^(?P<section_num2>\d+[A-Z]?(?:-\d+)?)\.?\s+(?P<section_title2>[^\n]+?)\s*$',
                re.IGNORECASE | re.MULTILINE
            ),
            'article': re.compile(r'^(?:ARTICLE|ART\.?)\s+(\d+[A-Z]?)\s*[\-–—:]\s*(.+?)(?=\n|$)', re.IGNORECASE | re.MULTILINE),
            'part': re.compile(r'^PART\s+([IVXLCDM]+|\d+)[\s\-–—]+(.+?)(?=\n|$)', re.IGNORECASE | re.MULTILINE),
            'rule': re.compile(r'^(?:RULE|R\.)\s+(\d+[A-Z]?)\s*[\-–—:]\s*(.+?)(?=\n|$)', re.IGNORECASE | re.MULTILINE),
            # Enhanced schedule pattern to match word-based schedules (FIRST, SECOND, etc.)
            'schedule': re.compile(
                r'^(\d+\[)?(?:FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH|ELEVENTH|TWELFTH|[IVXLCDM]+|\d+)\s+SCHEDULE',
                re.IGNORECASE | re.MULTILINE
            ),
            'clause': re.compile(r'^\((\d+)\)\s+(.+?)(?=\n\(\d+\)|\n[A-Z]|\n\n|$)', re.MULTILINE | re.DOTALL),
            'subsection': re.compile(r'^\(([a-z])\)\s+(.+?)(?=\n\([a-z]\)|\n\(\d+\)|\n[A-Z]|\n\n|$)', re.MULTILINE | re.DOTALL),
            'subclause': re.compile(r'^\(([ivxlcdm]+)\)\s+(.+?)(?=\n\([ivxlcdm]+\)|\n\([a-z]\)|\n\n|$)', re.IGNORECASE | re.MULTILINE | re.DOTALL)
        }

        # Schedule word-to-number mapping for normalization
        self.schedule_word_to_num = {
            'FIRST': '1', 'SECOND': '2', 'THIRD': '3', 'FOURTH': '4',
            'FIFTH': '5', 'SIXTH': '6', 'SEVENTH': '7', 'EIGHTH': '8',
            'NINTH': '9', 'TENTH': '10', 'ELEVENTH': '11', 'TWELFTH': '12'
        }
    
    def extract_text_multiple_methods(self, pdf_path: str) -> Dict[str, str]:
        """Extract text using multiple methods and choose the best"""
        methods = {}
        
        # Method 1: PDFPlumber (best for structured text)
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                methods['pdfplumber'] = text
        except Exception as e:
            print(f"PDFPlumber extraction failed: {e}")
            methods['pdfplumber'] = ""
        
        # Method 2: PyMuPDF (good for complex layouts)
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            methods['pymupdf'] = text
        except Exception as e:
            print(f"PyMuPDF extraction failed: {e}")
            methods['pymupdf'] = ""
        
        # Method 3: PyPDF2 (fallback)
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                methods['pypdf2'] = text
        except Exception as e:
            print(f"PyPDF2 extraction failed: {e}")
            methods['pypdf2'] = ""
        
        scored_methods = {
            name: (self.score_extraction_quality(content), len(content))
            for name, content in methods.items()
        }

        best_method = max(scored_methods.items(), key=lambda item: item[1])[0]
        quality_score, char_count = scored_methods[best_method]
        print(f"✅ Best extraction method: {best_method} | quality={quality_score:.3f} | chars={char_count}")

        return methods[best_method]

    def score_extraction_quality(self, text: str) -> float:
        """Heuristic quality score preferring rich, well-structured legal text."""
        if not text:
            return 0.0

        total_chars = len(text)
        ascii_ratio = sum(1 for ch in text if ord(ch) < 128) / total_chars

        legal_markers = re.findall(r'(?:section|chapter|part|schedule|clause|article)\s+(?:[IVXLCDM]+|\d+[A-Z]?)', text.lower())
        marker_density = min(len(legal_markers) / max(total_chars / 4000, 1), 1.0)

        tokens = [token for token in re.split(r'\W+', text.lower()) if token]
        unique_tokens = len(set(tokens))
        lexical_diversity = min(unique_tokens / max(len(tokens), 1), 1.0)

        noise_ratio = text.count('\x00') / total_chars

        length_score = min(total_chars / 35000, 1.0)

        score = (
            length_score * 0.35
            + marker_density * 0.35
            + lexical_diversity * 0.2
            + ascii_ratio * 0.1
        )

        score *= max(1 - noise_ratio, 0.85)
        return score
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file using the best available method"""
        text = self.extract_text_multiple_methods(pdf_path)
        return self.clean_text(text)
    
    def clean_text(self, text: str) -> str:
        """Advanced text cleaning and normalization"""
        if not text:
            return ""
        
        # Preserve legal structure markers and add spacing around them.
        def pad_header(match: re.Match) -> str:
            header = match.group('header').strip()
            prefix = '' if match.start() == 0 else '\n\n'
            return f"{prefix}{header}"

        text = re.sub(
            r'(?:^|\n)(?P<header>(?:CHAPTER|SECTION|PART|ARTICLE|SCHEDULE|RULE|CLAUSE|SUB-CLAUSE)[^\n]*)',
            pad_header,
            text
        )

        # Fix common OCR errors and harmonise casing for key legal nouns.
        ocr_fixes = {
            r'\bG0vernment\b': 'Government',
            r'\bGovt\b': 'Government',
            r'\bcommittee\b': 'Committee',
            r'\bco\-?operative\b': 'co-operative',
            r'\blocal\s+govt\b': 'local government',
            r'\bP\.?M\.?U\b': 'PMU',
            r'\btehsil\b': 'Tehsil',
            r'\bdistrict\b': 'District',
            r'\bunion\b': 'Union',
            r'\btown\b': 'Town',
            r'\bfunctions?\b': 'functions',
            r'\bduties\b': 'duties',
            r'\bresponsibilit(?:y|ies)\b': 'responsibilities'
        }
        
        for pattern, replacement in ocr_fixes.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Clean up spacing and formatting to keep paragraphs stable.
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r'[ \t]{2,}', ' ', text)
        text = re.sub(r'\x0c', '\n', text)  # Remove form feed page delimiters

        # Fix broken sentences and hyphenated line breaks commonly found in scans.
        text = re.sub(r'([a-zA-Z])\-\n([a-zA-Z])', r'\1\2', text)
        text = re.sub(r'([a-z])\n([a-z])', r'\1 \2', text)
        text = re.sub(r'([.!?])\s*\n([A-Z])', r'\1\n\n\2', text)

        # Preserve legal numbering and structure
        text = re.sub(r'\n(\d+\.|\([a-z]\)|\([0-9]+\)|\([ivxlcdm]+\))', r'\n\n\1', text, flags=re.IGNORECASE)

        return text.strip()
    
    def extract_document_structure(self, text: str) -> Dict[str, List[Dict]]:
        """Extract hierarchical structure from legal document"""
        structure = defaultdict(list)

        for structure_type, pattern in self.structure_patterns.items():
            seen_keys = set()
            for match in pattern.finditer(text):
                if structure_type == 'section':
                    # Handle alternation groups
                    number = None
                    title = ""
                    if match.group('section_num1'):
                        number = match.group('section_num1')
                        title = match.group('section_title1') or ""
                    elif match.group('section_num2'):
                        number = match.group('section_num2')
                        title = match.group('section_title2') or ""
                    if not number:
                        continue
                elif structure_type == 'schedule':
                    # Enhanced schedule extraction
                    full_match = match.group(0)
                    # Extract the schedule identifier (word or number)
                    schedule_id_match = re.search(
                        r'(FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH|ELEVENTH|TWELFTH|[IVXLCDM]+|\d+)\s+SCHEDULE',
                        full_match,
                        re.IGNORECASE
                    )
                    if not schedule_id_match:
                        continue

                    schedule_word = schedule_id_match.group(1).upper()
                    # Normalize to number
                    if schedule_word in self.schedule_word_to_num:
                        number = self.schedule_word_to_num[schedule_word]
                    elif schedule_word.isdigit():
                        number = schedule_word
                    else:
                        # Roman numeral - convert to number
                        try:
                            number = str(self._roman_to_int(schedule_word))
                        except:
                            number = schedule_word

                    # Extract reference marker and title from next few lines
                    start_pos = match.start()
                    end_pos = min(start_pos + 500, len(text))
                    snippet = text[start_pos:end_pos]

                    # Look for [See section X] pattern
                    reference = ""
                    ref_match = re.search(r'\[See\s+section\s+([^\]]+)\]', snippet, re.IGNORECASE)
                    if ref_match:
                        reference = ref_match.group(1).strip()

                    # Extract title (typically on the next non-empty line after header)
                    lines = snippet.split('\n')
                    title = ""
                    for line in lines[1:6]:  # Check next 5 lines
                        line = line.strip()
                        if line and not line.startswith('[') and len(line) > 3:
                            # Skip if it looks like another heading
                            if not re.match(r'^(PART|CHAPTER|SECTION|SCHEDULE)', line, re.IGNORECASE):
                                title = line
                                break

                    # Store both the word form and normalized number
                    structure[structure_type].append({
                        'number': number,
                        'schedule_word': schedule_word,
                        'title': title,
                        'reference': reference,
                        'type': structure_type,
                        'start_index': match.start()
                    })
                    continue
                else:
                    number = match.group(1) if match.lastindex else match.group(0)
                    title = match.group(2) if match.lastindex and match.lastindex >= 2 else ""

                key = (structure_type, str(number).strip().lower())
                if key in seen_keys:
                    continue
                seen_keys.add(key)

                structure[structure_type].append({
                    'number': str(number).strip(),
                    'title': str(title).strip(),
                    'type': structure_type,
                    'start_index': match.start()
                })

        return dict(structure)

    def _roman_to_int(self, s: str) -> int:
        """Convert Roman numeral to integer"""
        roman_map = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
        s = s.upper()
        result = 0
        prev_value = 0
        for char in reversed(s):
            value = roman_map.get(char, 0)
            if value < prev_value:
                result -= value
            else:
                result += value
            prev_value = value
        return result

    def create_section_scoped_chunks(self, text: str) -> List[Dict[str, Any]]:
        """Create chunks strictly scoped by Section and Schedule.

        Each chunk represents one complete Section (or Schedule item) with
        metadata: {section_number, title, schedule_ref}. This ensures retrieval
        always returns a whole Section/Schedule, never a fragment.
        """
        if not text:
            return []

        structure = self.extract_document_structure(text)

        # Gather only section and schedule headers with positions
        headers: List[Dict[str, Any]] = []
        for item in structure.get('section', []):
            headers.append({
                'type': 'section',
                'number': item.get('number'),
                'title': item.get('title', ''),
                'start_index': item.get('start_index', 0)
            })
        for item in structure.get('schedule', []):
            headers.append({
                'type': 'schedule',
                'number': item.get('number'),
                'schedule_word': item.get('schedule_word', ''),
                'title': item.get('title', ''),
                'reference': item.get('reference', ''),  # [See section X]
                'start_index': item.get('start_index', 0)
            })

        if not headers:
            # Fallback: attempt to heuristically split by numeric headings "N. Title"
            alt_pattern = re.compile(r'(?im)^(?P<num>\d+[A-Z]?(?:-\d+)?)\.?\s+(?P<title>[^\n]+)$')
            for m in alt_pattern.finditer(text):
                headers.append({
                    'type': 'section',
                    'number': m.group('num'),
                    'title': m.group('title').strip(),
                    'start_index': m.start()
                })

        # Sort headers by position and drop obvious duplicates (same type+number at same start)
        headers.sort(key=lambda x: x['start_index'])
        unique: List[Dict[str, Any]] = []
        seen = set()
        for h in headers:
            key = (h['type'], str(h.get('number')).lower(), h['start_index'])
            if key in seen:
                continue
            seen.add(key)
            unique.append(h)
        headers = unique

        # Build chunks from header to next header (or end)
        chunks: List[Dict[str, Any]] = []
        n = len(headers)
        for i, h in enumerate(headers):
            start = h['start_index']
            end = headers[i + 1]['start_index'] if i + 1 < n else len(text)
            raw = text[start:end].strip()
            if not raw:
                continue

            if h['type'] == 'section':
                metadata = {
                    'section_number': h.get('number'),
                    'title': h.get('title') or '',
                    'schedule_ref': None,
                    # Preserve compatibility with UI and embeddings
                    'section': h.get('title') or '',
                    'section_number_normalised': h.get('number')
                }
            else:  # schedule
                schedule_num = h.get('number')
                schedule_word = h.get('schedule_word', '')
                schedule_title = h.get('title', '')
                schedule_ref_section = h.get('reference', '')

                # Build comprehensive schedule reference
                if schedule_word and schedule_word.upper() in self.schedule_word_to_num:
                    # Use word form for display (e.g., "FIFTH SCHEDULE")
                    schedule_display = f"{schedule_word.title()} Schedule"
                else:
                    schedule_display = f"Schedule {schedule_num}"

                # Add section reference if present
                if schedule_ref_section:
                    schedule_display += f" [See section {schedule_ref_section}]"

                # Detect schedule parts for hierarchical structure
                parts = self._extract_schedule_parts(raw)

                metadata = {
                    'section_number': None,
                    'title': schedule_title,
                    'schedule_ref': schedule_display,
                    'schedule_number': schedule_num,
                    'schedule_word': schedule_word,
                    'schedule_ordinal': int(schedule_num) if schedule_num.isdigit() else None,
                    'section_reference': schedule_ref_section,
                    'schedule': schedule_title,
                    'has_parts': len(parts) > 0,
                    'parts': [p['part_id'] for p in parts] if parts else [],
                    'schedule_type': self._classify_schedule_type(raw, schedule_title)
                }

                # Enrich with schedule-specific key terms
                metadata['key_terms'] = self.extract_key_terms(raw) + [
                    'schedule', schedule_word.lower() if schedule_word else '',
                    f'schedule_{schedule_num}', schedule_title.lower() if schedule_title else ''
                ]
                metadata['key_terms'] = [t for t in metadata['key_terms'] if t]  # Remove empty strings

                chunks.append({
                    'text': raw,
                    'metadata': metadata
                })

                # Create additional sub-chunks for parts if schedule is large and has parts
                if len(raw) > 2000 and parts:
                    for part_info in parts:
                        part_metadata = metadata.copy()
                        part_metadata['is_schedule_part'] = True
                        part_metadata['part_id'] = part_info['part_id']
                        part_metadata['part_title'] = part_info.get('title', '')
                        part_metadata['title'] = f"{schedule_title} - {part_info['part_id']}" if schedule_title else part_info['part_id']

                        chunks.append({
                            'text': part_info['text'],
                            'metadata': part_metadata
                        })
                continue

            # Enrich with key terms for search (sections)
            metadata['key_terms'] = self.extract_key_terms(raw)

            chunks.append({
                'text': raw,
                'metadata': metadata
            })

        return chunks

    def _extract_schedule_parts(self, schedule_text: str) -> List[Dict[str, Any]]:
        """Extract Part subdivisions from a schedule (e.g., Part-A, Part-I, Part-II)"""
        parts = []
        # Pattern for parts: "PART-A", "Part-I", "Part- II", etc.
        part_pattern = re.compile(r'^(PART[-\s]*([IVXLCDM]+|[A-Z]|[0-9]+))\s*$', re.IGNORECASE | re.MULTILINE)

        lines = schedule_text.split('\n')
        part_starts = []

        for i, line in enumerate(lines):
            match = part_pattern.match(line.strip())
            if match:
                part_id = match.group(1).strip()
                part_starts.append((i, part_id))

        # Extract text for each part
        for idx, (line_num, part_id) in enumerate(part_starts):
            start_line = line_num
            end_line = part_starts[idx + 1][0] if idx + 1 < len(part_starts) else len(lines)

            part_lines = lines[start_line:end_line]
            part_text = '\n'.join(part_lines).strip()

            # Try to extract title (line after part header)
            title = ''
            if len(part_lines) > 1:
                potential_title = part_lines[1].strip()
                if potential_title and len(potential_title) < 100:
                    title = potential_title

            if part_text and len(part_text) > 50:  # Minimum content threshold
                parts.append({
                    'part_id': part_id,
                    'title': title,
                    'text': part_text
                })

        return parts

    def _classify_schedule_type(self, schedule_text: str, schedule_title: str) -> str:
        """Classify the type of schedule based on content"""
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
        elif any(word in text_lower for word in ['delimitation', 'boundary', 'district']):
            return 'delimitation'
        else:
            return 'general'
    
    def create_hierarchical_chunks(self, text: str, structure: Dict) -> List[Dict[str, Any]]:
        """Create multi-granular chunks with hierarchical context and metadata."""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        if not paragraphs:
            return []

        structure_lookup = {
            key: {item['number'].strip().lower(): item for item in items}
            for key, items in structure.items()
        }

        current_context = {
            'chapter': None,
            'part': None,
            'section': None,
            'article': None,
            'rule': None,
            'schedule': None
        }

        chunks_with_metadata: List[Dict[str, Any]] = []

        for index, paragraph in enumerate(paragraphs):
            current_context = self._update_structure_context(paragraph, structure_lookup, current_context)
            augmented_text = self._add_neighbor_context(paragraphs, index)

            metadata = self._build_metadata(index, paragraph, augmented_text, current_context)
            chunks_with_metadata.append({'text': augmented_text, 'metadata': metadata})

            # Generate clause-level variants for needle-in-the-haystack lookups.
            clause_blocks = self._extract_clause_blocks(paragraph)
            for clause in clause_blocks:
                clause_metadata = metadata.copy()
                clause_metadata.update({
                    'is_clause_variant': True,
                    'clause_label': clause['label'],
                    'original_text': clause['text'],
                    'word_count': len(clause['text'].split()),
                    'char_count': len(clause['text'])
                })
                clause_metadata['key_terms'] = self.extract_key_terms(clause['text'])
                chunks_with_metadata.append({
                    'text': clause['text'],
                    'metadata': clause_metadata
                })

        return chunks_with_metadata

    def _add_neighbor_context(self, paragraphs: List[str], idx: int, window: int = 1) -> str:
        """Fuse neighbouring paragraphs to preserve cross-clause context."""
        window_paragraphs = []
        start = max(0, idx - window)
        end = min(len(paragraphs), idx + window + 1)
        for pointer in range(start, end):
            snippet = paragraphs[pointer]
            if pointer != idx:
                snippet = snippet[:200] if pointer > idx else snippet[-200:]
            window_paragraphs.append(snippet.strip())
        return '\n'.join([part for part in window_paragraphs if part])

    def _update_structure_context(
        self,
        paragraph: str,
        structure_lookup: Dict[str, Dict[str, Dict[str, Any]]],
        current_context: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Update current context if this paragraph introduces a new structural unit."""
        updated_context = current_context.copy()
        header_span = paragraph[:200]

        for structure_type in ['chapter', 'part', 'section', 'article', 'rule', 'schedule']:
            pattern = self.structure_patterns.get(structure_type)
            if not pattern:
                continue
            match = pattern.search(header_span)
            if match:
                number = match.group(1).strip().lower()
                matched_item = structure_lookup.get(structure_type, {}).get(number)
                if matched_item:
                    updated_context[structure_type] = matched_item
        return updated_context

    def _build_metadata(
        self,
        paragraph_index: int,
        original_text: str,
        enhanced_text: str,
        context: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        metadata = {
            'paragraph_index': paragraph_index,
            'original_text': original_text,
            'enhanced_text': enhanced_text,
            'word_count': len(original_text.split()),
            'char_count': len(original_text),
        }

        for field in ['chapter', 'part', 'section', 'article', 'rule', 'schedule']:
            item = context.get(field)
            metadata[field] = item['title'] if item else None
            metadata[f'{field}_number'] = item['number'] if item else None

        metadata['key_terms'] = self.extract_key_terms(original_text)
        return metadata

    def _extract_clause_blocks(self, paragraph: str) -> List[Dict[str, str]]:
        """Extract clause-level blocks (1), (a), (i) to support precise retrieval."""
        lines = [line.strip() for line in paragraph.split('\n') if line.strip()]
        clause_blocks: List[Dict[str, str]] = []
        current_label = None
        current_lines: List[str] = []

        clause_pattern = re.compile(r'^\((\d+|[a-z]|[ivxlcdm]+)\)\s+', re.IGNORECASE)
        numbered_pattern = re.compile(r'^(\d+\.)\s+')

        for line in lines:
            match = clause_pattern.match(line) or numbered_pattern.match(line)
            if match:
                if current_label is not None and current_lines:
                    clause_blocks.append({
                        'label': current_label,
                        'text': ' '.join(current_lines).strip()
                    })
                current_label = match.group(1)
                current_lines = [line]
            elif current_label is not None:
                current_lines.append(line)

        if current_label is not None and current_lines:
            clause_blocks.append({
                'label': current_label,
                'text': ' '.join(current_lines).strip()
            })

        return clause_blocks
    
    def extract_key_terms(self, text: str) -> List[str]:
        """Extract key legal terms and concepts"""
        # Legal terms common in government acts
        legal_terms = [
            'government', 'council', 'committee', 'district', 'union', 'local',
            'power', 'function', 'duty', 'responsibility', 'authority', 'jurisdiction',
            'election', 'member', 'chairman', 'mayor', 'administrator', 'officer',
            'budget', 'fund', 'tax', 'fee', 'development', 'planning', 'scheme',
            'notification', 'rule', 'regulation', 'ordinance', 'act', 'law',
            'procedure', 'process', 'requirement', 'condition', 'provision',
            'public', 'private', 'service', 'welfare', 'health', 'education',
            'infrastructure', 'utilities', 'water', 'sanitation', 'waste'
        ]
        
        found_terms = []
        text_lower = text.lower()
        
        for term in legal_terms:
            if term in text_lower:
                found_terms.append(term)
        
        # Extract numerical references (sections, articles, etc.)
        numbers = re.findall(r'(?:section|article|chapter|part)\s+(\d+)', text_lower)
        found_terms.extend([f"ref_{num}" for num in numbers])
        
        return list(set(found_terms))
    
    def create_overlapping_chunks(self, chunks_with_metadata: List[Dict]) -> List[Dict[str, Any]]:
        """Create additional overlapping chunks for better context coverage"""
        overlapping_chunks = []

        base_chunks = [chunk for chunk in chunks_with_metadata if not chunk['metadata'].get('is_clause_variant')]

        for i in range(len(base_chunks) - 1):
            current_chunk = base_chunks[i]
            next_chunk = base_chunks[i + 1]

            # Create overlapping chunk
            overlap_text = f"{current_chunk['text'][-300:]} {next_chunk['text'][:300]}"

            overlap_metadata = current_chunk['metadata'].copy()
            overlap_metadata['is_overlap'] = True
            overlap_metadata['overlap_with'] = [current_chunk['metadata']['paragraph_index'], next_chunk['metadata']['paragraph_index']]
            overlap_metadata['original_text'] = overlap_text
            overlap_metadata['enhanced_text'] = overlap_text

            overlapping_chunks.append({
                'text': overlap_text,
                'metadata': overlap_metadata
            })
        
        return overlapping_chunks
    
    def chunk_text_advanced(self, text: str, structure: Dict) -> List[Dict[str, Any]]:
        """Advanced chunking with metadata and overlapping"""
        # Create hierarchical chunks
        hierarchical_chunks = self.create_hierarchical_chunks(text, structure)

        # Create overlapping chunks
        overlapping_chunks = self.create_overlapping_chunks(hierarchical_chunks)

        # Combine all chunks
        all_chunks = hierarchical_chunks + overlapping_chunks

        seen_hashes = set()
        filtered_chunks = []
        for chunk in all_chunks:
            text_body = chunk['text'].strip()
            chunk_hash = hash(text_body)
            if chunk_hash in seen_hashes:
                continue
            seen_hashes.add(chunk_hash)

            if len(text_body.split()) < 10 or len(text_body) < 50:
                continue

            chunk['metadata']['key_terms'] = self.extract_key_terms(text_body)
            filtered_chunks.append(chunk)

        return filtered_chunks
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks for vector storage (backward compatibility)"""
        chunks = self.text_splitter.split_text(text)
        return [chunk.strip() for chunk in chunks if chunk.strip()]
    
    def process_pdf_advanced(self, pdf_path: str) -> Tuple[List[Dict[str, Any]], Dict]:
        """Advanced PDF processing pipeline with structure analysis"""
        print("🔍 Extracting text from PDF...")
        text = self.extract_text_from_pdf(pdf_path)
        
        print("📖 Analyzing document structure...")
        structure = self.extract_document_structure(text)
        
        print("✂️  Creating advanced chunks with metadata...")
        chunks_with_metadata = self.chunk_text_advanced(text, structure)
        
        print(f"✅ Created {len(chunks_with_metadata)} chunks with metadata")
        
        # Print structure summary
        for struct_type, items in structure.items():
            if items:
                print(f"📋 Found {len(items)} {struct_type}(s)")
        
        return chunks_with_metadata, structure

    def process_pdf_section_scoped(self, pdf_path: str) -> Tuple[List[Dict[str, Any]], Dict]:
        """Section/Schedule-scoped processing pipeline.

        Produces one chunk per Section or Schedule with minimal, stable
        metadata anchoring to prevent orphaned clause fragments.
        """
        print("🔍 Extracting text from PDF...")
        text = self.extract_text_from_pdf(pdf_path)

        print("📖 Extracting structure and building section-scoped chunks...")
        structure = self.extract_document_structure(text)
        chunks = self.create_section_scoped_chunks(text)

        # Enrich chunks with section_type classification
        print("🏷️  Classifying section types for smart retrieval...")
        try:
            from .statute_parser import StatuteParser
            parser = StatuteParser()
            chunks = parser.enrich_metadata_with_types(chunks)
            print(f"✅ Enriched chunks with section_type metadata")
        except Exception as e:
            print(f"⚠️  Warning: Could not classify section types: {e}")

        print(f"✅ Created {len(chunks)} section/schedule-scoped chunks")
        return chunks, structure
    
    def process_pdf(self, pdf_path: str) -> List[str]:
        """Complete PDF processing pipeline (backward compatibility)"""
        text = self.extract_text_from_pdf(pdf_path)
        chunks = self.chunk_text(text)
        return chunks

# For backward compatibility
PDFProcessor = AdvancedPDFProcessor
