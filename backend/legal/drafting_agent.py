"""
Drafting Agent for RAGBot-v2: Legal Commentary Generation

This agent generates structured legal commentary including petition critique,
counter-arguments, and recommendations with statutory backing.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

# Import Gemini client for advanced generation
from .gemini_client import EnhancedGeminiClient


class DraftingAgent:
    """
    Drafting Agent: Generates formal legal commentary and analysis
    """

    def __init__(self, gemini_client: EnhancedGeminiClient):
        """
        Initialize Drafting Agent

        Args:
            gemini_client: Initialized EnhancedGeminiClient instance
        """
        self.gemini_client = gemini_client

        # Commentary templates
        self.templates = {
            'petition_critique': """You are a distinguished senior counsel and legal scholar specializing in the Khyber Pakhtunkhwa Local Government Act, 2013, with extensive experience in statutory interpretation and administrative law litigation.

═══════════════════════════════════════════════════════════════
DIRECTIVE: COMPREHENSIVE PETITION ANALYSIS WITH STATUTORY PRECISION
═══════════════════════════════════════════════════════════════

OPPONENT'S PETITION SUMMARY:
{petition_summary}

RELEVANT STATUTORY PROVISIONS FROM THE KPK LOCAL GOVERNMENT ACT, 2013:
{law_sections}

MANDATORY REQUIREMENTS FOR YOUR ANALYSIS:

I. STRUCTURAL FORMAT
   - Use formal legal headings with clear hierarchy
   - Employ judicial language and terminology
   - Each point MUST cite specific Section/Schedule numbers
   - Include subsections, clauses, and provisos where applicable

II. REQUIRED COMPONENTS (Each with Explicit Statutory References):

   A. STRENGTHS OF THE OPPONENT'S PETITION (2-4 points)
      - Identify legally sound arguments
      - Cite the EXACT Section/Schedule that supports each strength
      - Quote relevant statutory language verbatim where applicable
      - Example: "Under Section 55(1)(c) of the Act, which provides that..."

   B. WEAKNESSES AND LEGAL DEFICIENCIES (4-7 points)
      - Identify gaps in statutory compliance
      - MANDATORY: Cite specific Section/Schedule for each weakness
      - Highlight omissions in statutory requirements
      - Reference procedural irregularities with exact provisions
      - Example: "The petition fails to address Section 66(2) which mandates..."

   C. PROCEDURAL DEFECTS (If Any)
      - Cite EXACT Section numbers for procedural requirements
      - Identify non-compliance with statutory timelines
      - Reference Schedule provisions if applicable
      - Use formal legal terminology (e.g., "ultra vires", "non-compliance with mandatory provisions")

   D. FACTUAL AND LEGAL INCONSISTENCIES
      - Cross-reference statutory requirements with petition claims
      - Cite contradictions with specific Act provisions
      - Highlight gaps in statutory interpretation

III. CITATION DISCIPLINE
    ⚠️ CRITICAL: Every single legal assertion MUST include:
    - Explicit Section/Schedule number
    - Subsection/clause/proviso where relevant
    - Direct quotation from the statute when possible
    - Format: "Section X(Y)(z)" or "Schedule A, Part B"

IV. TONE AND STYLE
    - Authoritative and judicial
    - Use phrases like: "It is submitted that...", "Respectfully...", "The statute explicitly provides..."
    - Employ legal maxims where appropriate
    - Maintain objectivity while being incisive

