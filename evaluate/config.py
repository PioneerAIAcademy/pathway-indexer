"""
Configuration for LLM Evaluation Framework

Contains:
- Model configurations for GPT-4 and GPT-5 models
- Exact prompts copied from pathway-chatbot/backend/app/engine/__init__.py
- Grading prompt with 5 dimensions
- Evaluation settings (num_samples, random_seed)
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

# =============================================================================
# EXACT PROMPTS FROM PATHWAY-CHATBOT (DO NOT MODIFY)
# Source: pathway-chatbot/backend/app/engine/__init__.py
# =============================================================================

SYSTEM_CITATION_PROMPT = """
You are a helpful assistant who assists service missionaries with their BYU Pathway questions. You respond using information from a knowledge base containing nodes with metadata such as node ID, file name, and other relevant details. To ensure accuracy and transparency, include a citation for each fact or statement derived from the knowledge base.

Use the following format for citations: [^context number], as the identifier of the data node.

Example:
We have two nodes:
node_id: 1
text: Information about how service missionaries support BYU Pathway students.

node_id: 2
text: Details on training for service missionaries.

User question: How do service missionaries help students at BYU Pathway?
Your answer:
Service missionaries provide essential support by mentoring students and helping them navigate academic and spiritual challenges [^1]. They also receive specialized training to ensure they can effectively serve in this role [^2].

Ensure that each referenced piece of information is correctly cited. **If the information required to answer the question is not available in the retrieved nodes, respond with: "Sorry, I don't know."**

Definitions to keep in mind:
- Friend of the Church: An individual who is not a member of The Church of Jesus Christ of Latter-day Saints.
- Service Missionary: A volunteer who supports BYU Pathway students.
- BYU Pathway: A program offering online courses to help individuals improve their education and lives.
- Peer mentor: BYU Pathway students who offer guidance and support to other students. Mentors are not resources for missionaries.
- Gathering: Online or in-person sessions that students must attend per relevant attendance policies. As missionary is not necessary to report attendance.
- Canvas: Canvas is the online system used by BYU Pathway students to find course materials and submit their assignments. The students can't access to the zoom link from Canvas.
- Student Portal: The student portal is an online platform where BYU Pathway students can access various resources and information related to their studies. Students sign in to their portal at byupathway.org, where they can find their gathering location or Zoom link, view financial information for making payments, access academic course links and print their PathwayConnect certificate.
- Mentor Bridge Scholarship: It is a one-time scholarship for students in PathwayConnect and it can be awarded every two years to students in the online degree program.
- BYU-Pathway's Career Center: A hub dedicated to helping students prepare for and secure employment, build professional networks, and set themselves on a successful career.
- Three-year degree: A bachelor's degree that can be obtained in three years.
- starts date: The date when the term starts, information provided in academic calendar.
- Academic Calendar: The academic calendar is a schedule of important dates and deadlines for BYU Pathway students, also knows as the PathwayConnect calendar, Pathway Calendar, etc. Academic Calendar starts in Winter. most of the information is provided in markdown tables, make sure to read the information carefully. Be carefully if a table is not complete. Sometimes you will hace calendars from different years in the same document, be sure to read the year of the calendar. information for a specific year is not necessarily the same for another year, don't make assumptions. Priorize information fron source https://student-services.catalog.prod.coursedog.com/studentservices/academic-calendar

- When a user requests a specific term (e.g., Term 2 in 2025):
    - Map the term based on the sequence above.
    - For Term 2 in 2025: Look for **Winter Term 2** in 2025.
    - Validate that the retrieved chunks contain information for the correct term and year.
    - Always verify the term and year before constructing a response.
    - Do not make assumptions or provide incorrect information.

Abbreviations:
- OD: Online Degree
- PC: PathwayConnect
- EC3: English Connect 3
- institute: Religion (religion courses)
Also keep the abbreviations in mind in vice versa.

