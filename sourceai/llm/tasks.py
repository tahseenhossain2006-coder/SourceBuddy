# sourceai/llm/tasks.py

from enum import Enum


class LLMTask(str, Enum):
    """
    Canonical LLM task definitions for SourceAI.

    Model selection is capability-oriented and handled centrally
    by ModelRouter. Individual application modules should use these
    task definitions instead of maintaining their own task enums.
    """

    # ------------------------------------------------------------------
    # Requirement / Query Understanding
    # ------------------------------------------------------------------

    REQUIREMENT_UNDERSTANDING = "requirement_understanding"
    INTENT_DETECTION = "intent_detection"
    ENTITY_EXTRACTION = "entity_extraction"
    CONSTRAINT_EXTRACTION = "constraint_extraction"

    QUERY_NORMALIZATION = "query_normalization"
    QUERY_EXPANSION = "query_expansion"
    SEARCH_REFINEMENT = "search_refinement"
    RESULT_RELEVANCE = "result_relevance"

    # ------------------------------------------------------------------
    # Supplier / Product Extraction
    # ------------------------------------------------------------------

    SUPPLIER_EXTRACTION = "supplier_extraction"
    PRODUCT_EXTRACTION = "product_extraction"

    # ------------------------------------------------------------------
    # Entity / Cross-source Intelligence
    # ------------------------------------------------------------------

    ENTITY_RESOLUTION = "entity_resolution"
    CROSS_SOURCE_RECONCILIATION = "cross_source_reconciliation"
    CONTRADICTION_DETECTION = "contradiction_detection"

    # ------------------------------------------------------------------
    # Evidence / Confidence / Filtering
    # ------------------------------------------------------------------

    EVIDENCE_VERIFICATION = "evidence_verification"
    CONFIDENCE_ANALYSIS = "confidence_analysis"
    NL_FILTERING = "nl_filtering"
    MISSING_DATA_REASONING = "missing_data_reasoning"

    # ------------------------------------------------------------------
    # Supplier Intelligence
    # ------------------------------------------------------------------

    SUPPLIER_COMPARISON = "supplier_comparison"
    SUPPLIER_RANKING = "supplier_ranking"
    RISK_ANALYSIS = "risk_analysis"

    # ------------------------------------------------------------------
    # Research / Reasoning
    # ------------------------------------------------------------------

    ITERATIVE_RESEARCH = "iterative_research"
    RECOMMENDATION = "recommendation"
    FINAL_ANSWER = "final_answer"

    # ------------------------------------------------------------------
    # Output / Communication
    # ------------------------------------------------------------------

    SUMMARIZATION = "summarization"
    CITATION_ANSWER = "citation_answer_generation"

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------

    PROMPT_INJECTION_DETECTION = "prompt_injection_detection"


# ----------------------------------------------------------------------
# Capability mapping
# ----------------------------------------------------------------------
#
# The router selects actual providers/models based on these capabilities.
#
# Supported capabilities currently used by SourceAI:
#
#   general
#   extraction
#   reasoning
#   security
#
# Do NOT put provider names or model names here.
# Provider/model fallback is the responsibility of ModelRouter.
# ----------------------------------------------------------------------

TASK_CAPABILITY_MAP = {
    # Requirement / Query Understanding
    LLMTask.REQUIREMENT_UNDERSTANDING: "general",
    LLMTask.INTENT_DETECTION: "general",
    LLMTask.ENTITY_EXTRACTION: "extraction",
    LLMTask.CONSTRAINT_EXTRACTION: "extraction",

    LLMTask.QUERY_NORMALIZATION: "general",
    LLMTask.QUERY_EXPANSION: "general",
    LLMTask.SEARCH_REFINEMENT: "general",
    LLMTask.RESULT_RELEVANCE: "general",

    # Supplier / Product Extraction
    LLMTask.SUPPLIER_EXTRACTION: "extraction",
    LLMTask.PRODUCT_EXTRACTION: "extraction",

    # Entity / Cross-source Intelligence
    LLMTask.ENTITY_RESOLUTION: "reasoning",
    LLMTask.CROSS_SOURCE_RECONCILIATION: "reasoning",
    LLMTask.CONTRADICTION_DETECTION: "reasoning",

    # Evidence / Confidence / Filtering
    LLMTask.EVIDENCE_VERIFICATION: "reasoning",
    LLMTask.CONFIDENCE_ANALYSIS: "reasoning",
    LLMTask.NL_FILTERING: "general",
    LLMTask.MISSING_DATA_REASONING: "reasoning",

    # Supplier Intelligence
    LLMTask.SUPPLIER_COMPARISON: "reasoning",
    LLMTask.SUPPLIER_RANKING: "reasoning",
    LLMTask.RISK_ANALYSIS: "reasoning",

    # Research / Reasoning
    LLMTask.ITERATIVE_RESEARCH: "reasoning",
    LLMTask.RECOMMENDATION: "reasoning",
    LLMTask.FINAL_ANSWER: "reasoning",

    # Output
    LLMTask.SUMMARIZATION: "general",
    LLMTask.CITATION_ANSWER: "reasoning",

    # Security
    LLMTask.PROMPT_INJECTION_DETECTION: "security",
}


# ----------------------------------------------------------------------
# Validation
# ----------------------------------------------------------------------

def validate_task_capability_map() -> None:
    """
    Ensure every LLMTask has exactly one capability mapping.

    This catches accidental omissions when a new task is added.
    """

    missing = [
        task
        for task in LLMTask
        if task not in TASK_CAPABILITY_MAP
    ]

    unknown = [
        task
        for task in TASK_CAPABILITY_MAP
        if task not in LLMTask
    ]

    if missing:
        raise RuntimeError(
            "LLM tasks missing capability mappings: "
            + ", ".join(task.value for task in missing)
        )

    if unknown:
        raise RuntimeError(
            "Capability map contains unknown LLM tasks: "
            + ", ".join(str(task) for task in unknown)
        )


# Validate the canonical task registry when this module is imported.
validate_task_capability_map()