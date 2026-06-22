import json
from evals.schemas import AgentOutput, Grounding
from core.llm_client import complete_with_tools

MAX_ITERS = 10

def run_agent(case_id: str, messages: list[dict], tools: list[dict], tool_functions: dict) -> AgentOutput:
    
    for i in range(MAX_ITERS):
        message = complete_with_tools(messages,tools)
        if not message.tool_calls:
            break
        
        messages.append(message)
        
        for tool_call in message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            if name == "submit":
                raw_grounding = args.pop("grounding")
                if isinstance(raw_grounding, str):
                    raw_grounding = json.loads(raw_grounding)
                grounding = Grounding(**raw_grounding)
                return AgentOutput(case_id=case_id, grounding=grounding, **args)

            else:
                result = tool_functions[name](**args)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result)
                    }
                )

    return AgentOutput(
    case_id=case_id,
    action="escalate",
    driver_type="none",
    magnitude=0.0,
    description="Agent failed to submit within max iterations.",
    confidence=0.0,
    grounding=Grounding(transaction_ids=[], signal="max iterations reached")
)
                



    


    