Audience: Your primary audience is service missionaries, when they use "I" in their questions, they are referring to themselves (Pathway missionaries). When they use "students," they are referring to BYU Pathway students.

Instruction: Tailor your responses based on the audience. If the question is from a service missionary (e.g., "How can I get help with a broken link?"), provide missionary-specific information. For questions about students, focus on student-relevant information. Always keep the response relevant to the question's context.

Follow these steps for certain topics:
- For questions about Zoom and Canvas, respond only based on the retrieved nodes. Do not make assumptions.
- Missionaries can't access to the student portal.
- Missionaries are not required to report student attendance. They may want to keep track of attendance on their own.
- Missionaries can change the name of the student in the printed certificate only if the student has requested it.
- The best way to solve Canvas connection issues is by trying the troubleshooting steps first.
- Church's Meetinghouse Locator: website to get know the ward/stake close to the person.
- Missionaries can see student materials in gathering resources.
- internal server error: students can join Canvas directly using a link for canvas authentication.
- Students can access the BYUI application by going to the degree application page.
- To know if an institute class is for credit, it is necessary to talk with the instructor.
- When you receive questions about the religion credits required for the three year degree program, answer with the religion credits required for a bachelor's degree.
- When you receive questions about the institute classes required for the three year degree program, answer with the institute classes required for a bachelor's degree.
"""

CONTEXT_PROMPT = """
Answer the question as truthfully as possible using the numbered contexts below. If the answer isn't in the text, please say "Sorry, I'm not able to answer this question. Could you rephrase it?" Please provide a detailed answer. For each sentence in your answer, include a link to the contexts the sentence came from using the format [^context number].

Contexts:
{context_str}

Instruction: Based on the above documents, provide a detailed answer for the user question below. Ensure that each statement is clearly cited, e.g., 'This is the answer based on the source [^1]. This is part of the answer [^2]...'
"""

CONDENSE_PROMPT_TEMPLATE = """
Based on the following follow-up question from the user,
rephrase it to form a complete, standalone question.

Follow Up Input: {question}
Standalone question:"""


# =============================================================================
# GRADING PROMPT
# =============================================================================

GRADING_PROMPT = """
You are an expert evaluator for a BYU Pathway Missionary Chatbot. Your task is to grade the quality of an AI assistant's response to a user question.

## Context Information
The AI was provided with the following retrieved documents from a knowledge base:
{retrieved_docs}

## User Question
{question}

## AI Response
{response}

## Grading Instructions
Evaluate the response on the following 5 dimensions. For each dimension, provide:
1. A score from 1-5 (1=very poor, 2=poor, 3=acceptable, 4=good, 5=excellent)
2. A brief explanation (1-2 sentences) justifying the score

### Dimensions

1. **On-Topic (1-5)**: Does the response directly address the user's question? Is it relevant to what was asked?
   - 5: Perfectly addresses the question with no tangential content
   - 3: Mostly addresses the question but includes some irrelevant information
   - 1: Completely misses the point of the question

2. **Grounded (1-5)**: Is the response based on the provided context documents? Does it use citations appropriately?
   - 5: All claims are supported by the provided documents with proper citations
   - 3: Some claims are supported, but some appear to be from outside knowledge
   - 1: Response appears to be made up or not based on the provided documents

3. **No Contradiction (1-5)**: Is the response consistent with the provided documents? Does it avoid contradicting the source material?
   - 5: Completely consistent with all provided documents
   - 3: Minor inconsistencies or ambiguities
   - 1: Directly contradicts information in the provided documents

4. **Understandability (1-5)**: Is the response clear, well-organized, and easy to understand?
   - 5: Crystal clear, well-structured, and easy to follow
   - 3: Understandable but could be clearer or better organized
   - 1: Confusing, poorly organized, or hard to understand

5. **Overall Quality (1-5)**: Considering all factors, how would you rate the overall quality of this response for helping a BYU Pathway service missionary?
   - 5: Excellent response that fully addresses the missionary's needs
   - 3: Adequate response but with room for improvement
   - 1: Poor response that would not be helpful

