"""
Enhanced Court Document Generator for RAGBot-v2
Generates sophisticated, court-ready documents with PDF export capabilities

This module creates professional legal documents following Pakistani court format:
- Appeals with comprehensive grounds and case law citations
- Plaints/Petitions with detailed fact statements
- Written Statements with para-wise responses
- PDF generation with proper formatting and styling
- Auto-fill capabilities for standard legal phrases
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import os
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, darkblue, darkred, grey
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Frame, PageTemplate
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from .gemini_client import EnhancedGeminiClient


class NumberedCanvas(canvas.Canvas):
    """Custom Canvas for adding page numbers and headers/footers"""

    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []
        self.case_title = ""
        self.doc_type = ""

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """Add page info to each page (page x of y)"""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        """Draw page number and header/footer"""
        page_num = self._pageNumber

        # Draw header line
        self.setStrokeColor(grey)
        self.setLineWidth(0.5)
        self.line(0.75*inch, A4[1] - 0.6*inch, A4[0] - 0.75*inch, A4[1] - 0.6*inch)

        # Draw footer line
        self.line(0.75*inch, 0.7*inch, A4[0] - 0.75*inch, 0.7*inch)

        # Add page number in footer
        self.setFont('Times-Roman', 9)
        self.setFillColor(black)
        text = f"Page {page_num} of {page_count}"
        self.drawCentredString(A4[0] / 2.0, 0.5*inch, text)

        # Add case title in header (if available)
        if self.case_title:
            self.setFont('Times-Roman', 8)
            self.setFillColor(grey)
            self.drawString(0.75*inch, A4[1] - 0.5*inch, self.case_title[:80])

        # Add document type in header right
        if self.doc_type:
            self.setFont('Times-Roman', 8)
            self.setFillColor(grey)
            self.drawRightString(A4[0] - 0.75*inch, A4[1] - 0.5*inch, self.doc_type)

        # Add filing date in footer left
        filing_date = datetime.now().strftime('%d %B %Y')
        self.setFont('Times-Roman', 8)
        self.setFillColor(grey)
        self.drawString(0.75*inch, 0.5*inch, f"Filed on: {filing_date}")


class EnhancedCourtDocumentGenerator:
    """Generates sophisticated court documents with PDF export capabilities"""

    def __init__(self, gemini_client: EnhancedGeminiClient):
        """
        Initialize Enhanced Court Document Generator

        Args:
            gemini_client: Initialized Gemini client for content generation
        """
        self.gemini_client = gemini_client
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for legal documents"""
        # Court Header Style - Professional government document style
        self.styles.add(ParagraphStyle(
            name='CourtHeader',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceAfter=18,
            spaceBefore=6,
            alignment=TA_CENTER,
            textColor=black,
            fontName='Times-Bold',
            leading=20
        ))

        # Case Title Style
        self.styles.add(ParagraphStyle(
            name='CaseTitle',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=12,
            spaceBefore=6,
            alignment=TA_CENTER,
            textColor=black,
            fontName='Times-Bold',
            leading=16
        ))

        # Subject Style
        self.styles.add(ParagraphStyle(
            name='Subject',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=15,
            spaceBefore=6,
            alignment=TA_CENTER,
            textColor=black,
            fontName='Times-Bold',
            leading=14
        ))

        # Fact Paragraph Style - 1.5 line spacing for readability
        self.styles.add(ParagraphStyle(
            name='FactParagraph',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=9,
            spaceBefore=3,
            alignment=TA_JUSTIFY,
            leftIndent=0,
            rightIndent=0,
            fontName='Times-Roman',
            leading=16.5  # 1.5x line spacing
        ))

        # Ground Style - Indented for clarity
        self.styles.add(ParagraphStyle(
            name='Ground',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=9,
            spaceBefore=3,
            alignment=TA_JUSTIFY,
            leftIndent=20,
            rightIndent=0,
            fontName='Times-Roman',
            leading=16.5
        ))

        # Prayer Style
        self.styles.add(ParagraphStyle(
            name='Prayer',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=9,
            spaceBefore=3,
            alignment=TA_JUSTIFY,
            leftIndent=20,
            rightIndent=0,
            fontName='Times-Roman',
            leading=16.5
        ))

        # Verification Style
        self.styles.add(ParagraphStyle(
            name='Verification',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=9,
            spaceBefore=3,
            alignment=TA_LEFT,
            leftIndent=0,
            rightIndent=0,
            fontName='Times-Roman',
            leading=16.5
        ))

        # Section Heading Style
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            spaceBefore=15,
            alignment=TA_CENTER,
            textColor=black,
            fontName='Times-Bold',
            leading=16
        ))

    def generate_sophisticated_appeal(
        self,
        case_analysis: Dict[str, Any],
        law_retrieval: Dict[str, Any],
        case_details: Dict[str, str],
        impugned_orders: List[Dict[str, str]],
        generate_pdf: bool = True
    ) -> Dict[str, Any]:
        """
        Generate sophisticated Appeal document with PDF export

        Args:
            case_analysis: Output from CaseAgent
            law_retrieval: Output from LawAgent
            case_details: Dictionary with appellant/respondent details
            impugned_orders: List of orders being challenged
            generate_pdf: Whether to generate PDF version

        Returns:
            Dictionary with text and PDF content
        """
        # Build comprehensive appeal header
        appeal_header = self._build_sophisticated_appeal_header(case_details)

        # Generate detailed fact paragraphs
        fact_paragraphs = self._generate_sophisticated_appeal_facts(
            case_analysis, case_details, law_retrieval
        )

        # Generate comprehensive grounds of appeal
        grounds = self._generate_sophisticated_grounds_of_appeal(
            case_analysis, law_retrieval
        )

        # Generate detailed prayer section
        prayer = self._generate_sophisticated_prayer_appeal(
            case_details, impugned_orders, case_analysis
        )

        # Generate index/annexure list
        index = self._generate_document_index(case_details, impugned_orders)

        # Assemble complete appeal
        appeal_document = f"""{appeal_header}

{fact_paragraphs}

GROUNDS OF APPEAL:

{grounds}

PRAYER:

{prayer}

Appellants

Through Counsels

{case_details.get('counsel_details', '')}

{self._generate_signature_block(case_details)}
"""

        result = {
            'text': appeal_document,
            'index': index,
            'pdf_path': None
        }

        # Generate PDF if requested
        if generate_pdf:
            pdf_path = self._generate_appeal_pdf(
                appeal_document, case_details, index, impugned_orders
            )
            result['pdf_path'] = pdf_path

        return result

    def generate_sophisticated_plaint(
        self,
        narrative: str,
        case_analysis: Dict[str, Any],
        law_retrieval: Dict[str, Any],
        case_details: Dict[str, str],
        generate_pdf: bool = True
    ) -> Dict[str, Any]:
        """
        Generate sophisticated Plaint/Petition document

        Args:
            narrative: User's narrative
            case_analysis: Output from CaseAgent
            law_retrieval: Output from LawAgent
            case_details: Dictionary with plaintiff/defendant details
            generate_pdf: Whether to generate PDF version

        Returns:
            Dictionary with text and PDF content
        """
        # Build sophisticated plaint header
        plaint_header = self._build_sophisticated_plaint_header(case_details)

        # Generate comprehensive fact paragraphs
        fact_paragraphs = self._generate_sophisticated_plaint_facts(
            narrative, case_analysis, law_retrieval, case_details
        )

        # Generate detailed prayer
        prayer = self._generate_sophisticated_prayer_plaint(case_analysis, case_details)

        # Generate verification
        verification = self._build_sophisticated_verification(case_details)

        # Generate cause of action analysis
        cause_of_action = self._generate_cause_of_action_analysis(
            case_analysis, law_retrieval
        )

        # Assemble complete plaint
        plaint_document = f"""{plaint_header}

Respectfully Sheweth:-

{fact_paragraphs}

CAUSE OF ACTION:

{cause_of_action}

PRAYER:

{prayer}

PLAINTIFF

THROUGH

COUNSEL

{verification}

{self._generate_signature_block(case_details)}
"""

        result = {
            'text': plaint_document,
            'pdf_path': None
        }

        # Generate PDF if requested
        if generate_pdf:
            pdf_path = self._generate_plaint_pdf(
                plaint_document, case_details
            )
            result['pdf_path'] = pdf_path

        return result

    def generate_sophisticated_written_statement(
        self,
        petition: str,
        case_analysis: Dict[str, Any],
        law_retrieval: Dict[str, Any],
        case_details: Dict[str, str],
        generate_pdf: bool = True
    ) -> Dict[str, Any]:
        """
        Generate sophisticated Written Statement

        Args:
            petition: Opponent's petition text
            case_analysis: Output from CaseAgent
            law_retrieval: Output from LawAgent
            case_details: Dictionary with defendant details
            generate_pdf: Whether to generate PDF version

        Returns:
            Dictionary with text and PDF content
        """
        # Build sophisticated header
        ws_header = self._build_sophisticated_written_statement_header(case_details)

        # Generate comprehensive para-wise responses
        responses = self._generate_sophisticated_written_statement_responses(
            petition, case_analysis, law_retrieval
        )

        # Generate detailed prayer
        prayer = self._generate_sophisticated_prayer_written_statement(
            case_details, case_analysis
        )

        # Generate legal objections
        legal_objections = self._generate_legal_objections(case_analysis, law_retrieval)

        # Assemble complete written statement
        ws_document = f"""{ws_header}

Respectfully Sheweth:

PRELIMINARY OBJECTIONS:

{legal_objections}

ON MERITS:

{responses}

PRAYER:

{prayer}

ANSWERING DEFENDANT

THROUGH

{case_details.get('counsel_name', 'ADVOCATE')}

{self._generate_signature_block(case_details)}
"""

        result = {
            'text': ws_document,
            'pdf_path': None
        }

        # Generate PDF if requested
        if generate_pdf:
            pdf_path = self._generate_written_statement_pdf(
                ws_document, case_details
            )
            result['pdf_path'] = pdf_path

        return result

    def _build_sophisticated_appeal_header(self, case_details: Dict[str, str]) -> str:
        """Build sophisticated appeal document header with proper formatting"""
        court_name = case_details.get('court_name', 'HONORABLE DISTRICT JUDGE, LAHORE')
        appeal_no = case_details.get('appeal_no', f'/{datetime.now().year}')
        
        # Auto-generate case number if not provided
        if not case_details.get('appeal_no'):
            appeal_no = f"Appeal No. {case_details.get('case_number', '')}/{datetime.now().year}"

        appellants = case_details.get('appellants', [])
        respondents = case_details.get('respondents', [])

        # Format appellants with proper legal descriptions
        appellant_text = self._format_party_list(appellants, "Appellant")
        respondent_text = self._format_party_list(respondents, "Respondent")

        # Generate sophisticated subject line
        subject = self._generate_sophisticated_subject(case_details, "APPEAL")

        header = f"""IN THE COURT OF {court_name}

{appeal_no}

{appellant_text}

Versus

{respondent_text}

SUBJECT: {subject}

Appellants submit as follows:"""

        return header

    def _build_sophisticated_plaint_header(self, case_details: Dict[str, str]) -> str:
        """Build sophisticated plaint document header"""
        court_name = case_details.get('court_name', 'CIVIL JUDGE, LAHORE')
        suit_no = case_details.get('suit_no', f'_________/{datetime.now().year}')

        plaintiff = case_details.get('plaintiff', '')
        defendants = case_details.get('defendants', [])

        # Format parties with proper legal descriptions
        plaintiff_text = self._format_plaintiff(plaintiff)
        defendant_text = self._format_party_list(defendants, "Defendant")

        subject = self._generate_sophisticated_subject(case_details, "SUIT")

        header = f"""IN THE COURT OF {court_name}

Civil Suit No.{suit_no}

{plaintiff_text}

PLAINTIFF

Versus

{defendant_text}

DEFENDANTS

SUBJECT: {subject}"""

        return header

    def _build_sophisticated_written_statement_header(self, case_details: Dict[str, str]) -> str:
        """Build sophisticated written statement header"""
        court_name = case_details.get('court_name', 'CIVIL JUDGE, LAHORE')
        case_title = case_details.get('case_title', '')
        subject = case_details.get('subject', '')

        header = f"""IN THE COURT OF {court_name}

{case_title}

({subject})

WRITTEN STATEMENT ON BEHALF OF ANSWERING DEFENDANT"""

        return header

    def _format_party_list(self, parties: List[str], party_type: str) -> str:
        """Format party list with proper legal descriptions"""
        if not parties:
            return f"[{party_type.upper()}S TO BE SPECIFIED]"

        formatted_parties = []
        for i, party in enumerate(parties, 1):
            # Auto-enhance party descriptions
            enhanced_party = self._enhance_party_description(party, party_type)
            formatted_parties.append(f"{i}. {enhanced_party}")

        return "\n".join(formatted_parties)

    def _enhance_party_description(self, party: str, party_type: str) -> str:
        """Enhance party description with legal details"""
        # Auto-detect if it's a company, individual, or government entity
        if any(keyword in party.upper() for keyword in ['LTD', 'LIMITED', 'PVT', 'PRIVATE', 'COMPANY', 'CORP']):
            return f"{party}, a company incorporated under the Companies Act, 2017"
        elif any(keyword in party.upper() for keyword in ['GOVT', 'GOVERNMENT', 'DISTRICT', 'MUNICIPAL']):
            return f"{party}, through its authorized representative"
        else:
            return f"{party}, {party_type.lower()}"

    def _format_plaintiff(self, plaintiff: str) -> str:
        """Format plaintiff with proper legal description"""
        if not plaintiff:
            return "[PLAINTIFF TO BE SPECIFIED]"
        
        # Auto-enhance plaintiff description
        if any(keyword in plaintiff.upper() for keyword in ['LTD', 'LIMITED', 'PVT', 'PRIVATE', 'COMPANY']):
            return f"{plaintiff}, a company incorporated under the Companies Act, 2017"
        else:
            return f"{plaintiff}, {self._get_residence_description()}"

    def _get_residence_description(self) -> str:
        """Generate standard residence description"""
        return "resident of [ADDRESS TO BE SPECIFIED]"

    def _generate_sophisticated_subject(self, case_details: Dict[str, str], doc_type: str) -> str:
        """Generate sophisticated subject line with legal provisions"""
        base_subject = case_details.get('subject', f'{doc_type} FOR APPROPRIATE RELIEF')
        
        # Add relevant legal provisions based on case type
        if doc_type == "APPEAL":
            return f"{base_subject} UNDER SECTION 104 READ WITH ORDER 43 RULE 1(a) OF THE CODE OF CIVIL PROCEDURE, 1908"
        elif doc_type == "SUIT":
            return f"{base_subject} UNDER SECTION 9 OF THE CODE OF CIVIL PROCEDURE, 1908"
        else:
            return base_subject

    def _generate_sophisticated_appeal_facts(
        self,
        case_analysis: Dict[str, Any],
        case_details: Dict[str, str],
        law_retrieval: Dict[str, Any]
    ) -> str:
        """Generate sophisticated fact paragraphs for appeal using enhanced AI prompts"""

        case_summary = case_analysis.get('case_summary', {})
        issues = case_analysis.get('legal_issues', [])
        law_sections = law_retrieval.get('all_relevant_sections', [])[:10]

        # Build comprehensive law context
        law_context = "\n".join([
            f"- {s.get('citation', 'Section')}: {s.get('text', '')[:200]}..."
            for s in law_sections
        ])

        prompt = f"""You are a senior legal draftsman with 20+ years of experience preparing Appeal documents for Pakistani courts.

CASE SUMMARY:
{case_summary}

LEGAL ISSUES IDENTIFIED:
{[issue.get('description', '') for issue in issues[:8]]}

RELEVANT STATUTORY PROVISIONS:
{law_context}

CASE DETAILS:
- Court: {case_details.get('court_name', 'HONORABLE DISTRICT JUDGE, LAHORE')}
- Case Type: Appeal
- Subject Matter: {case_details.get('subject', '')}

TASK: Generate comprehensive numbered fact paragraphs for the FACTS section of an Appeal.

REQUIREMENTS:
1. Start each paragraph with "That"
2. Use sophisticated legal language with proper terminology
3. Present facts chronologically and logically
4. Include specific dates, parties, and legal proceedings
5. Reference relevant statutory provisions where applicable
6. Each paragraph should be 3-5 sentences
7. Generate 8-12 comprehensive paragraphs covering:
   - Introduction of appellants and their legal status
   - Background facts leading to the dispute
   - Lower court proceedings and timeline
   - The impugned orders and their dates
   - Legal basis for challenging the orders
   - Jurisdictional issues if any
   - Procedural irregularities
   - Substantive legal errors

FORMAT EXAMPLE:
1. That the appellants are [legal description] and are aggrieved by the impugned orders dated [DATE] passed by the learned [COURT]...
2. That the brief facts giving rise to the instant appeal are that on [DATE], the respondents [action], in contravention of [STATUTORY PROVISION]...
3. That in response to the said [matter], the appellants [action] and filed [document] before the learned court...

Generate the sophisticated numbered fact paragraphs now:"""

        try:
            response = self.gemini_client.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"[Error generating sophisticated facts: {str(e)}]"

    def _generate_sophisticated_grounds_of_appeal(
        self,
        case_analysis: Dict[str, Any],
        law_retrieval: Dict[str, Any]
    ) -> str:
        """Generate sophisticated grounds of appeal with case law citations"""

        weaknesses = case_analysis.get('weaknesses', [])
        issues = case_analysis.get('legal_issues', [])
        law_sections = law_retrieval.get('all_relevant_sections', [])[:15]

        law_text = "\n".join([
            f"- {s.get('citation', 'Section')}: {s.get('text', '')[:200]}..."
            for s in law_sections
        ])

        prompt = f"""You are a senior legal draftsman preparing comprehensive GROUNDS OF APPEAL for a Pakistani court.

IDENTIFIED LEGAL ISSUES:
{[issue.get('description', '') for issue in issues[:12]]}

WEAKNESSES IN LOWER COURT ORDER:
{[w.get('description', '') for w in weaknesses]}

RELEVANT STATUTORY PROVISIONS:
{law_text}

TASK: Generate lettered grounds of appeal (A, B, C, etc.) with sophisticated legal reasoning.

REQUIREMENTS:
1. Start each ground with a letter (A, B, C...)
2. Begin each ground with "That"
3. Use sophisticated legal language and terminology
4. Cite specific statutory provisions with proper references
5. Include relevant case law precedents where applicable
6. Reference constitutional provisions if relevant
7. Each ground should be 3-6 sentences
8. Generate 10-15 comprehensive grounds covering:
   - Jurisdictional errors
   - Procedural irregularities
   - Misreading of facts
   - Misapplication of law
   - Violation of natural justice
   - Constitutional violations
   - Statutory interpretation errors
   - Evidence evaluation errors

FORMAT EXAMPLE:
A. That the impugned order is based on misreading and non-reading of the statutory provisions of [ACT], particularly Section [X], which clearly provides that [provision], and the learned court failed to appreciate that [legal reasoning]...

B. That the learned court has violated the fundamental principles of natural justice by [specific violation], which is contrary to the established principles laid down in [CASE LAW] and Article [X] of the Constitution of Pakistan...

Generate the sophisticated lettered grounds now:"""

        try:
            response = self.gemini_client.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"[Error generating sophisticated grounds: {str(e)}]"

    def _generate_sophisticated_plaint_facts(
        self,
        narrative: str,
        case_analysis: Dict[str, Any],
        law_retrieval: Dict[str, Any],
        case_details: Dict[str, str]
    ) -> str:
        """Generate sophisticated fact paragraphs for plaint"""

        law_sections = law_retrieval.get('all_relevant_sections', [])[:10]
        law_text = "\n".join([
            f"- {s.get('citation', '')}"
            for s in law_sections
        ])

        prompt = f"""You are a senior legal draftsman preparing a comprehensive Plaint (Petition) for a Pakistani court.

PLAINTIFF'S NARRATIVE:
{narrative}

RELEVANT STATUTORY PROVISIONS:
{law_text}

CASE ANALYSIS:
{case_analysis.get('case_summary', {})}

TASK: Generate sophisticated numbered fact paragraphs for the FACTS section of a Plaint.

REQUIREMENTS:
1. Start each paragraph with "That"
2. Use sophisticated legal language ("Respectfully submit", "It is submitted that")
3. Present facts chronologically and logically
4. Include specific dates, parties, events, and amounts
5. Reference relevant legal provisions with proper citations
6. Explain cause of action clearly and comprehensively
7. Each paragraph should be 3-5 sentences
8. Generate 8-12 comprehensive paragraphs

MUST INCLUDE:
- Introduction of plaintiff with legal status
- Background facts leading to the dispute
- The alleged wrong/grievance with specific details
- Actions taken by plaintiff (notices, correspondence)
- Cause of action with legal basis
- Jurisdiction of court with statutory backing
- Valuation for court fee purposes
- Limitation period considerations
- Legal basis for relief sought

FORMAT EXAMPLE:
1. That the plaintiff is [legal description] and is engaged in [business/activity] as more particularly described in the cause title...
2. That the brief facts giving rise to the instant suit are that on [date], the defendants [specific action], in contravention of [statutory provision]...
3. That the plaintiff, being aggrieved by the said [action], served a legal notice dated [date] upon the defendants calling upon them to [demand]...

Generate the sophisticated numbered fact paragraphs now:"""

        try:
            response = self.gemini_client.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"[Error generating sophisticated plaint facts: {str(e)}]"

    def _generate_sophisticated_written_statement_responses(
        self,
        petition: str,
        case_analysis: Dict[str, Any],
        law_retrieval: Dict[str, Any]
    ) -> str:
        """Generate sophisticated para-wise responses for written statement"""

        strengths = case_analysis.get('strengths', [])
        law_sections = law_retrieval.get('all_relevant_sections', [])[:10]

        law_text = "\n".join([
            f"- {s.get('citation', '')}: {s.get('text', '')[:150]}..."
            for s in law_sections
        ])

        prompt = f"""You are a senior legal draftsman preparing a comprehensive Written Statement (response) for a Pakistani court.

OPPONENT'S PETITION/PLAINT:
{petition[:2000]}...

DEFENDANT'S STRENGTHS:
{[s.get('description', '') for s in strengths]}

RELEVANT STATUTORY PROVISIONS:
{law_text}

TASK: Generate sophisticated numbered paragraph-wise responses to the opponent's plaint.

REQUIREMENTS:
1. Number each paragraph (1, 2, 3...)
2. Start with "That the contents of para No.X..."
3. Respond with: "are admitted/denied/partly admitted/irrelevant/not admitted"
4. Provide detailed legal reasoning for denials with statutory backing
5. Cite relevant statutory provisions and case law
6. Use sophisticated legal language
7. Include "ON MERITS" defenses with legal basis
8. Generate 10-15 comprehensive responses

FORMAT EXAMPLE:
1. That the contents of para No.1 are admitted to the extent of [specific part] and denied to the extent of [specific part]. It is respectfully submitted that [legal reasoning with statutory backing]...
2. That the contents of para No.2 are denied. It is respectfully submitted that [detailed legal reasoning] and reference is made to [statutory provision] which provides that [provision]...
3. That the contents of para No.3 are irrelevant to the answering defendant and do not require any response...

Generate the sophisticated numbered responses now:"""

        try:
            response = self.gemini_client.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"[Error generating sophisticated responses: {str(e)}]"

    def _generate_sophisticated_prayer_appeal(
        self,
        case_details: Dict[str, str],
        impugned_orders: List[Dict[str, str]],
        case_analysis: Dict[str, Any]
    ) -> str:
        """Generate sophisticated prayer section for appeal"""

        orders_text = ", ".join([
            f"dated {order.get('date', '')}"
            for order in impugned_orders
        ])

        # Generate comprehensive prayer based on case analysis
        recommendations = case_analysis.get('recommendations', [])
        specific_relief = []
        
        for rec in recommendations[:3]:
            if rec.get('action'):
                specific_relief.append(rec['action'])

        prayer = f"""In view of the above facts, circumstances, and legal position, it is most respectfully prayed that this Honorable Court may graciously be pleased to:

a) Set aside the impugned orders {orders_text} passed by the learned lower court as being illegal, without jurisdiction, and contrary to law;

b) Allow the present appeal and pass such orders as this Honorable Court deems fit and proper in the circumstances of the case;

c) Award costs of the appeal in favor of the appellants;

d) Grant such other relief as this Honorable Court deems fit and proper in the interest of justice."""

        if specific_relief:
            prayer += f"\n\ne) {specific_relief[0]};"

        return prayer

    def _generate_sophisticated_prayer_plaint(
        self,
        case_analysis: Dict[str, Any],
        case_details: Dict[str, str]
    ) -> str:
        """Generate sophisticated prayer section for plaint"""

        # Extract demands from case analysis
        recommendations = case_analysis.get('recommendations', [])
        specific_demands = []
        
        for rec in recommendations[:5]:
            if rec.get('action'):
                specific_demands.append(rec['action'])

        prayer = """Under the circumstances, it is therefore most respectfully prayed that this Honorable Court may graciously be pleased to:

a) Pass a decree for [SPECIFIC RELIEF] in favor of the plaintiff and against the defendants;

b) Award damages in the sum of [AMOUNT] for the wrongful acts of the defendants;

c) Grant permanent injunction restraining the defendants from [SPECIFIC ACTS];

d) Award costs of the suit in favor of the plaintiff;

e) Grant such other relief as this Honorable Court deems fit and proper in the greater interest of justice."""

        if specific_demands:
            prayer = prayer.replace("[SPECIFIC RELIEF]", specific_demands[0])
            if len(specific_demands) > 1:
                prayer += f"\n\nf) {specific_demands[1]};"

        return prayer

    def _generate_sophisticated_prayer_written_statement(
        self,
        case_details: Dict[str, str],
        case_analysis: Dict[str, Any]
    ) -> str:
        """Generate sophisticated prayer section for written statement"""

        prayer = """Under the circumstances, it is therefore most respectfully prayed that this Honorable Court may graciously be pleased to:

a) Dismiss the suit under reply with costs in favor of the answering defendant;

b) Hold that the plaintiff has no cause of action against the answering defendant;

c) Declare that the answering defendant is not liable for any of the claims made by the plaintiff;

d) Grant such other relief as this Honorable Court deems fit and proper in the circumstances of the case."""

        return prayer

    def _build_sophisticated_verification(self, case_details: Dict[str, str]) -> str:
        """Build sophisticated verification section"""
        place = case_details.get('place', 'Lahore')
        date = datetime.now().strftime('%d day of %B %Y')

        verification = f"""VERIFICATION:

Verified on oath at {place} on this {date} that the contents of the above paragraphs are correct to the best of my knowledge, information, and belief.

PLAINTIFF

[Signature]"""

        return verification

    def _generate_cause_of_action_analysis(
        self,
        case_analysis: Dict[str, Any],
        law_retrieval: Dict[str, Any]
    ) -> str:
        """Generate cause of action analysis"""

        prompt = f"""You are a senior legal draftsman analyzing the cause of action for a civil suit.

CASE ANALYSIS:
{case_analysis.get('case_summary', {})}

LEGAL ISSUES:
{[issue.get('description', '') for issue in case_analysis.get('legal_issues', [])[:5]]}

TASK: Generate a comprehensive cause of action analysis.

REQUIREMENTS:
1. Explain when the cause of action first arose
2. Identify the legal basis for the claim
3. Reference relevant statutory provisions
4. Explain why the court has jurisdiction
5. Address limitation period considerations
6. Use 3-5 paragraphs with sophisticated legal language

Generate the cause of action analysis now:"""

        try:
            response = self.gemini_client.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"[Error generating cause of action analysis: {str(e)}]"

    def _generate_legal_objections(
        self,
        case_analysis: Dict[str, Any],
        law_retrieval: Dict[str, Any]
    ) -> str:
        """Generate legal objections section"""

        prompt = f"""You are a senior legal draftsman preparing preliminary legal objections for a written statement.

CASE ANALYSIS:
{case_analysis.get('case_summary', {})}

LEGAL ISSUES:
{[issue.get('description', '') for issue in case_analysis.get('legal_issues', [])[:5]]}

TASK: Generate comprehensive preliminary legal objections.

REQUIREMENTS:
1. Number each objection (1, 2, 3...)
2. Start with "That the suit is not maintainable"
3. Include jurisdictional objections
4. Reference relevant statutory provisions
5. Use sophisticated legal language
6. Generate 5-8 objections

FORMAT EXAMPLE:
1. That the suit is not maintainable as this Honorable Court has no jurisdiction to entertain the same in view of [legal provision]...
2. That the suit is barred by limitation as the cause of action, if any, arose on [date] and the suit has been filed beyond the prescribed period...

Generate the legal objections now:"""

        try:
            response = self.gemini_client.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"[Error generating legal objections: {str(e)}]"

    def _generate_document_index(
        self,
        case_details: Dict[str, str],
        impugned_orders: List[Dict[str, str]]
    ) -> str:
        """Generate document index/annexure list"""

        index_items = [
            "1. Appeal",
            "2. Power of Attorney / Authority Letter",
            "3. Copies of plaint & written statements respectively",
            "4. Copy of impugned order dated [DATE]",
        ]

        if len(impugned_orders) > 1:
            for i, order in enumerate(impugned_orders[1:], 5):
                index_items.append(f"{i}. Copy of impugned order dated {order.get('date', '[DATE]')}")

        index_items.extend([
            f"{len(index_items) + 1}. Stay Application",
            f"{len(index_items) + 2}. Affidavit",
            f"{len(index_items) + 3}. Legal Notices",
            f"{len(index_items) + 4}. Supporting Documents"
        ])

        index = "INDEX\n\nSr.No:\tDocuments\tAnnexures\tPage No:\n"
        for item in index_items:
            index += f"{item}\t\t\t\n"

        return index

    def _generate_signature_block(self, case_details: Dict[str, str]) -> str:
        """Generate signature block"""
        counsel_name = case_details.get('counsel_name', '[COUNSEL NAME]')
        bar_number = case_details.get('bar_number', '[BAR NUMBER]')
        
        return f"""
{counsel_name}
Advocate High Court
Bar No. {bar_number}
[ADDRESS]"""

    def _generate_appeal_pdf(
        self,
        document_text: str,
        case_details: Dict[str, str],
        index: str,
        impugned_orders: List[Dict[str, str]]
    ) -> str:
        """Generate PDF for appeal document"""
        filename = f"Appeal_{case_details.get('case_number', 'Unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join("generated_documents", filename)

        # Create directory if it doesn't exist
        os.makedirs("generated_documents", exist_ok=True)

        # Create document with professional margins (1.5" left, 1" other sides)
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            leftMargin=1.5*inch,
            rightMargin=1.0*inch,
            topMargin=1.0*inch,
            bottomMargin=1.0*inch
        )
        story = []

        # Add index page
        story.append(Paragraph("INDEX", self.styles['CourtHeader']))
        story.append(Spacer(1, 12))

        # Parse and add index items
        index_lines = index.split('\n')[2:]  # Skip header lines
        for line in index_lines:
            if line.strip():
                story.append(Paragraph(line, self.styles['Normal']))

        story.append(PageBreak())

        # Add main document
        self._add_document_to_story(document_text, story)

        # Build with custom canvas for page numbers
        def on_page(canvas_obj, doc_obj):
            canvas_obj.case_title = case_details.get('case_title', '')[:60]
            canvas_obj.doc_type = "APPEAL"

        doc.build(story, onFirstPage=on_page, onLaterPages=on_page, canvasmaker=NumberedCanvas)
        return filepath

    def _generate_plaint_pdf(
        self,
        document_text: str,
        case_details: Dict[str, str]
    ) -> str:
        """Generate PDF for plaint document"""
        filename = f"Plaint_{case_details.get('case_number', 'Unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join("generated_documents", filename)

        os.makedirs("generated_documents", exist_ok=True)

        # Create document with professional margins
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            leftMargin=1.5*inch,
            rightMargin=1.0*inch,
            topMargin=1.0*inch,
            bottomMargin=1.0*inch
        )
        story = []

        self._add_document_to_story(document_text, story)

        # Build with custom canvas for page numbers
        def on_page(canvas_obj, doc_obj):
            canvas_obj.case_title = case_details.get('case_title', '')[:60]
            canvas_obj.doc_type = "PLAINT/PETITION"

        doc.build(story, onFirstPage=on_page, onLaterPages=on_page, canvasmaker=NumberedCanvas)
        return filepath

    def _generate_written_statement_pdf(
        self,
        document_text: str,
        case_details: Dict[str, str]
    ) -> str:
        """Generate PDF for written statement document"""
        filename = f"WrittenStatement_{case_details.get('case_number', 'Unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join("generated_documents", filename)

        os.makedirs("generated_documents", exist_ok=True)

        # Create document with professional margins
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            leftMargin=1.5*inch,
            rightMargin=1.0*inch,
            topMargin=1.0*inch,
            bottomMargin=1.0*inch
        )
        story = []

        self._add_document_to_story(document_text, story)

        # Build with custom canvas for page numbers
        def on_page(canvas_obj, doc_obj):
            canvas_obj.case_title = case_details.get('case_title', '')[:60]
            canvas_obj.doc_type = "WRITTEN STATEMENT"

        doc.build(story, onFirstPage=on_page, onLaterPages=on_page, canvasmaker=NumberedCanvas)
        return filepath

    def _clean_markdown(self, text: str) -> str:
        """
        Clean markdown formatting from text for clean PDF rendering

        Removes:
        - Bold/italic markers (**, __, *, _)
        - Headers (###, ##, #)
        - Markdown links ([text](url))
        - Code blocks (```)
        - Other markdown artifacts

        Returns clean, professional text suitable for legal PDFs
        """
        import re

        # Remove code blocks
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`[^`]+`', '', text)

        # Remove markdown headers (### Header -> Header)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

        # Remove bold/italic (**text** or __text__ -> text)
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)

        # Remove single emphasis (*text* or _text_ -> text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'\b_([^_]+)_\b', r'\1', text)

        # Remove markdown links ([text](url) -> text)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

        # Remove horizontal rules (---, ***, ___)
        text = re.sub(r'^[\*\-_]{3,}\s*$', '', text, flags=re.MULTILINE)

        # Remove blockquotes (> text -> text)
        text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)

        # Remove HTML tags if any
        text = re.sub(r'<[^>]+>', '', text)

        # Clean up multiple spaces
        text = re.sub(r'  +', ' ', text)

        return text.strip()

    def _add_document_to_story(self, document_text: str, story: List):
        """Add document text to PDF story with proper formatting"""
        # Clean markdown from the entire document first
        document_text = self._clean_markdown(document_text)

        lines = document_text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 6))
                continue

            # Determine paragraph style based on content
            if line.startswith('IN THE COURT OF'):
                story.append(Paragraph(line, self.styles['CourtHeader']))
            elif line.startswith('SUBJECT:'):
                story.append(Paragraph(line, self.styles['Subject']))
            elif line.startswith(('GROUNDS OF APPEAL:', 'PRAYER:', 'CAUSE OF ACTION:',
                                  'PRELIMINARY OBJECTIONS:', 'ON MERITS:', 'VERIFICATION:',
                                  'Respectfully Sheweth')):
                story.append(Spacer(1, 12))
                story.append(Paragraph(line, self.styles['SectionHeading']))
                story.append(Spacer(1, 6))
            elif line.startswith(('A.', 'B.', 'C.', 'D.', 'E.', 'F.', 'G.', 'H.', 'I.', 'J.',
                                  'K.', 'L.', 'M.', 'N.', 'O.')):
                story.append(Paragraph(line, self.styles['Ground']))
            elif line.startswith(('a)', 'b)', 'c)', 'd)', 'e)', 'f)', 'g)', 'h)', 'i)', 'j)')):
                story.append(Paragraph(line, self.styles['Prayer']))
            elif line.startswith(('Appellants', 'PLAINTIFF', 'ANSWERING DEFENDANT', 'Through Counsels',
                                  'THROUGH', 'COUNSEL')):
                story.append(Spacer(1, 12))
                story.append(Paragraph(line, self.styles['Heading3']))
            elif line.startswith(('That', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.',
                                  '10.', '11.', '12.', '13.', '14.', '15.')):
                story.append(Paragraph(line, self.styles['FactParagraph']))
            else:
                story.append(Paragraph(line, self.styles['Normal']))


def generate_enhanced_court_documents(
    narrative: str,
    petition: str,
    case_analysis: Dict[str, Any],
    law_retrieval: Dict[str, Any],
    gemini_client: EnhancedGeminiClient,
    case_details: Dict[str, str],
    generate_pdfs: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to generate all enhanced court documents

    Args:
        narrative: User's narrative
        petition: Opponent's petition
        case_analysis: Output from CaseAgent
        law_retrieval: Output from LawAgent
        gemini_client: Initialized Gemini client
        case_details: Case-specific details
        generate_pdfs: Whether to generate PDF versions

    Returns:
        Dictionary with generated documents and PDF paths
    """
    generator = EnhancedCourtDocumentGenerator(gemini_client)

    documents = {}

    # Generate plaint from narrative
    documents['plaint'] = generator.generate_sophisticated_plaint(
        narrative, case_analysis, law_retrieval, case_details, generate_pdfs
    )

    # Generate written statement (response to petition)
    documents['written_statement'] = generator.generate_sophisticated_written_statement(
        petition, case_analysis, law_retrieval, case_details, generate_pdfs
    )

    # Generate appeal (if applicable)
    if case_details.get('generate_appeal'):
        documents['appeal'] = generator.generate_sophisticated_appeal(
            case_analysis, law_retrieval, case_details,
            case_details.get('impugned_orders', []), generate_pdfs
        )

    return documents

