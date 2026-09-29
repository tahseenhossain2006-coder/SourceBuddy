import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv(
    r"C:\Users\maina\OneDrive\Desktop\sourceAI\sourceai\.env"
)

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError("GROQ_API_KEY is missing")

client = Groq(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1",
)

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "system",
            "content": "You are a helpful AI assistant."
        },
        {
            "role": "user",
            "content": "Explain what a supplier intelligence agent does in 3 sentences."
        }
    ],
    reasoning_effort="medium",
    include_reasoning=False,
)

print(response.choices[0].message.content)