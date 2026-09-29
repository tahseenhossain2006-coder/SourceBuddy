import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv(
    r"C:\Users\maina\OneDrive\Desktop\sourceAI\sourceai\.env"
)

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError("GROQ_API_KEY is missing")

print("API key loaded:", bool(api_key))

client = Groq(
    api_key=api_key
)

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "user",
            "content": "Say exactly: GPT-OSS is working."
        }
    ],
)

print("\nGPT-OSS RESPONSE:\n")
print(response.choices[0].message.content)