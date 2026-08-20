"""
Court Document Generator for RAGBot-v2
Generates formal court-ready documents following Pakistani legal format

This module transforms legal analysis into properly formatted court documents:
- Appeals
- Plaints/Petitions
- Written Statements
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from .gemini_client import EnhancedGeminiClient


class CourtDocumentGenerator:
    """Generates formal court documents following Pakistani legal templates"""

    def __init__(self, gemini_client: EnhancedGeminiClient):
        """
        Initialize Court Document Generator

        Args:
            gemini_client: Initialized Gemini client for content generation
        """
        self.gemini_client = gemini_client

    def generate_appeal(
        self,
        case_analysis: Dict[str, Any],
        law_retrieval: Dict[str, Any],
        case_details: Dict[str, str],
        impugned_orders: List[Dict[str, str]]
    ) -> str:
        """
        Generate formal Appeal document

        Args:
            case_analysis: Output from CaseAgent
            law_retrieval: Output from LawAgent
            case_details: Dictionary with appellant/respondent details
            impugned_orders: List of orders being challenged

        Returns:
            Formatted appeal document as string
        """
        # Build appeal header
        appeal_header = self._build_appeal_header(case_details)

        # Generate fact paragraphs using Gemini
        fact_paragraphs = self._generate_appeal_facts(
            case_analysis, case_details
        )

        # Generate grounds of appeal
        grounds = self._generate_grounds_of_appeal(
            case_analysis, law_retrieval
        )

        # Build prayer section
        prayer = self._generate_prayer_appeal(case_details, impugned_orders)

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
"""

        return appeal_document

    def generate_plaint(
        self,
        narrative: str,
        case_analysis: Dict[str, Any],
        law_retrieval: Dict[str, Any],
        case_details: Dict[str, str]
    ) -> str:
        """
        Generate formal Plaint/Petition document

        Args:
            narrative: User's narrative
            case_analysis: Output from CaseAgent
            law_retrieval: Output from LawAgent
            case_details: Dictionary with plaintiff/defendant details

        Returns:
            Formatted plaint document as string
        """
        # Build plaint header
        plaint_header = self._build_plaint_header(case_details)

        # Generate fact paragraphs from narrative
        fact_paragraphs = self._generate_plaint_facts(
            narrative, case_analysis, law_retrieval
        )

        # Generate prayer based on demands
        prayer = self._generate_prayer_plaint(case_analysis)

        # Build verification section
        verification = self._build_verification(case_details)

        # Assemble complete plaint
        plaint_document = f"""{plaint_header}

Respectfully Sheweth:-

{fact_paragraphs}

PRAYER:

{prayer}

PLAINTIFF

THROUGH

COUNSEL

{verification}
"""

        return plaint_document

    def generate_written_statement(
        self,
        petition: str,
        case_analysis: Dict[str, Any],
        law_retrieval: Dict[str, Any],
        case_details: Dict[str, str]
    ) -> str:
        """
        Generate formal Written Statement (response to petition)

        Args:
            petition: Opponent's petition text
            case_analysis: Output from CaseAgent
            law_retrieval: Output from LawAgent
            case_details: Dictionary with defendant details

        Returns:
            Formatted written statement as string
        """
        # Build header
        ws_header = self._build_written_statement_header(case_details)

        # Generate para-wise response
        responses = self._generate_written_statement_responses(
            petition, case_analysis, law_retrieval
        )

        # Generate prayer
        prayer = self._generate_prayer_written_statement(case_details)

        # Assemble complete written statement
        ws_document = f"""{ws_header}

Respectfully Sheweth:

ON MERITS:

{responses}

PRAYER:

{prayer}

ANSWERING DEFENDANT

THROUGH

{case_details.get('counsel_name', 'ADVOCATE')}
"""

        return ws_document

    def _build_appeal_header(self, case_details: Dict[str, str]) -> str:
        """Build appeal document header"""
        court_name = case_details.get('court_name', 'HONORABLE DISTRICT JUDGE, LAHORE')
        appeal_no = case_details.get('appeal_no', f'/{datetime.now().year}')

        appellants = case_details.get('appellants', [])
        respondents = case_details.get('respondents', [])

        appellant_text = "\n".join([f"{i+1}. {app}" for i, app in enumerate(appellants)])
        respondent_text = "\n".join([f"{i+1}. {resp}" for i, resp in enumerate(respondents)])

        subject = case_details.get('subject', 'APPEAL UNDER APPLICABLE PROVISIONS OF LAW')

        header = f"""IN THE COURT OF {court_name}

Appeal No: {appeal_no}

{appellant_text}
Appellants....

Versus

{respondent_text}
Respondents.....

SUBJECT: {subject}

Appellants submit as follows:"""

        return header

    def _build_plaint_header(self, case_details: Dict[str, str]) -> str:
        """Build plaint document header"""
        court_name = case_details.get('court_name', 'CIVIL JUDGE, LAHORE')
        suit_no = case_details.get('suit_no', f'_________/{datetime.now().year}')

        plaintiff = case_details.get('plaintiff', '')
        defendants = case_details.get('defendants', [])

        defendant_text = "\n".join([f"{i+1}. {def_}" for i, def_ in enumerate(defendants)])

        subject = case_details.get('subject', 'SUIT FOR APPROPRIATE RELIEF')

        header = f"""IN THE COURT OF {court_name}

Civil Suit No.{suit_no}

{plaintiff}

PLAINTIFF

Versus

{defendant_text}

DEFENDANTS

SUBECT: {subject}"""

        return header

    def _build_written_statement_header(self, case_details: Dict[str, str]) -> str:
        """Build written statement header"""
        court_name = case_details.get('court_name', 'CIVIL JUDGE, LAHORE')
        case_title = case_details.get('case_title', '')
        subject = case_details.get('subject', '')

        header = f"""IN THE COURT OF {court_name}

{case_title}

({subject})

WRITTEN STATEMENT ON BEHALF OF ANSWERING DEFENDANT"""

        return header

    def _build_verification(self, case_details: Dict[str, str]) -> str:
        """Build verification section"""
        place = case_details.get('place', 'Lahore')
        date = datetime.now().strftime('%d day of %B %Y')

        verification = f"""VERIFICATION:

Verified on oath at {place} on this {date} that the contents are correct to the best of my knowledge.

PLAINTIFF"""

        return verification

    def _generate_appeal_facts(
        self,
        case_analysis: Dict[str, Any],
        case_details: Dict[str, str]
    ) -> str:
        """Generate fact paragraphs for appeal using Gemini"""

        case_summary = case_analysis.get('case_summary', {})
        issues = case_analysis.get('legal_issues', [])

        prompt = f"""You are a senior legal draftsman preparing an Appeal document for a Pakistani court.

CASE SUMMARY:
{case_summary}

LEGAL ISSUES:
{[issue.get('description', '') for issue in issues[:5]]}

TASK: Generate numbered fact paragraphs (starting with "That") for the FACTS section of an Appeal.

REQUIREMENTS:
1. Start each paragraph with "That"
2. Use formal legal language
3. Present facts chronologically
4. Be specific with dates, parties, and events
5. Each paragraph should be 2-4 sentences
6. Generate 5-8 paragraphs covering:
   - Introduction and parties
   - Background facts
   - Lower court proceedings
   - The impugned orders
   - Reasons for appeal

FORMAT EXAMPLE:
1. That the appellants are [description]...
2. That the brief facts giving rise to the instant appeal are that...
3. That in response to the said [matter], the appellants...

Generate the numbered fact paragraphs now:"""

        try:
            response = self.gemini_client.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"[Error generating facts: {str(e)}]"

    def _generate_grounds_of_appeal(
        self,
        case_analysis: Dict[str, Any],
        law_retrieval: Dict[str, Any]
    ) -> str:
        """Generate lettered grounds of appeal using Gemini"""

        weaknesses = case_analysis.get('weaknesses', [])
        issues = case_analysis.get('legal_issues', [])
        law_sections = law_retrieval.get('all_relevant_sections', [])[:10]

        law_text = "\n".join([
            f"- {s.get('citation', 'Section')}: {s.get('text', '')[:200]}..."
            for s in law_sections
        ])

        prompt = f"""You are a senior legal draftsman preparing GROUNDS OF APPEAL for a Pakistani court.

IDENTIFIED ISSUES:
{[issue.get('description', '') for issue in issues[:10]]}

WEAKNESSES IN LOWER COURT ORDER:
{[w.get('description', '') for w in weaknesses]}

RELEVANT STATUTORY PROVISIONS:
{law_text}

TASK: Generate lettered grounds of appeal (A, B, C, etc.)

REQUIREMENTS:
1. Start each ground with a letter (A, B, C...)
2. Begin each ground with "That"
3. Use formal legal language
4. Cite specific statutory provisions where applicable
5. Reference legal precedents if relevant
6. Each ground should be 2-5 sentences
7. Generate 8-12 comprehensive grounds

FORMAT EXAMPLE:
A. That the impugned order is based on misreading and non-reading of the facts...
B. That the learned court failed to appreciate that [specific legal point]...
C. That the order violates Section X of [Act], which provides that...

Generate the lettered grounds now:"""

        try:
            response = self.gemini_client.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"[Error generating grounds: {str(e)}]"

    def _generate_plaint_facts(
        self,
        narrative: str,
        case_analysis: Dict[str, Any],
        law_retrieval: Dict[str, Any]
    ) -> str:
        """Generate fact paragraphs for plaint using Gemini"""

        law_sections = law_retrieval.get('all_relevant_sections', [])[:8]
        law_text = "\n".join([
            f"- {s.get('citation', '')}"
            for s in law_sections
        ])

        prompt = f"""You are a senior legal draftsman preparing a Plaint (Petition) for a Pakistani court.

PLAINTIFF'S NARRATIVE:
{narrative}

RELEVANT STATUTORY PROVISIONS:
{law_text}

TASK: Generate numbered fact paragraphs for the FACTS section of a Plaint.

REQUIREMENTS:
1. Start each paragraph with "That"
2. Use formal legal language ("Respectfully submit", "It is submitted that")
3. Present facts chronologically
4. Include specific dates, parties, events
5. Reference relevant legal provisions
6. Explain cause of action clearly
7. Each paragraph should be 2-4 sentences
8. Generate 6-10 paragraphs

MUST INCLUDE:
- Introduction of plaintiff
- Background facts
- The alleged wrong/grievance
- Actions taken by plaintiff
- Cause of action
- Jurisdiction of court
- Valuation for court fee

FORMAT EXAMPLE:
1. That the plaintiff is a resident of [address] and is engaged in [business/activity]...
2. That the brief facts are that on [date], the defendant [action]...
3. That the plaintiff approached the defendant on [date] but...

Generate the numbered fact paragraphs now:"""

        try:
            response = self.gemini_client.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"[Error generating plaint facts: {str(e)}]"

    def _generate_written_statement_responses(
        self,
        petition: str,
        case_analysis: Dict[str, Any],
        law_retrieval: Dict[str, Any]
    ) -> str:
        """Generate para-wise responses for written statement"""

        strengths = case_analysis.get('strengths', [])
        law_sections = law_retrieval.get('all_relevant_sections', [])[:8]

        law_text = "\n".join([
            f"- {s.get('citation', '')}: {s.get('text', '')[:150]}..."
            for s in law_sections
        ])

        prompt = f"""You are a senior legal draftsman preparing a Written Statement (response) for a Pakistani court.

OPPONENT'S PETITION/PLAINT:
{petition[:1500]}...

DEFENDANT'S STRENGTHS:
{[s.get('description', '') for s in strengths]}

RELEVANT STATUTORY PROVISIONS:
{law_text}

TASK: Generate numbered paragraph-wise responses to the opponent's plaint.

REQUIREMENTS:
1. Number each paragraph (1, 2, 3...)
2. Start with "That the contents of para No.X..."
3. Respond with: "are admitted/denied/partly admitted/irrelevant"
4. Provide detailed legal reasoning for denials
5. Cite statutory provisions where applicable
6. Use formal legal language
7. Include "ON MERITS" defenses
8. Generate 8-12 responses

FORMAT EXAMPLE:
1. That the contents of para No.1 are admitted to the extent of [specific part] and denied to the extent of [specific part]. It is submitted that...
2. That the contents of para No.2 are denied. It is respectfully submitted that [legal reasoning with statutory backing]...
3. That the contents of para No.3 are irrelevant to the answering defendant.

Generate the numbered responses now:"""

        try:
            response = self.gemini_client.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"[Error generating responses: {str(e)}]"

    def _generate_prayer_appeal(
        self,
        case_details: Dict[str, str],
        impugned_orders: List[Dict[str, str]]
    ) -> str:
        """Generate prayer section for appeal"""

        orders_text = ", ".join([
            f"dated {order.get('date', '')}"
            for order in impugned_orders
        ])

        prayer = f"""In view of the above, it is most respectfully prayed that this Honorable Court may graciously be pleased to set aside the impugned orders {orders_text} passed by the learned lower court.

It is further prayed that this Honorable Court may grant such other relief as it deems fit and proper in the interest of justice."""

        return prayer

    def _generate_prayer_plaint(self, case_analysis: Dict[str, Any]) -> str:
        """Generate prayer section for plaint"""

        # Extract demands from case analysis
        demands = []
        if case_analysis.get('recommendations'):
            for rec in case_analysis['recommendations'][:3]:
                demands.append(rec.get('action', ''))

        prayer = """a) Under the circumstances it is therefore, most respectfully prayed that appropriate relief as sought may kindly be granted in favour of the plaintiff and against the defendants.
b) Any other relief, which this court deems fit and proper in the greater interest of justice, may also be awarded."""

        return prayer

    def _generate_prayer_written_statement(self, case_details: Dict[str, str]) -> str:
        """Generate prayer section for written statement"""

        prayer = """a) Under the circumstances, it is therefore most respectfully prayed that the suit under reply may kindly be dismissed with costs.
b) Any other relief, which this Hon'ble Court deems fit and proper may also be awarded."""

        return prayer


def generate_court_documents(
    narrative: str,
    petition: str,
    case_analysis: Dict[str, Any],
    law_retrieval: Dict[str, Any],
    gemini_client: EnhancedGeminiClient,
    case_details: Dict[str, str]
) -> Dict[str, str]:
    """
    Convenience function to generate all court documents

    Args:
        narrative: User's narrative
        petition: Opponent's petition
        case_analysis: Output from CaseAgent
        law_retrieval: Output from LawAgent
        gemini_client: Initialized Gemini client
        case_details: Case-specific details

    Returns:
        Dictionary with generated documents
    """
    generator = CourtDocumentGenerator(gemini_client)

    documents = {}

    # Generate plaint from narrative
    documents['plaint'] = generator.generate_plaint(
        narrative, case_analysis, law_retrieval, case_details
    )

    # Generate written statement (response to petition)
    documents['written_statement'] = generator.generate_written_statement(
        petition, case_analysis, law_retrieval, case_details
    )

    # Generate appeal (if applicable)
    if case_details.get('generate_appeal'):
        documents['appeal'] = generator.generate_appeal(
            case_analysis, law_retrieval, case_details,
            case_details.get('impugned_orders', [])
        )

    return documents
