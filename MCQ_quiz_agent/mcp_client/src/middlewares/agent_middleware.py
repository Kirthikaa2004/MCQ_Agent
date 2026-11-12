from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse,ExtendedModelResponse,HumanInTheLoopMiddleware
from src.prompts.quiz_agent_prompt import QUIZ_AGENT_PROMPT
from src.prompts.review_agent_prompt import REVIEW_AGENT_PROMPT
from src.tools.tool import quiz_generator_tool,quiz_reviewer_tool
from typing import Callable
from src.utils.helper import logger

AGENT_REGISTRY = {
       "quiz_tool":{
              "prompt": QUIZ_AGENT_PROMPT,
              "tools" : [quiz_generator_tool]
       },
       "review_tool":{
              "prompt": REVIEW_AGENT_PROMPT,
              "tools" : [quiz_reviewer_tool]
       }

}
        

# Define outside the class or as a static method
@wrap_model_call()
async def apply_step_config(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    # Logic remains the same
    current_state_key = request.state.get('current_state') or 'quiz_tool'
    print(request.state,current_state_key)
    agent_config = AGENT_REGISTRY[current_state_key]
    
    
    logger.info(f'loaded tools : {agent_config}' )

    print(agent_config,'agent_config')
    if agent_config:
        tools = agent_config.get('tools', [])
        request = request.override(tools=tools)

    return await handler(request)
    

async def hitl_middleware():
        return HumanInTheLoopMiddleware(
        interrupt_on={"quiz_reviewer_tool": {
            "allowed_decisions" : ["approve","edit"]
            }},
        
    )
