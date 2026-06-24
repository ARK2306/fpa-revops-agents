from dotenv import load_dotenv
from langfuse.openai import OpenAI
import os

load_dotenv()

MODEL_1 = "deepseek/deepseek-v4-flash"
MODEL_2 = "nex-agi/nex-n2-pro:free"
MODEL_3 = "poolside/laguna-m.1:free"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

def complete(
        messages: list[dict],
        model: str = MODEL_1,
        temperature: float = 0.0,
        max_tokens: int = 1000
) -> str:
    completion = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=messages,
        max_tokens=max_tokens

    )
    return completion.choices[0].message.content

def complete_with_tools(
    messages: list[dict],
    tools: list[dict],
    model: str = MODEL_1,
    temperature: float = 0.0,
    max_tokens: int = 3000
) -> object:
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=messages,
        tools=tools,
        max_tokens=max_tokens
    )
    return response.choices[0].message

if __name__ == "__main__":
    print(complete([{"role": "user", "content": "what is the meaning of life, answer in 1 line"}]))

    


