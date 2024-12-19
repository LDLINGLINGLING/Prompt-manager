# vllm serve /DATA/disk0/ld/ld_model_pretrain/Qwen2.5-3B-Instruct  --dtype auto --api-key token-abc123

from openai import OpenAI

# Modify OpenAI's API key and API base to use vLLM's API server.
openai_api_key = "token-abc123"
openai_api_base = "http://localhost:8000/v1"

client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key=openai_api_key,
    base_url=openai_api_base,
)

models = client.models.list()
model = models.data[0].id
print(model)
def main():
    chat_completion = client.chat.completions.create(
        messages=[{
            "role": "system",
            "content": "You are a helpful assistant."
        }, {
            "role": "user",
            "content": "你好"
        }],
        model=model,
        top_p=1,
        max_tokens=4096,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        seed=42,
        temperature=0.7
    )

    return chat_completion.choices[0].message.content
print(main())