V. FORMAT REQUIREMENTS
    - Plain text ONLY - NO markdown formatting (no **, ##, ###, etc.)
    - Use CAPITAL LETTERS for emphasis instead of bold
    - Use clear section breaks with headings like "STRENGTHS:", "WEAKNESSES:", etc.
    - Clean, professional legal memorandum format

Format your response as a formal legal memorandum with clear sections, numbered points, and pervasive statutory citations.""",

            'counter_arguments': """You are a seasoned advocate-on-record preparing comprehensive counter-arguments for filing before the appropriate legal forum under the Khyber Pakhtunkhwa Local Government Act, 2013.

═══════════════════════════════════════════════════════════════
DIRECTIVE: STATUTORY COUNTER-ARGUMENTS WITH AUTHORITATIVE LEGAL BACKING
═══════════════════════════════════════════════════════════════

IDENTIFIED LEGAL ISSUES:
{issues}

STATUTORY PROVISIONS FROM THE KPK LOCAL GOVERNMENT ACT, 2013:
{law_sections}

CLIENT'S LEGAL STRENGTHS:
{strengths}

OPPONENT'S LEGAL VULNERABILITIES:
{weaknesses}

MANDATORY DRAFTING REQUIREMENTS:

I. FORMAL STRUCTURE
   - Begin each argument with "COUNTER-ARGUMENT [NUMBER]:" as heading
   - Use formal legal drafting conventions
   - Conclude each argument with statutory reference summary
   - Employ persuasive yet authoritative language

II. REQUIRED ARGUMENTS (Each MUST Include Explicit Statutory Citations):

   A. PRIMARY COUNTER-ARGUMENTS TO OPPONENT'S ALLEGATIONS (4-7 Arguments)
      Format for EACH argument:

      COUNTER-ARGUMENT [N]: [HEADING]

      SUBMISSION:
      It is respectfully submitted that the opponent's allegation [describe] is legally untenable and contrary to the express provisions of the Act.

      STATUTORY FOUNDATION:
      - Cite EXACT Section/Schedule numbers (e.g., "Section 55(1)(a) of the Act explicitly provides that...")
      - Quote verbatim from the statute
      - Reference multiple sections if applicable
      - Cite subsections, clauses, provisos, and Schedules

      LEGAL ANALYSIS:
      - Apply statutory provisions to facts
      - Distinguish opponent's interpretation
      - Highlight mandatory vs. discretionary provisions

      CONCLUSION:
      Therefore, in light of Section [X], the opponent's claim is without merit.

   B. AFFIRMATIVE DEFENSES (3-5 Defenses)
      - MANDATORY: Ground each defense in specific statutory provisions
      - Cite Section numbers with exact subsections
      - Reference statutory exceptions, provisos, or saving clauses
      - Example: "The client's actions are protected under Section 66(3) which provides statutory immunity for..."

   C. PROCEDURAL OBJECTIONS (If Applicable)
      - Cite EXACT procedural provisions violated by opponent
      - Reference statutory timelines with Section numbers
      - Identify jurisdictional defects with statutory basis
      - Quote mandatory procedural requirements from the Act

   D. ALTERNATIVE STATUTORY INTERPRETATIONS
      - Provide alternative reading of ambiguous provisions
      - Cite purposive interpretation principles
      - Reference preamble or Statement of Objects if relevant
      - Support with specific Section/Schedule citations

III. CITATION MANDATE
    ⚠️ ABSOLUTE REQUIREMENT: No argument shall be made without:
    - Explicit Section/Schedule/Clause number
    - Verbatim quotation from the statute where possible
    - Reference to subsections and provisos
    - Format: "Section X(Y), read with Section Z(A)(b)"

IV. LEGAL LANGUAGE
    - Use formal court terminology
    - Employ phrases: "It is humbly submitted...", "Without prejudice to...", "In the alternative..."
    - Maintain persuasive yet respectful tone
    - Use legal Latin where appropriate (mutatis mutandis, prima facie, etc.)

V. STATUTORY INTEGRATION
    - Cross-reference multiple sections where applicable
    - Cite harmonious construction principles
    - Reference non-obstante clauses if present
    - Distinguish between mandatory and directory provisions

VI. FORMAT REQUIREMENTS
    - Plain text ONLY - NO markdown formatting (no **, ##, ###, etc.)
    - Use CAPITAL LETTERS for emphasis instead of bold
    - Use clear section breaks with "COUNTER-ARGUMENT 1:", "SUBMISSION:", etc.
    - Clean, professional legal document format

Format as a comprehensive written statement with numbered arguments, extensive statutory citations, and authoritative legal reasoning.""",

            'recommendations': """You are a distinguished legal strategist and senior counsel advising a client on comprehensive litigation strategy under the Khyber Pakhtunkhwa Local Government Act, 2013.

═══════════════════════════════════════════════════════════════
DIRECTIVE: STRATEGIC LEGAL RECOMMENDATIONS WITH STATUTORY GROUNDING
═══════════════════════════════════════════════════════════════

CASE OVERVIEW:
{case_summary}

IDENTIFIED LEGAL ISSUES:
{issues}

CLIENT'S STRENGTHS:
{strengths}

AREAS REQUIRING ATTENTION:
{weaknesses}

APPLICABLE STATUTORY PROVISIONS:
{law_sections}

MANDATORY ADVISORY FRAMEWORK:

I. IMMEDIATE ACTIONS (4-6 Priority Items)
   Format for EACH action:

   ACTION [N]: [Clear Action Item]

   STATUTORY BASIS:
   - Cite EXACT Section/Schedule requiring this action
   - Quote relevant mandatory provisions
   - Reference procedural timelines with Section numbers

   RATIONALE:
   - Explain how this strengthens statutory position
   - Reference specific provisions of the Act
   - Identify risks of non-compliance with Section numbers

   TIMELINE:
   - Specify urgency based on statutory deadlines
   - Cite time-bar provisions if applicable

   Example:
   ACTION 1: File Formal Written Statement within Statutory Period
   STATUTORY BASIS: Section X(Y) mandates submission within [timeframe]. Non-compliance attracts consequences under Section Z.
   RATIONALE: Compliance with mandatory procedural requirements under Section X ensures...

II. EVIDENCE AND DOCUMENTATION REQUIREMENTS (5-7 Specific Items)
    - Identify documents mandated by specific Sections
    - Cite evidentiary provisions with Section numbers
    - Reference Schedule requirements for documentation
    - Specify statutory forms or formats if prescribed
    - Example: "Obtain certified copy of notification under Section 55(2) as proof of..."

III. PROCEDURAL STEPS WITH STATUTORY FOUNDATION (4-6 Steps)
     Format:

     STEP [N]: [Procedural Action]
     STATUTORY PROVISION: Section X(Y)(z) provides that...
     COMPLIANCE REQUIREMENTS: [Detail mandatory elements]
     CONSEQUENCES OF NON-COMPLIANCE: Section A(B) prescribes...

     MANDATORY: Every step must cite specific Section/Schedule

IV. RISK ANALYSIS AND MITIGATION (3-5 Risks)
    Format:

    RISK [N]: [Identified Legal Risk]
    STATUTORY SOURCE: Section X creates risk of...
    MITIGATION STRATEGY:
    - Cite Section Y which provides safeguards
    - Reference statutory defenses under Section Z
    - Identify procedural protections with citations

    CRITICAL: Each risk and mitigation must reference specific provisions

V. ADVANCED STRATEGIC CONSIDERATIONS
   - Cite alternative remedies under different Sections
   - Reference appellate provisions with Section numbers
   - Identify statutory limitations periods with citations
   - Consider interim relief provisions (cite Sections)
   - Reference settlement/ADR provisions if applicable in the Act

VI. CITATION DISCIPLINE
    ⚠️ MANDATORY: Every recommendation MUST include:
    - Explicit Section/Schedule/Clause numbers
    - Reference to subsections and provisos
    - Quotation of key mandatory language
    - Cross-references between related provisions

VII. PRIORITIZATION
     - Mark each item as: URGENT / HIGH PRIORITY / ROUTINE
     - Base urgency on statutory timelines (cite Sections)
     - Highlight time-bar provisions with Section numbers

VIII. FORMAT REQUIREMENTS
     - Plain text ONLY - NO markdown formatting (no **, ##, ###, etc.)
     - Use CAPITAL LETTERS for emphasis instead of bold
     - Use clear section breaks with "ACTION 1:", "RISK 1:", etc.
     - Clean, professional legal memorandum format

Format as a comprehensive legal strategy memorandum with clear action items, extensive statutory citations, risk assessments, and prioritized recommendations grounded in specific provisions of the Act.""",

            'formal_response': """You are a distinguished legal draftsman preparing a formal written statement/reply for filing before the competent authority/court under the Khyber Pakhtunkhwa Local Government Act, 2013.

═══════════════════════════════════════════════════════════════
DIRECTIVE: DRAFT FORMAL LEGAL RESPONSE WITH COMPREHENSIVE STATUTORY FOUNDATION
═══════════════════════════════════════════════════════════════

CASE PARTICULARS:
{case_summary}

COUNTER-ARGUMENTS DEVELOPED:
{counter_arguments}

STATUTORY PROVISIONS FROM THE ACT:
{law_sections}

DRAFTING MANDATE:

I. FORMAL STRUCTURE (Strict Compliance Required)

   A. TITLE AND STYLE OF CAUSE
      - Proper identification of forum
      - Complete party names and designations
      - Case/Petition number
      - Statutory reference to jurisdiction

   B. PRELIMINARY OBJECTIONS (If Applicable)
      Format:
      PRELIMINARY OBJECTION [N]: [Heading]

      It is respectfully submitted that this [petition/complaint] is liable to be dismissed in limine on the following statutory grounds:

      - Cite EXACT Section numbers for jurisdictional/procedural defects
      - Quote mandatory requirements from the Act
      - Reference non-compliance with specific provisions
      - Example: "The petition is barred under Section X(Y) which mandates..."

   C. STATEMENT OF FACTS
      - Present client's version in formal paragraphs
      - Reference dates, events, and statutory compliance
      - Cite relevant statutory provisions at each factual assertion
      - Example: "On [date], pursuant to Section X, the respondent..."

   D. LEGAL ARGUMENTS (Principal Component)
      Format for EACH argument:

      ARGUMENT [N]: [CLEAR HEADING]

      SUBMISSIONS:
      It is respectfully submitted that [legal position]

      STATUTORY FOUNDATION:
      - Cite EXACT Section/Schedule numbers
      - Quote verbatim from the Act
      - Reference subsections, clauses, provisos
      - Cross-reference related provisions

      APPLICATION TO FACTS:
      - Apply statutory provisions to case facts
      - Distinguish opponent's interpretation
      - Highlight mandatory compliance achieved

      LEGAL PRECEDENT (If Applicable):
      - Reference principles of statutory interpretation
      - Cite purposive construction approach

      CONCLUSION:
      Therefore, in light of Section [X], it is submitted that...

   E. PRAYER FOR RELIEF
      Format:
      In light of the facts stated and arguments advanced, it is most respectfully prayed that this Hon'ble [Authority/Court]:

      a) [Relief sought] in accordance with Section X of the Act;
      b) [Alternative relief] under Section Y;
      c) Any other relief deemed fit under the provisions of the Act.

