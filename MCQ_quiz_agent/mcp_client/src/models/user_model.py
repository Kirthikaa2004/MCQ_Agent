from pydantic import BaseModel,Field
from typing import  Optional,TypedDict,Literal,Annotated,List,Union
from langchain.agents.middleware.types import AgentState
class RequestModel(BaseModel):
    user_id:str
    user_query:str 
    session_id:Optional[str] = None




# class ResponseModel(BaseModel):
#     """
#     The structured output schema for the Research Agent.
    
#     This model ensures that the agent from the qualitative analysis and findings (research context).
#     """
#     research_context: Optional[str] = Field(
#         default=None,
#         description=(
#             "A comprehensive summary of the research findings. This should include "
#             "key insights, explanations of concepts, and synthesized information "
#             "retrieved by the tools."
#         )
#     )



# class ReviewResponseModel(BaseModel):
#     """
#     Results of a PEP8 code format analysis. This model captures the 
#     outcome of the 'format_code' tool and categorizes the code's 
#     adherence to Python style guidelines.
#     """

#     error: Optional[str] = Field(
#         default=None,
#         description=(
#             "Contains the traceback or error message if the tool failed to run "
#             "(e.g., due to a SyntaxError). Should be null if the analysis finished."
#         )
#     )

#     code: Optional[str] = Field(
#         default=None,
#         description=(
#             "The specific PEP8 violation code (e.g., 'E401', 'W293') or a summary "
#             "of the rule broken. Should be null if the status is 'passed'."
#         )
#     )

#     review_status: Optional[Literal["passed", "failed"]] = Field(
#         default=None,
#         description=(
#             "The final result of the PEP8 check. Use 'passed' if the code fully "
#             "conforms to PEP8 or was successfully auto-formatted. Use 'failed' "
#             "if the code contains unresolvable style issues or syntax errors."
#         )
#     )


def reduce_latest(left: str, right: str) -> str:
    return right



class QuizReviewItem(BaseModel):
    question: str = Field(..., description="The text of the question")
    answer_given: str = Field(..., description="The option and text the user provided")
    actual_answer: str = Field(..., description="The correct option and text from the key")
    is_correct: bool = Field(..., description="True if answer_given matches actual_answer, False otherwise")
    reason: str = Field(..., description="Brief explanation of the result")



class QuizToolResponse(BaseModel):
    """
    USE THIS only after BOTH quiz_generator_tool AND quiz_reviewer_tool 
    have been called and returned results successfully.
    ONLY valid when context='valid' AND a clear topic is present in the user query.
    DO NOT USE as a fallback. DO NOT USE if tools were not called.
    """
    decision: Literal["report"] = Field(
        ...,
        description="Always 'report'. Set ONLY after both tools complete successfully."
    )
    reviews: List[QuizReviewItem] = Field(..., description="Question-by-question reviews")
    total_questions: int = Field(..., description="Total number of quiz questions")
    questions_attended: int = Field(..., description="Total number of questions attempted")
    questions_unattended: int = Field(..., description="Total number of questions not attempted")
    correct_answers: int = Field(..., description="Number of correct answers")
    score: int = Field(
        ..., 
        description="Math: (correct_answers divided by questions_attended) times 100. Example: 2/5 is 40.0, not 0."
    )



class OffContextResponse(BaseModel):
    """
    USE THIS for ALL non-execution paths:
      1. context='reject'  → input has no quiz intent (greetings, unrelated, gibberish)
      2. context='incomplete' → input has quiz intent but topic is missing ('generate quiz on', 'quiz about')
    DO NOT USE if context='valid' and a clear topic is present.
    CALLING ANY TOOL when returning this response is FORBIDDEN.
    """
    decision: Literal["reject"] = Field(
        ...,
        description=(
            "Always 'reject'. Covers both off-topic inputs AND incomplete quiz requests. "
            "Use whenever context != 'valid' OR topic is absent."
        )
    )
    response: str = Field(
        ...,
        description=(
            "Explain specifically why the request was rejected and guide the user. "
            "For incomplete: 'You asked to generate a quiz but no topic was provided. "
            "Try: Generate a quiz on World War II.' "
            "For off-topic: 'This doesn't appear to be a quiz request. "
            "Try: Generate a quiz on Python basics.'"
        )
    )


class FinalAgentResponse(BaseModel):
    """
    Two-way union: reject | report.
    'reject' handles ALL non-execution cases (off-topic + incomplete).
    'report' is used ONLY when tools have been called and results are ready.
    """
    output: Union[OffContextResponse, QuizToolResponse] = Field(
        ...,
        discriminator="decision",
        description=(
            "Choose EXACTLY ONE:\n"
            "  'reject' → context is 'reject' or 'incomplete', or topic is missing. NO tools.\n"
            "  'report' → context is 'valid', topic present, both tools called successfully."
        )
    )




class APIResponse(BaseModel):
    message:str 
    status_code:int
    data:dict | str | FinalAgentResponse | QuizToolResponse



class CommonState(AgentState):
     user_query : str
     reply_message:str
     generated_questions: Annotated[str, reduce_latest] 
     answer_key: Annotated[str, reduce_latest]
     current_state:Annotated[str, reduce_latest]
     replied_answer:str
     review_result:QuizToolResponse
     system_prompt:str


