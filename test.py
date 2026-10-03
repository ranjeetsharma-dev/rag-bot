from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic()

reply = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=100,
    messages=[{"role": "user", "content": "Say fuck you in 10 words"}]
)

print(reply.content[0].text)