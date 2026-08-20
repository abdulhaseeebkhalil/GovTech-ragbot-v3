"""
Orchestrator for RAGBot-v2: Multi-Agent Workflow Coordination

This module coordinates the execution of the multi-agent legal assistant workflow:
Processing → Case Agent → Law Agent → Drafting Agent
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

# Import all agents and processors
from .processing import DocumentProcessor
from .case_agent import CaseAgent
from .law_agent import LawAgent
from .drafting_agent import DraftingAgent
from .vector_store import EnhancedQdrantVectorStore
from .gemini_client import EnhancedGeminiClient


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    PROCESSING = "processing"
    CASE_ANALYSIS = "case_analysis"
    LAW_RETRIEVAL = "law_retrieval"
    DRAFTING = "drafting"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowState:
    """
    Maintains state of the multi-agent workflow

    Persists inputs, intermediate outputs, and final results for audit trail
    """

    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize workflow state

        Args:
            session_id: Unique session identifier (auto-generated if not provided)
        """
        self.session_id = session_id or self._generate_session_id()
        self.status = WorkflowStatus.PENDING
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at

        # Inputs
        self.narrative = None
        self.petition = None

        # Intermediate outputs
        self.processed_data = None
        self.case_analysis = None
        self.law_retrieval = None
        self.commentary = None

        # Errors and warnings
        self.errors = []
        self.warnings = []

        # Execution metadata
        self.execution_log = []

    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        from uuid import uuid4
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid4())[:8]}"

    def log_step(self, step_name: str, status: str, details: Optional[str] = None):
        """
        Log a workflow step

        Args:
            step_name: Name of the workflow step
            status: Status (success/error/warning)
            details: Optional details or error message
        """
        log_entry = {
            'step': step_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.execution_log.append(log_entry)
        self.updated_at = datetime.now().isoformat()

    def add_error(self, error_message: str, step: Optional[str] = None):
        """Add error to state"""
        error_entry = {
            'message': error_message,
            'step': step,
            'timestamp': datetime.now().isoformat()
        }
        self.errors.append(error_entry)
        self.log_step(step or 'unknown', 'error', error_message)

    def add_warning(self, warning_message: str, step: Optional[str] = None):
        """Add warning to state"""
        warning_entry = {
            'message': warning_message,
            'step': step,
            'timestamp': datetime.now().isoformat()
        }
        self.warnings.append(warning_entry)
        self.log_step(step or 'unknown', 'warning', warning_message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary"""
        return {
            'session_id': self.session_id,
            'status': self.status.value,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'inputs': {
                'narrative': self.narrative,
                'petition': self.petition
            },
            'outputs': {
                'processed_data': self.processed_data,
                'case_analysis': self.case_analysis,
                'law_retrieval': self.law_retrieval,
                'commentary': self.commentary
            },
            'errors': self.errors,
            'warnings': self.warnings,
            'execution_log': self.execution_log
        }

    def save(self, filepath: Optional[str] = None):
        """Save state to JSON file"""
        if filepath is None:
            filepath = f"workflow_state_{self.session_id}.json"

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, filepath: str) -> 'WorkflowState':
        """Load state from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        state = cls(session_id=data['session_id'])
        state.status = WorkflowStatus(data['status'])
        state.created_at = data['created_at']
        state.updated_at = data['updated_at']

        state.narrative = data['inputs']['narrative']
        state.petition = data['inputs']['petition']

        state.processed_data = data['outputs']['processed_data']
        state.case_analysis = data['outputs']['case_analysis']
        state.law_retrieval = data['outputs']['law_retrieval']
        state.commentary = data['outputs']['commentary']

        state.errors = data['errors']
        state.warnings = data['warnings']
        state.execution_log = data['execution_log']

        return state


class AgentOrchestrator:
    """
    Agent Orchestrator: Coordinates multi-agent workflow execution
    """

    def __init__(
        self,
        vector_store: EnhancedQdrantVectorStore,
        gemini_client: EnhancedGeminiClient
    ):
        """
        Initialize orchestrator with required services

        Args:
            vector_store: Initialized Qdrant vector store
            gemini_client: Initialized Gemini client
        """
        self.vector_store = vector_store
        self.gemini_client = gemini_client

        # Initialize agents
        self.document_processor = DocumentProcessor()
        self.case_agent = CaseAgent(gemini_client=gemini_client)
        self.law_agent = LawAgent(vector_store=vector_store)
        self.drafting_agent = DraftingAgent(gemini_client=gemini_client)

    def execute_workflow(
        self,
        narrative: str,
        petition: str,
        session_id: Optional[str] = None,
        enable_fallback: bool = True
    ) -> WorkflowState:
        """
        Execute complete multi-agent workflow

        Args:
            narrative: User's narrative text
            petition: Opponent's petition text
            session_id: Optional session ID for resuming
            enable_fallback: Enable fallback mechanisms if steps fail

        Returns:
            WorkflowState with complete results
        """
        # Initialize or resume workflow state
        state = WorkflowState(session_id=session_id)
        state.narrative = narrative
        state.petition = petition

        print(f"🚀 Starting RAGBot-v2 workflow (Session: {state.session_id})")

        try:
            # Step 1: Document Processing (NER + Claim Extraction)
            state.status = WorkflowStatus.PROCESSING
            state = self._execute_processing(state)

            # Step 2: Case Analysis
            state.status = WorkflowStatus.CASE_ANALYSIS
            state = self._execute_case_analysis(state)

            # Step 3: Law Retrieval
            state.status = WorkflowStatus.LAW_RETRIEVAL
            state = self._execute_law_retrieval(state, enable_fallback)

            # Step 4: Drafting Commentary
            state.status = WorkflowStatus.DRAFTING
            state = self._execute_drafting(state)

            # Mark as completed
            state.status = WorkflowStatus.COMPLETED
            state.log_step('workflow', 'success', 'All steps completed successfully')

            print(f"✅ Workflow completed successfully (Session: {state.session_id})")

        except Exception as e:
            state.status = WorkflowStatus.FAILED
            state.add_error(f"Workflow failed: {str(e)}", step='workflow')
            print(f"❌ Workflow failed: {e}")

        return state

    def _execute_processing(self, state: WorkflowState) -> WorkflowState:
        """Execute document processing step"""
        print("📄 Step 1: Processing documents (NER + Claim Extraction)...")

        try:
            processed_data = self.document_processor.process_case(
                state.narrative,
                state.petition
            )

            state.processed_data = processed_data
            state.log_step('processing', 'success', f"Extracted {len(processed_data['narrative']['claims'])} narrative claims, {len(processed_data['petition']['claims'])} petition claims")

            print(f"  ✅ Processing complete: {processed_data['analysis']['narrative_claim_count']} narrative claims, {processed_data['analysis']['petition_claim_count']} petition claims")

        except Exception as e:
            state.add_error(f"Processing failed: {str(e)}", step='processing')
            print(f"  ❌ Processing error: {e}")
            raise

        return state

    def _execute_case_analysis(self, state: WorkflowState) -> WorkflowState:
        """Execute case analysis step"""
        print("⚖️  Step 2: Analyzing case (Issue extraction)...")

        try:
            case_analysis = self.case_agent.analyze_case(
                state.narrative,
                state.petition,
                extracted_data=state.processed_data
            )

            state.case_analysis = case_analysis
            state.log_step('case_analysis', 'success', f"Identified {len(case_analysis['legal_issues'])} legal issues")

            print(f"  ✅ Case analysis complete: {len(case_analysis['legal_issues'])} issues identified")

            # Warn if critical weaknesses found
            critical_weaknesses = [w for w in case_analysis.get('weaknesses', []) if w.get('severity') == 'high']
            if critical_weaknesses:
                state.add_warning(f"{len(critical_weaknesses)} critical weakness(es) identified", step='case_analysis')
                print(f"  ⚠️  {len(critical_weaknesses)} critical weakness(es) found")

        except Exception as e:
            state.add_error(f"Case analysis failed: {str(e)}", step='case_analysis')
            print(f"  ❌ Case analysis error: {e}")
            raise

        return state

    def _execute_law_retrieval(
        self,
        state: WorkflowState,
        enable_fallback: bool = True
    ) -> WorkflowState:
        """Execute law retrieval step"""
        print("📚 Step 3: Retrieving relevant law sections...")

        try:
            issues = state.case_analysis['legal_issues']

            law_retrieval = self.law_agent.retrieve_relevant_law(
                issues,
                max_sections_per_issue=3
            )

            state.law_retrieval = law_retrieval
            state.log_step('law_retrieval', 'success', f"Retrieved {len(law_retrieval['all_relevant_sections'])} unique law sections")

            print(f"  ✅ Law retrieval complete: {len(law_retrieval['all_relevant_sections'])} relevant sections found")

            # Check retrieval quality
            low_confidence_mappings = [
                m for m in law_retrieval['issue_law_mapping']
                if m['retrieval_confidence'] == 'low'
            ]

            if low_confidence_mappings and enable_fallback:
                state.add_warning(f"{len(low_confidence_mappings)} issue(s) have low-confidence law retrieval", step='law_retrieval')
                print(f"  ⚠️  {len(low_confidence_mappings)} issue(s) with low confidence - attempting fallback...")

                # Attempt fallback retrieval for low-confidence issues
                for mapping in low_confidence_mappings:
                    category = mapping['issue_category']
                    fallback_sections = self.law_agent.get_fallback_sections(category, limit=2)
                    if fallback_sections:
                        mapping['relevant_sections'].extend(fallback_sections)
                        print(f"     ✓ Added {len(fallback_sections)} fallback section(s) for {category} issue")

        except Exception as e:
            state.add_error(f"Law retrieval failed: {str(e)}", step='law_retrieval')
            print(f"  ❌ Law retrieval error: {e}")

            # If fallback is enabled, use empty retrieval instead of failing
            if enable_fallback:
                state.add_warning("Using fallback: empty law retrieval", step='law_retrieval')
                state.law_retrieval = {
                    'issue_law_mapping': [],
                    'all_relevant_sections': [],
                    'metadata': {'total_issues': 0, 'total_unique_sections': 0}
                }
                print("  ⚠️  Using fallback: continuing without law retrieval")
            else:
                raise

        return state

    def _execute_drafting(self, state: WorkflowState) -> WorkflowState:
        """Execute drafting commentary step"""
        print("✍️  Step 4: Generating legal commentary...")

        try:
            commentary = self.drafting_agent.generate_commentary(
                state.case_analysis,
                state.law_retrieval
            )

            state.commentary = commentary
            state.log_step('drafting', 'success', 'Legal commentary generated')

            print(f"  ✅ Drafting complete: Commentary generated")

            # Check for errors in commentary generation
            if commentary.get('petition_critique', {}).get('error'):
                state.add_warning("Petition critique generation encountered errors", step='drafting')

            if commentary.get('counter_arguments', {}).get('error'):
                state.add_warning("Counter-arguments generation encountered errors", step='drafting')

        except Exception as e:
            state.add_error(f"Drafting failed: {str(e)}", step='drafting')
            print(f"  ❌ Drafting error: {e}")
            raise

        return state

    def resume_workflow(self, state: WorkflowState) -> WorkflowState:
        """
        Resume workflow from saved state

        Args:
            state: Previously saved WorkflowState

        Returns:
            Updated WorkflowState
        """
        print(f"🔄 Resuming workflow from {state.status.value} state...")

        # Determine where to resume
        if state.status == WorkflowStatus.PENDING or state.status == WorkflowStatus.PROCESSING:
            return self.execute_workflow(state.narrative, state.petition, session_id=state.session_id)

        elif state.status == WorkflowStatus.CASE_ANALYSIS:
            state = self._execute_case_analysis(state)
            state = self._execute_law_retrieval(state)
            state = self._execute_drafting(state)
            state.status = WorkflowStatus.COMPLETED

        elif state.status == WorkflowStatus.LAW_RETRIEVAL:
            state = self._execute_law_retrieval(state)
            state = self._execute_drafting(state)
            state.status = WorkflowStatus.COMPLETED

        elif state.status == WorkflowStatus.DRAFTING:
            state = self._execute_drafting(state)
            state.status = WorkflowStatus.COMPLETED

        else:
            print("  ℹ️  Workflow already completed or failed")

        return state

    def get_summary(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Get workflow execution summary

        Args:
            state: WorkflowState

        Returns:
            Summary dictionary
        """
        summary = {
            'session_id': state.session_id,
            'status': state.status.value,
            'execution_time': state.updated_at,
            'steps_completed': len([log for log in state.execution_log if log['status'] == 'success']),
            'errors_count': len(state.errors),
            'warnings_count': len(state.warnings),
        }

        if state.case_analysis:
            summary['issues_identified'] = len(state.case_analysis.get('legal_issues', []))
            summary['strengths'] = len(state.case_analysis.get('strengths', []))
            summary['weaknesses'] = len(state.case_analysis.get('weaknesses', []))

        if state.law_retrieval:
            summary['law_sections_retrieved'] = len(state.law_retrieval.get('all_relevant_sections', []))

        if state.commentary:
            summary['commentary_generated'] = True
        else:
            summary['commentary_generated'] = False

        return summary


def run_legal_analysis(
    narrative: str,
    petition: str,
    vector_store: EnhancedQdrantVectorStore,
    gemini_client: EnhancedGeminiClient
) -> WorkflowState:
    """
    Convenience function to run complete legal analysis

    Args:
        narrative: User's narrative
        petition: Opponent's petition
        vector_store: Initialized vector store
        gemini_client: Initialized Gemini client

    Returns:
        WorkflowState with results
    """
    orchestrator = AgentOrchestrator(vector_store, gemini_client)
    return orchestrator.execute_workflow(narrative, petition)
