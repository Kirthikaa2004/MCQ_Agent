from langchain.tools import tool, ToolRuntime
from src.models.user_model import CommonState,QuizToolResponse
from langchain.agents import create_agent
from langgraph.types import Command
from langchain.agents.structured_output import (
    ToolStrategy,
    StructuredOutputValidationError,
    MultipleStructuredOutputsError,
)
import re
from src.utils.helper import get_llm
import json
from src.repositories.error_repository import ErrorRepository
from src.repositories.database import Database
from langchain.messages import SystemMessage, HumanMessage,ToolMessage
from src.prompts.quiz_agent_prompt import QUIZ_AGENT_PROMPT
from src.prompts.review_agent_prompt import REVIEW_AGENT_PROMPT
from src.utils.custom_app_exception import CustomAppException



@tool
async def quiz_generator_tool(user_query:str,runtime: ToolRuntime[CommonState]):
    """
    Generates multiple-choice questions (MCQs) and an answer key based on a user-provided topic.
    
    This tool leverages an underlying LLM agent to create educational content. It extracts 
    the topic from the state, processes it, and returns a structured set of questions 
    along with their correct answers.
    


    Args:
        user_query: A string containing the topic, desired difficulty (easy/medium/hard), 
                   and the number of questions to generate.

    Returns:
        Command: Updates the state with 'generated_question', 'answer_key', 
        and sets 'current_state' to 'quiz_tool'.
    """


    try:

        llm = await get_llm(err_repo=ErrorRepository(Database()))
        agent = create_agent(
            model=llm,
            system_prompt=SystemMessage(content=QUIZ_AGENT_PROMPT),
            tools = []
        )

        response = await agent.ainvoke({
            "messages": [HumanMessage(content=user_query)]
        })

        # Accessing the structured output from the agent response
        agent_response = response['messages'][-1].content
        print(agent_response,'agent response')
        final_response = json.loads(agent_response)
        print(response,'tool response')

        print('special_tool_id' ,runtime.tool_call_id )
        
        print(final_response.get('questions'),'question')
        print(final_response.get('answer_key'),'answer')

        quiz_content_for_llm = {
        "generated_quiz": final_response.get('questions'),
        "status": "GENERATION_COMPLETE",
        "next_action": "The quiz has been generated and displayed. Now, immediately call the quiz_reviewer_tool to prepare the evaluation environment."
        }

        updated_state = {
            "messages": [
                ToolMessage(
                    # The LLM needs to see the actual content here to repeat it to the user
                    content=quiz_content_for_llm, 
                    tool_call_id=runtime.tool_call_id
                )
            ],
            "generated_questions": final_response.get('questions'),
            "answer_key": final_response.get('answer_key'),
            "current_state": "review_tool"
        }

        return Command(update=updated_state)
    except CustomAppException:
        raise
    except Exception as e:
        raise CustomAppException(
            err_code="QUIZ_GENERATOR_ERR",
            status_code=500,
            message=f"Err at quiz_generator_tool : {str(e)}"
        )


@tool
async def quiz_reviewer_tool(user_answer:str , runtime: ToolRuntime[CommonState]):
    """
    Evaluates the user's submitted answers against the correct answer key.
    
    Args:
        user_answer (str): The answer string provided by the user via the resume command.
        runtime (ToolRuntime[CommonState]): The current agent state containing the 
            'answer_key' and 'generated_question'.

    Logic:
        The tool uses the provided 'user_answer' and compares it with 'answer_key' 
        stored in the state. It uses an LLM to analyze correctness and provide 
        feedback/reasoning for each answer.
    
    Returns:
        Command: Updates the state with 'review_result' (evaluation objects), 
        'replied_answer' (to persist the input), and sets 'current_state' to 'review_tool'.
    """
    try:

        print('user_answer',user_answer)
        print(runtime.state,'state')
        state = runtime.state

        # The error suggests 'state' or one of these variables is an AIMessage object
        # If generated_question was stored as a message, we need the .content
        # generated_question = state['generated_question']
        # if hasattr(generated_question, 'content'):
        #     generated_question = generated_question.content

        # answer_key = state.get('answer_key')
        # if hasattr(answer_key, 'content'):
        #     answer_key = answer_key.content
        

        generated_question = runtime.state['generated_questions']
        answer_key = runtime.state['answer_key']
    
        


        message = (
            f"Generated Question:\n{generated_question}\n\n"
            f"Correct Answer Key:\n{answer_key}\n\n"
            f"User's Replied Answer:\n{user_answer}"
        )

        print(message,'message')
        

        llm = await get_llm(err_repo = ErrorRepository(Database()))
        agent = create_agent(
            model=llm,
            response_format=ToolStrategy(
                schema=QuizToolResponse,
                tool_message_content="Structured report captured successfully.",
                handle_errors=True,
            ),
            system_prompt=SystemMessage(content=REVIEW_AGENT_PROMPT)
        )
        
        response = await agent.ainvoke({
            "messages": [HumanMessage(content=message)]
        })

        # Assuming the agent returns the JSON in the content field
        
        print(response,'full_resp')
        print(response.get('structured_response'),'dddsss')
        agent_response = response.get('structured_response')
        
        print(agent_response,'review tool response')
        print('compleled')

        review_content_for_llm = {
            "review_generated" : agent_response,
            "status": "REVIEW_COMPLETE",
            "next_action": "The quiz answers has been reviewed successfully. Display these structured response directly to the client without modifying this structured response "
        }

        updated_state = {
            "messages": [
                ToolMessage(
                    # The LLM needs to see the actual content here to repeat it to the user
                    content=review_content_for_llm, 
                    tool_call_id=runtime.tool_call_id
                )
            ],
            "review_result":agent_response,
            "current_state": "quiz_tool"
        }


        return Command(
            update = updated_state
        )
    
    except CustomAppException:
        raise
    except Exception as e:
        raise CustomAppException(
            err_code="QUIZ_REVIEWER_ERR",
            status_code=500,
            message=f"Err at quiz_reviewer_tool : {str(e)}"
        )




    



