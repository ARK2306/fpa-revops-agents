import json
from evals.schemas import AgentOutput, Grounding
from core.llm_client import complete_with_tools
from langfuse import observe, propagate_attributes
from pydantic import ValidationError
from dataclasses import dataclass

MAX_ITERS = 10


@dataclass
class RunUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    llm_calls: int = 0

    def add(self, usage) -> None:
        self.prompt_tokens += usage.prompt_tokens
        self.completion_tokens += usage.completion_tokens
        self.cost_usd += getattr(usage, 'cost', 0.0)
        self.llm_calls += 1
        

@observe()
def run_agent(case_id: str, messages: list[dict], tools: list[dict], tool_functions: dict) -> AgentOutput:
    with propagate_attributes(
        trace_name=case_id,        
        session_id=case_id,
        tags=["fpa"],
    ):
            usage_acc = RunUsage()
    
            for i in range(MAX_ITERS):
                message, usage = complete_with_tools(messages,tools)
                usage_acc.add(usage)

                if not message.tool_calls:
                    break
                
                messages.append(message)
                
                for tool_call in message.tool_calls:
                    name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)

                    if name == "submit":
                        try:
                            raw_grounding = args.pop("grounding")
                            if isinstance(raw_grounding, str):
                                raw_grounding = json.loads(raw_grounding)
                            grounding = Grounding(**raw_grounding)
                            output = AgentOutput(case_id=case_id, grounding=grounding, **args)
                        except (ValidationError, KeyError, json.JSONDecodeError) as e:
                            return AgentOutput(
                                case_id=case_id,
                                action="escalate",
                                driver_type="none",
                                magnitude=0.0,
                                confidence=0.0,
                                description=f"Malformed output from model: {e}",
                                grounding=Grounding(transaction_ids=[], signal="validation_failed")
                            ), usage_acc
                        if output.action in ("flag", "escalate") and not output.grounding.transaction_ids:
                            return AgentOutput(
                                case_id=case_id,
                                action="escalate",
                                driver_type=output.driver_type,
                                magnitude=output.magnitude,
                                confidence=0.3,
                                description=output.description + " [guardrail: no transaction IDs cited — escalated for human review]",
                                grounding=Grounding(transaction_ids=[], signal="grounding_guardrail_triggered")
                            ), usage_acc
                        return output, usage_acc

                    else:
                        try:
                            result = tool_functions[name](**args)
                        except (TypeError, KeyError) as e:
                            result = {"error": f"Tool call failed: {e}"}
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result)
                        })

            return AgentOutput(
            case_id=case_id,
            action="escalate",
            driver_type="none",
            magnitude=0.0,
            description="Agent failed to submit within max iterations.",
            confidence=0.0,
            grounding=Grounding(transaction_ids=[], signal="max iterations reached")
        ), usage_acc
                    



        


        

