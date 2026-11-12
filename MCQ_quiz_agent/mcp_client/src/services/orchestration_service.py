from langgraph.graph import StateGraph, END
from src.models.user_model import CommonState
from src.utils.helper import get_llm
from fastapi import Depends
import ast
import json
import re
from src.models.user_model import CommonState,FinalAgentResponse
from src.prompts.orchestrator_prompt import ORCHESTRATOR_PROMPT,CLASSIFIER_PROMPT
from langchain.agents.structured_output import (
    ToolStrategy
)
from src.prompts.quiz_agent_prompt import QUIZ_AGENT_PROMPT
from src.prompts.review_agent_prompt import REVIEW_AGENT_PROMPT
from langchain_core.messages import SystemMessage,HumanMessage,ToolMessage
from src.utils.custom_app_exception import CustomAppException
from typing import Literal,Callable
from langchain.agents.middleware import HumanInTheLoopMiddleware
from src.utils.helper import logger,get_llm
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from src.tools.tool import quiz_generator_tool,quiz_reviewer_tool
from langchain.agents import create_agent

from langgraph.types import Command
from src.repositories.error_repository import ErrorRepository
from src.repositories.database import Database
from settings import config
from src.middlewares.agent_middleware import apply_step_config


# AGENT_REGISTRY = {
#        "quiz_tool":{
#               "prompt": QUIZ_AGENT_PROMPT,
#               "tools" : [quiz_generator_tool]
#        },
#        "review_tool":{
#               "prompt": REVIEW_AGENT_PROMPT,
#               "tools" : [quiz_reviewer_tool]
#        }
# }


# @wrap_model_call(state_schema=CommonState)
# async def apply_step_config(
#     request: ModelRequest,
#     handler: Callable[[ModelRequest], ModelResponse],
# ) -> ExtendedModelResponse:
#     # 1. Get the current state from the request
#     # Ensure 'current_state' is actually in your state_schema
#     current_state_key = request.state.get('current_state', 'quiz_tool')

#     # 2. Lookup config from your registry
#     agent_config = AGENT_REGISTRY.get(current_state_key)
#     if not agent_config:
#         # Fallback to prevent empty tool/prompt errors
#         return await handler(request)

#     tools = agent_config.get('tools', [])

#     # 3. Override the request with dynamic context
#     # Note: Use system_prompt if your middleware supports prompt overriding
#     request = request.override(
#         tools=tools
#     )

#     # 4. CRITICAL: Await and return the handler
#     response = await handler(request)
#     return response


class OrchestratorService:

    def __init__(self):
        self.system_prompt = ORCHESTRATOR_PROMPT


    async def run_agent(self,user_prompt:str,thread_id:str,err_repo:ErrorRepository):

        try:
            DATABASE_URL = (
                    f"postgresql://{config.db_username}:{config.db_password}"
                    f"@{config.db_host}:{config.db_port}/{config.db_name}"
                    )
            logger.info("run_agent is triggered...")
            async with AsyncPostgresSaver.from_conn_string(DATABASE_URL) as checkpointer:

                await checkpointer.setup()

                logger.info('Created Checkpointer')
                llm = await get_llm(err_repo= ErrorRepository(Database()))
                messages = [
                    SystemMessage(content = CLASSIFIER_PROMPT),
                    HumanMessage(content=user_prompt)
                ]
                get_context = await llm.ainvoke(messages)
                print(get_context.content,'context')
                agent = create_agent(
                    model=llm,
                    system_prompt=SystemMessage(content = self.system_prompt),
                    state_schema=CommonState,
                    tools = [quiz_generator_tool,quiz_reviewer_tool],
                    middleware=[
                        apply_step_config,
                        HumanInTheLoopMiddleware(
                            interrupt_on={"quiz_reviewer_tool": {
                                "allowed_decisions" : ["approve","edit"]
                                }},
                             
                        )
                    ],
                    checkpointer=checkpointer,
                    response_format=ToolStrategy(
        schema=FinalAgentResponse,
        tool_message_content="Structured report captured successfully.",
        handle_errors=True,

    ),

                )

                session_config = {
                    "configurable":{
                        "thread_id":str(thread_id)
                    }
                }

                print(user_prompt,self.system_prompt,'fknfd')
                user_message =  user_prompt  + "\n" + get_context.content
                print(user_message,'user')
                response = await agent.ainvoke(
                    {
                    "messages": HumanMessage(content = user_message)},
                    config = session_config
                    )
                print(response, 'full_response')
                    
                print(response['messages'][-1].content,'response')

                
                if '__interrupt__' in response:

                    quiz_tool_msg = next(
                        (msg for msg in reversed(response['messages']) 
                        if isinstance(msg, ToolMessage) and msg.name == 'quiz_generator_tool'), 
                        None
                    )

                    if quiz_tool_msg:
                        # 2. The content is a string-encoded dictionary
                        # We can parse it to make it readable
                        
                            content_data = ast.literal_eval(quiz_tool_msg.content)
                            quiz_list = content_data.get('generated_quiz', [])
                            
                            print("\n---  GENERATED QUIZ ---")
                            for q in quiz_list:
                                print(f"\nQ{q['question_number']}: {q['generated_question']}")
                                for opt, val in q['options'].items():
                                    print(f"  {opt}) {val}")
                            print("\n--------------------------")

                    
        # 3. Handle the User Answer for Resume
                    user_answer = input("\nEnter your answers (e.g., 1A, 2B...): ")

                    print(user_answer)
                    edited_args = {"user_answer":user_answer}
                    response = await agent.ainvoke(
                    Command(
                        resume={
                            "decisions": [
                                {
                                    "type": "edit",
                                    "edited_action": {
                                        "name": "quiz_reviewer_tool", # Must provide the tool name
                                        "args": edited_args      # Your modified arguments
                                    }
                                }
                            ]
                        }
                    ),
                    config=session_config,
                    version="v2"
            )
                    print('came')
                    print(response,'ssss')

                    agent__response = response.value['messages']
                    print(agent__response,'temp')
                    
                    print(response.value['review_result'],'result_Review')


                    return response.value['review_result']
                
                return response.get('structured_response')

            
        except CustomAppException:
            raise
        except Exception as e:
            print(e)
            logger.info(f"err raised at run_agent...: {str(e)}")

            await err_repo.add_error(
                message=f"Err at creating orchestrator agent : {str(e)}",
                file_name="orchestration_service",
                function_name="run_agent"
            )
            return CustomAppException(
                err_code="RUN_MAIN_AGENT",
                status_code=500,
                message=f"Err at main agent : {str(e)}"
            )

def get_orchestrator_service():
    return OrchestratorService()