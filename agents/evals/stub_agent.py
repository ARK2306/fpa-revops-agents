from evals.schemas import CaseInput, AgentOutput, Grounding

def stub_agent(case: CaseInput) -> AgentOutput:
    return AgentOutput(
        case_id="",
        action="do_nothing",
        driver_type="none",
        magnitude=0.0,
        description="stub: always do nothing",
        grounding=Grounding(transaction_ids=[], signal="stub")
    )