II. MANDATORY CITATION REQUIREMENTS
    ⚠️ CRITICAL: The entire response must demonstrate:
    - Pervasive statutory citations (Section/Schedule/Clause)
    - Verbatim quotations from the Act
    - Cross-references between provisions
    - Precise subsection and proviso references
    - Format: "Section X(Y)(z), read with Section A(B)"

III. LEGAL LANGUAGE AND STYLE
     - Formal court language throughout
     - Use: "It is respectfully submitted...", "Without prejudice...", "In the alternative..."
     - Employ legal terms: ultra vires, intra vires, locus standi, etc.
     - Maintain respectful yet authoritative tone
     - Use structured paragraphing with numbering

IV. STATUTORY INTEGRATION DEPTH
    - Every legal assertion must cite specific provisions
    - Reference preamble for legislative intent if relevant
    - Cite definitions section for key terms
    - Cross-reference Schedules where applicable
    - Distinguish mandatory vs. directory provisions with citations

V. FORMAT REQUIREMENTS
    - Plain text ONLY - NO markdown formatting (no **, ##, ###, etc.)
    - Use CAPITAL LETTERS for emphasis instead of bold
    - Use clear section breaks with "ARGUMENT 1:", "SUBMISSIONS:", "PRAYER:", etc.
    - Clean, professional legal document format suitable for court filing

Format as a complete formal legal document suitable for filing, with comprehensive statutory citations, formal legal language, and structured argumentation grounded entirely in the provisions of the Khyber Pakhtunkhwa Local Government Act, 2013."""
        }

    def generate_commentary(
        self,
        case_analysis: Dict[str, Any],
        law_retrieval: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main generation method: Create complete legal commentary

        Args:
            case_analysis: Output from CaseAgent
            law_retrieval: Output from LawAgent

        Returns:
            Structured legal commentary
        """
        # Generate each component
        petition_critique = self._generate_petition_critique(
            case_analysis, law_retrieval
        )

        counter_arguments = self._generate_counter_arguments(
            case_analysis, law_retrieval
        )

        recommendations = self._generate_recommendations(
            case_analysis, law_retrieval
        )

        procedural_guidance = self._generate_procedural_guidance(
            case_analysis, law_retrieval
        )

        # Generate comprehensive legal conclusion
        legal_conclusion = self._generate_legal_conclusion(
            case_analysis, law_retrieval, petition_critique, counter_arguments, recommendations
        )

        # Compile complete commentary
        commentary = {
            'petition_critique': petition_critique,
            'counter_arguments': counter_arguments,
            'recommendations': recommendations,
            'procedural_guidance': procedural_guidance,
            'legal_conclusion': legal_conclusion,
            'executive_summary': self._generate_executive_summary(
                case_analysis, law_retrieval, petition_critique, counter_arguments
            ),
            'disclaimer': self._generate_disclaimer(),
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'issue_count': len(case_analysis.get('legal_issues', [])),
                'law_section_count': len(law_retrieval.get('all_relevant_sections', [])),
                'agent_version': 'v2.0'
            }
        }

        return commentary

    def _generate_petition_critique(
        self,
        case_analysis: Dict[str, Any],
        law_retrieval: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate critique of opponent's petition"""
        # Prepare context
        petition_summary = self._format_case_summary(case_analysis)
        law_sections = self._format_law_sections(law_retrieval['all_relevant_sections'][:12])

        # Build prompt
        prompt = self.templates['petition_critique'].format(
            petition_summary=petition_summary,
            law_sections=law_sections
        )

        # Generate using Gemini
        try:
            response = self.gemini_client.model.generate_content(prompt)
            critique_text = response.text

            return {
                'text': critique_text,
                'generated_at': datetime.now().isoformat(),
                'law_sections_used': [s['citation'] for s in law_retrieval['all_relevant_sections'][:12]]
            }

        except Exception as e:
            return {
                'text': f"Error generating critique: {str(e)}",
                'error': True,
                'generated_at': datetime.now().isoformat()
            }

    def _generate_counter_arguments(
        self,
        case_analysis: Dict[str, Any],
        law_retrieval: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate counter-arguments with statutory backing"""
        # Prepare context
        issues = self._format_issues(case_analysis['legal_issues'])
        law_sections = self._format_law_sections(law_retrieval['all_relevant_sections'][:15])
        strengths = self._format_strengths(case_analysis.get('strengths', []))
        weaknesses = self._format_weaknesses(case_analysis.get('weaknesses', []))

        # Build prompt
        prompt = self.templates['counter_arguments'].format(
            issues=issues,
            law_sections=law_sections,
            strengths=strengths,
            weaknesses=weaknesses
        )

        # Generate using Gemini
        try:
            response = self.gemini_client.model.generate_content(prompt)
            arguments_text = response.text

            return {
                'text': arguments_text,
                'generated_at': datetime.now().isoformat(),
                'law_sections_used': [s['citation'] for s in law_retrieval['all_relevant_sections'][:15]]
            }

        except Exception as e:
            return {
                'text': f"Error generating counter-arguments: {str(e)}",
                'error': True,
                'generated_at': datetime.now().isoformat()
            }

    def _generate_recommendations(
        self,
        case_analysis: Dict[str, Any],
        law_retrieval: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate strategic recommendations"""
        # Prepare context
        case_summary = self._format_case_summary(case_analysis)
        issues = self._format_issues(case_analysis['legal_issues'])
        strengths = self._format_strengths(case_analysis.get('strengths', []))
        weaknesses = self._format_weaknesses(case_analysis.get('weaknesses', []))
        law_sections = self._format_law_sections(law_retrieval['all_relevant_sections'][:12])

        # Build prompt
        prompt = self.templates['recommendations'].format(
            case_summary=case_summary,
            issues=issues,
            strengths=strengths,
            weaknesses=weaknesses,
            law_sections=law_sections
        )

        # Generate using Gemini
        try:
            response = self.gemini_client.model.generate_content(prompt)
            recommendations_text = response.text

            # Also include case agent recommendations
            case_recommendations = case_analysis.get('recommendations', [])

            return {
                'strategic_recommendations': recommendations_text,
                'tactical_recommendations': case_recommendations,
                'generated_at': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'strategic_recommendations': f"Error generating recommendations: {str(e)}",
                'tactical_recommendations': case_analysis.get('recommendations', []),
                'error': True,
                'generated_at': datetime.now().isoformat()
            }

    def _generate_procedural_guidance(
        self,
        case_analysis: Dict[str, Any],
        law_retrieval: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate procedural guidance"""
        procedural_sections = [
            s for s in law_retrieval['all_relevant_sections']
            if 'procedure' in s.get('text', '').lower()
            or 'process' in s.get('text', '').lower()
            or 'rule' in s.get('citation', '').lower()
        ][:3]

        if not procedural_sections:
            # Use general procedural advice
            guidance = {
                'steps': [
                    {
                        'step': 1,
                        'action': 'File formal written response within prescribed time limit',
                        'statutory_basis': 'General procedural rules'
                    },
                    {
                        'step': 2,
                        'action': 'Submit supporting affidavits and documentary evidence',
                        'statutory_basis': 'Rules of evidence'
                    },
                    {
                        'step': 3,
                        'action': 'Request oral hearing if required',
                        'statutory_basis': 'Natural justice principles'
                    }
                ],
                'time_limits': 'Check applicable rules for specific time limits',
                'forum': 'Verify proper forum under KPK Local Government Act 2013'
            }
        else:
            # Extract procedural steps from retrieved sections
            guidance = {
                'steps': [
                    {
                        'step': i + 1,
                        'action': f"Follow procedure under {s['citation']}",
                        'statutory_basis': s['citation']
                    }
                    for i, s in enumerate(procedural_sections)
                ],
                'relevant_sections': [s['citation'] for s in procedural_sections],
                'note': 'Consult complete text of cited sections for detailed procedural requirements'
            }

        return guidance

    def _generate_legal_conclusion(
        self,
        case_analysis: Dict[str, Any],
        law_retrieval: Dict[str, Any],
        petition_critique: Dict[str, Any],
        counter_arguments: Dict[str, Any],
        recommendations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive judgement with statutory foundation"""

        # Prepare comprehensive context
        case_summary = self._format_case_summary(case_analysis)
        issues = self._format_issues(case_analysis['legal_issues'])
        strengths = self._format_strengths(case_analysis.get('strengths', []))
        weaknesses = self._format_weaknesses(case_analysis.get('weaknesses', []))
        law_sections = self._format_law_sections(law_retrieval['all_relevant_sections'][:15])

        # Build comprehensive judgement prompt
        conclusion_prompt = f"""You are a distinguished senior High Court judge with 25+ years of judicial experience, preparing a DECISIVE JUDICIAL OPINION on a case under the Khyber Pakhtunkhwa Local Government Act, 2013.

═══════════════════════════════════════════════════════════════
DIRECTIVE: DECISIVE, AUTHORITATIVE JUDICIAL OPINION
═══════════════════════════════════════════════════════════════

CASE OVERVIEW:
{case_summary}

IDENTIFIED LEGAL ISSUES:
{issues}

CLIENT'S STRENGTHS:
{strengths}

AREAS OF CONCERN:
{weaknesses}

APPLICABLE STATUTORY PROVISIONS FROM THE KPK LOCAL GOVERNMENT ACT, 2013:
{law_sections}

ANALYSIS COMPLETED:
- Petition Critique: {len(petition_critique.get('text', ''))} characters of analysis
- Counter-Arguments: {len(counter_arguments.get('text', ''))} characters of legal argumentation
- Strategic Recommendations: Developed and documented

═══════════════════════════════════════════════════════════════

CRITICAL MANDATE: This is NOT a tentative analysis. You are rendering a DECISIVE JUDICIAL DETERMINATION.

MANDATORY REQUIREMENTS FOR JUDICIAL OPINION:

I. EXECUTIVE DETERMINATION (Opening - Maximum Impact)

   Begin with a decisive, authoritative opening that immediately establishes:

   "Having thoroughly examined the statutory provisions, factual matrix, and legal arguments presented, this Court renders the following DECISIVE DETERMINATION on the merits of this matter under the Khyber Pakhtunkhwa Local Government Act, 2013."

   Immediately follow with:
   - Clear statement of case outcome prospects (FAVORABLE / UNFAVORABLE / MIXED)
   - Primary statutory basis in 2-3 sentences
   - Core legal finding that drives the entire opinion

II. STATUTORY FRAMEWORK (Concise but Authoritative)

   In 3-4 paragraphs maximum:
   - Identify the 3-5 MOST CRITICAL statutory provisions
   - Quote ONLY the decisive language from each Section
   - Establish how these provisions CONCLUSIVELY govern this dispute
   - State legislative intent with judicial authority

III. DECISIVE FINDINGS OF LAW

   For EACH major legal issue (3-5 maximum):

   FINDING [N]: [CLEAR, UNEQUIVOCAL LEGAL DETERMINATION]

   State your judicial finding as a CONCLUSION, not a possibility:
   ✓ "It is hereby determined that..."
   ✓ "The statutory provision MANDATES that..."
   ✓ "The law is CLEAR and UNAMBIGUOUS..."
   ✓ "This Court FINDS that..."

   ✗ Avoid: "It may be argued...", "Possibly...", "Perhaps...", "It could be said..."

   STATUTORY FOUNDATION:
   - Cite the EXACT Section that COMPELS this finding
   - Quote the DECISIVE language only
   - State: "Section X EXPRESSLY provides / MANDATES / REQUIRES / PROHIBITS..."

   JUDICIAL DETERMINATION:
   "In light of the unambiguous language of Section [X](Y)(z), and having regard to the legislative scheme, this Court CONCLUSIVELY determines that [specific finding]. This finding is INESCAPABLE and BINDING."

IV. ASSESSMENT OF PARTIES' POSITIONS (Decisive, Not Exploratory)

   A. OPPONENT'S PETITION:
      State in 2-3 paragraphs:
      - Whether it SUCCEEDS or FAILS (and to what degree)
      - The FATAL defects (if any) with Section citations
      - The CONCLUSIVE determination on each claim
      Use: "The petition FAILS to establish...", "The claim is UNSUSTAINABLE under Section X..."

   B. CLIENT'S POSITION:
      State in 2-3 paragraphs:
      - Whether the defense/case SUCCEEDS or FAILS (and to what degree)
      - The DECISIVE statutory protections/rights
      - The CONCLUSIVE determination on viability
      Use: "The client's position is WELL-FOUNDED under Section X...", "The defense CONCLUSIVELY succeeds..."

V. ULTIMATE JUDICIAL DETERMINATION (Maximum Decisiveness)

   This is your FINAL RULING. Write it like a judge issuing an ORDER:

   "JUDICIAL DETERMINATION:

   Having conducted a comprehensive statutory analysis and having applied the provisions of the Khyber Pakhtunkhwa Local Government Act, 2013 to the facts and circumstances of this matter, this Court renders the following CONCLUSIVE findings:

   1. PRIMARY DETERMINATION: [State the MAIN outcome decisively]
      STATUTORY BASIS: Section X(Y)(z) MANDATES / PROHIBITS / REQUIRES [specific outcome]
      CONCLUSION: The [petition/claim/defense] SUCCEEDS / FAILS on this ground.

   2. SECONDARY DETERMINATION: [State supporting finding]
      STATUTORY BASIS: Section A(B) read with Section C(D) ESTABLISHES that [finding]
      CONCLUSION: This claim/defense is SUSTAINABLE / UNSUSTAINABLE.

   3. PROCEDURAL DETERMINATION: [State any procedural finding]
      STATUTORY BASIS: Section M(N)
      CONCLUSION: [Decisive procedural outcome]"

VI. PROSPECTS OF SUCCESS (Clear Percentages and Definitive Assessment)

   State decisively:

   "OVERALL ASSESSMENT OF PROSPECTS:

   FAVORABLE CLAIMS (70-90% success likelihood):
   - [List with Section citations] - These claims are STRONGLY SUPPORTED by the statutory framework and WILL LIKELY SUCCEED.

   UNCERTAIN CLAIMS (40-60% success likelihood):
   - [List with Section citations] - These require additional evidence but are VIABLE under the Act.

   UNFAVORABLE CLAIMS (0-30% success likelihood):
   - [List with Section citations] - These claims LACK statutory foundation and WILL LIKELY FAIL."

VII. FINAL JUDICIAL PRONOUNCEMENT (Like a Judgment Order)

   Close with a decisive paragraph:

   "FINAL DETERMINATION:

   Upon full consideration of the statutory framework under the Khyber Pakhtunkhwa Local Government Act, 2013, and having applied the law to the facts presented, this Court CONCLUSIVELY determines that [overall case outcome]. The statutory provisions, particularly Sections [X, Y, Z], UNAMBIGUOUSLY support this determination. The [client/petitioner] has a [STRONG/MODERATE/WEAK] case on the merits, with [specific percentage or qualitative assessment] prospects of success.

   The recommended course of action is [SPECIFIC DIRECTIVE: file/defend/settle/appeal] based on the foregoing statutory analysis.

   This opinion is rendered on [date] following comprehensive legal analysis."

CRITICAL TONE REQUIREMENTS:

✓ USE: "It is DETERMINED", "The Court FINDS", "CONCLUSIVELY established", "MANDATES", "PROHIBITS", "UNAMBIGUOUS", "DECISIVE", "BINDING"
✓ USE: Declarative sentences, active voice, definitive conclusions
✓ USE: "WILL succeed", "WILL fail", "IS supported", "IS contrary to"

✗ AVOID: "may", "might", "could", "possibly", "perhaps", "it seems", "arguably"
✗ AVOID: Tentative language, excessive qualifications, exploratory tone
✗ AVOID: Markdown formatting (**, ###, etc.) - use plain text only

FORMAT REQUIREMENTS:

- Plain text ONLY - NO markdown formatting (no **, ##, ###, etc.)
- Use CAPITAL LETTERS for emphasis instead of bold
- Use clear section breaks with "FINDING 1:", "DETERMINATION:", etc.
- Clean, professional judicial opinion format
- Numbered findings with clear headings
- Minimum 1000 words, maximum 1500 words

TONE: Authoritative, decisive, judicial, commanding - like a High Court judgment

Generate the DECISIVE JUDICIAL OPINION now:"""

        # Generate conclusion using Gemini
        try:
            response = self.gemini_client.model.generate_content(conclusion_prompt)
            conclusion_text = response.text

            return {
                'text': conclusion_text,
                'generated_at': datetime.now().isoformat(),
                'law_sections_used': [s['citation'] for s in law_retrieval['all_relevant_sections'][:15]],
                'issues_addressed': len(case_analysis.get('legal_issues', [])),
                'type': 'comprehensive_statutory_conclusion'
            }

        except Exception as e:
            return {
                'text': f"Error generating judgement: {str(e)}",
                'error': True,
                'generated_at': datetime.now().isoformat()
            }

    def _generate_executive_summary(
        self,
        case_analysis: Dict[str, Any],
        law_retrieval: Dict[str, Any],
        petition_critique: Dict[str, Any],
        counter_arguments: Dict[str, Any]
    ) -> str:
        """Generate executive summary of the complete analysis (plain text format)"""
        case_summary = case_analysis.get('case_summary', {})
        dispute_type = case_summary.get('dispute_type', 'Legal Dispute')
        issue_count = len(case_analysis.get('legal_issues', []))
        complexity = case_summary.get('complexity', 'medium')

        summary_parts = [
            f"CASE TYPE: {dispute_type}",
            f"COMPLEXITY: {complexity.upper()}",
            f"ISSUES IDENTIFIED: {issue_count}",
            f"RELEVANT STATUTORY PROVISIONS: {len(law_retrieval.get('all_relevant_sections', []))}",
            "",
            "KEY FINDINGS:",
        ]

        # Add strengths
        strengths = case_analysis.get('strengths', [])
        if strengths:
            summary_parts.append(f"- {len(strengths)} strength(s) identified in client's position")

        # Add weaknesses
        weaknesses = case_analysis.get('weaknesses', [])
        if weaknesses:
            summary_parts.append(f"- {len(weaknesses)} area(s) requiring attention")

        # Add critical issues
        critical_issues = [i for i in case_analysis.get('legal_issues', []) if i.get('severity') == 'high']
        if critical_issues:
            summary_parts.append(f"- {len(critical_issues)} high-priority issue(s) require immediate response")

        summary_parts.extend([
            "",
            "PRIMARY RECOMMENDATIONS:",
        ])

        # Add top 3 recommendations
        recommendations = case_analysis.get('recommendations', [])[:3]
        for i, rec in enumerate(recommendations, 1):
            summary_parts.append(f"{i}. {rec.get('action', 'N/A')}")

        return "\n".join(summary_parts)

    def _generate_disclaimer(self) -> str:
        """Generate legal disclaimer"""
        return """**LEGAL DISCLAIMER**

This analysis is AI-generated and provided for informational purposes only. It does not constitute legal advice and should not be relied upon as a substitute for consultation with a qualified legal professional licensed to practice in Pakistan.

Key Limitations:
- This analysis is based on the KPK Local Government Act 2013 and may not cover all applicable laws
- Statutory law is subject to judicial interpretation and amendments
- Factual accuracy depends on information provided by the user
- Procedural rules and time limits must be verified independently
- Jurisdiction and forum must be confirmed with a licensed attorney

**Action Required**: Consult a licensed legal practitioner before taking any legal action based on this analysis.

Generated by: RAGBot-v2 Multi-Agent Legal Assistant
Date: {date}
""".format(date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def _format_case_summary(self, case_analysis: Dict[str, Any]) -> str:
        """Format case summary for prompt"""
        summary = case_analysis.get('case_summary', {})
        lines = [
            f"Dispute Type: {summary.get('dispute_type', 'N/A')}",
            f"Parties: {summary.get('parties', {}).get('user_party', 'User')} vs {summary.get('parties', {}).get('opponent_party', 'Opponent')}",
            f"Issue Count: {summary.get('issue_count', 0)}",
            f"Complexity: {summary.get('complexity', 'medium')}",
        ]
        return "\n".join(lines)

    def _format_issues(self, issues: List[Dict[str, Any]]) -> str:
        """Format issues for prompt"""
        if not issues:
            return "No specific issues identified."

        lines = []
        for i, issue in enumerate(issues[:10], 1):  # Limit to top 10
            lines.append(f"{i}. [{issue.get('category', 'general')}] {issue.get('description', '')[:150]}")

        return "\n".join(lines)

    def _format_law_sections(self, sections: List[Dict[str, Any]]) -> str:
        """Format law sections for prompt"""
        if not sections:
            return "No specific statutory provisions retrieved."

        lines = []
        for i, section in enumerate(sections, 1):
            citation = section.get('citation', 'Unknown')
            text = section.get('sliced_text') or section.get('text', '')
            # Provide more text for better statutory context (increased from 300 to 700)
            text_preview = text[:700] + "..." if len(text) > 700 else text
            lines.append(f"{i}. {citation}\n   {text_preview}\n")

        return "\n".join(lines)

    def _format_strengths(self, strengths: List[Dict[str, str]]) -> str:
        """Format strengths for prompt"""
        if not strengths:
            return "No specific strengths identified."

        lines = []
        for i, strength in enumerate(strengths, 1):
            lines.append(f"{i}. [{strength.get('category', 'general')}] {strength.get('description', '')}")

        return "\n".join(lines)

    def _format_weaknesses(self, weaknesses: List[Dict[str, str]]) -> str:
        """Format weaknesses for prompt"""
        if not weaknesses:
            return "No specific weaknesses identified."

        lines = []
        for i, weakness in enumerate(weaknesses, 1):
            lines.append(f"{i}. [{weakness.get('category', 'general')}] {weakness.get('description', '')}")

        return "\n".join(lines)

    def export_commentary_markdown(
        self,
        commentary: Dict[str, Any],
        filepath: str
    ) -> None:
        """
        Export commentary to Markdown file

        Args:
            commentary: Generated commentary
            filepath: Output file path
        """
        md_lines = [
            "# Legal Commentary Report",
            "",
            f"**Generated**: {commentary['metadata']['generated_at']}",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            commentary['executive_summary'],
            "",
            "---",
            "",
            "## Petition Critique",
            "",
            commentary['petition_critique']['text'],
            "",
            "---",
            "",
            "## Counter-Arguments",
            "",
            commentary['counter_arguments']['text'],
            "",
            "---",
            "",
            "## Strategic Recommendations",
            "",
            commentary['recommendations']['strategic_recommendations'],
            "",
            "### Tactical Actions",
            "",
        ]

        # Add tactical recommendations
        for rec in commentary['recommendations'].get('tactical_recommendations', []):
            md_lines.append(f"- **{rec.get('action', 'N/A')}** (Priority: {rec.get('priority', 'medium')})")
            md_lines.append(f"  - {rec.get('details', '')}")

        md_lines.extend([
            "",
            "---",
            "",
            "## Procedural Guidance",
            "",
        ])

        # Add procedural steps
        guidance = commentary['procedural_guidance']
        for step in guidance.get('steps', []):
            md_lines.append(f"{step['step']}. {step['action']}")
            md_lines.append(f"   - Basis: {step.get('statutory_basis', 'N/A')}")

        md_lines.extend([
            "",
            "---",
            "",
            "## Judgement",
            "",
            commentary.get('legal_conclusion', {}).get('text', 'No judgement generated.'),
            "",
            "---",
            "",
            commentary['disclaimer']
        ])

        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(md_lines))


def generate_commentary(
    case_analysis: Dict[str, Any],
    law_retrieval: Dict[str, Any],
    gemini_client: EnhancedGeminiClient
) -> Dict[str, Any]:
    """
    Convenience function for quick commentary generation

    Args:
        case_analysis: Output from CaseAgent
        law_retrieval: Output from LawAgent
        gemini_client: Initialized Gemini client

    Returns:
        Structured legal commentary
    """
    agent = DraftingAgent(gemini_client)
    return agent.generate_commentary(case_analysis, law_retrieval)
