from pydantic import BaseModel
from datetime import date
from typing import Literal

class TransactionInput(BaseModel):
    transaction_id: str
    date: date
    amount: float
    description: str

class CaseInput(BaseModel):
    period: str
    account_id: str
    budget: float
    transactions: list[TransactionInput]

class Grounding(BaseModel):
    transaction_ids: list[str]
    signal: str

class ExpectedOutput(BaseModel):
    action: Literal["flag","do_nothing","escalate"]
    driver_type: Literal["price_change", "one_time_item", "volume_change", "timing_accrual", "data_error", "none"]
    magnitude: float
    description: str
    grounding: Grounding

class GoldenCase(BaseModel):
    case_id: str
    case_type: str
    input: CaseInput
    expected_output: ExpectedOutput

class AgentOutput(BaseModel):
    case_id: str
    action: Literal["flag", "do_nothing", "escalate"]
    driver_type: Literal["price_change", "one_time_item", "volume_change", 
                         "timing_accrual", "data_error", "none"]
    magnitude: float
    description: str
    grounding: Grounding
    confidence: float

class LiveCaseInput(BaseModel):
    period: str
    account_id: str
    budget: float