## Output Format
Respond with ONLY a valid JSON object in the following format:
{{
    "on_topic": {{
        "score": <1-5>,
        "explanation": "<brief explanation>"
    }},
    "grounded": {{
        "score": <1-5>,
        "explanation": "<brief explanation>"
    }},
    "no_contradiction": {{
        "score": <1-5>,
        "explanation": "<brief explanation>"
    }},
    "understandability": {{
        "score": <1-5>,
        "explanation": "<brief explanation>"
    }},
    "overall": {{
        "score": <1-5>,
        "explanation": "<brief explanation>"
    }}
}}
"""


# =============================================================================
# MODEL CONFIGURATIONS
# =============================================================================


@dataclass
class ModelConfig:
    """Configuration for a single model."""

    name: str
    model_id: str
    api_type: Literal["chat_completions", "responses"]
    # For Chat Completions API (GPT-4)
    temperature: Optional[float] = None
    # For Responses API (GPT-5)
    reasoning_effort: Optional[Literal["low", "medium", "high"]] = None
    # Pricing per 1M tokens
    input_price_per_1m: float = 0.0
    output_price_per_1m: float = 0.0


# Models to evaluate (from Slack instructions)
MODELS_TO_EVALUATE: list[ModelConfig] = [
    ModelConfig(
        name="GPT-4o-mini (current)",
        model_id="gpt-4o-mini",
        api_type="chat_completions",
        temperature=0.7,
        input_price_per_1m=0.15,  # $0.15 per 1M input tokens
        output_price_per_1m=0.60,  # $0.60 per 1M output tokens
    ),
    ModelConfig(
        name="GPT-5-nano",
        model_id="gpt-5-nano",
        api_type="responses",
        reasoning_effort="low",
        input_price_per_1m=0.05,  # $0.05 per 1M input tokens
        output_price_per_1m=0.40,  # $0.40 per 1M output tokens
    ),
    ModelConfig(
        name="GPT-5-mini",
        model_id="gpt-5-mini",
        api_type="responses",
        reasoning_effort="low",
        input_price_per_1m=0.25,  # $0.25 per 1M input tokens
        output_price_per_1m=2.00,  # $2.00 per 1M output tokens
    ),
    ModelConfig(
        name="GPT-5.1",
        model_id="gpt-5.1",
        api_type="responses",
        reasoning_effort="low",
        input_price_per_1m=1.25,  # $1.25 per 1M input tokens
        output_price_per_1m=10.00,  # $10.00 per 1M output tokens
    ),
]

# Grading model configuration (GPT-5.1 with reasoning_effort=high)
GRADER_MODEL = ModelConfig(
    name="GPT-5.1 Grader",
    model_id="gpt-5.1",
    api_type="responses",
    reasoning_effort="high",
    input_price_per_1m=1.25,
    output_price_per_1m=10.00,
)


# =============================================================================
# EVALUATION CONFIGURATION
# =============================================================================


@dataclass
class EvaluationConfig:
    """Main configuration for the evaluation framework."""

    # Sample settings
    num_samples: int = 100
    random_seed: int = 42  # 0 = sequential, non-zero = random selection

    # Paths
    langfuse_csv_path: Path = Path("/home/chris/byu-pathway/langfuse_traces_11_26_25.csv")
    output_dir: Path = Path("/home/chris/byu-pathway/pathway-indexer/data/evaluations")

    # Models
    models_to_evaluate: list[ModelConfig] = field(default_factory=lambda: MODELS_TO_EVALUATE.copy())
    grader_model: ModelConfig = field(default_factory=lambda: GRADER_MODEL)

    # Rate limiting
    requests_per_minute: int = 60
    delay_between_requests: float = 1.0  # seconds

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 5.0  # seconds

    def __post_init__(self):
        """Ensure output directory exists."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
