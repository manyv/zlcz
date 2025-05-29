from fastapi import FastAPI, Request
from sse_starlette import EventSourceResponse
from pydantic import BaseModel
from openai import OpenAI

# 工具定义
tools = [{"type": "builtin_function", "function": {"name": "$web_search"}}]

# Chat处理函数，动态接收client
def chat(messages, client):
    # 第一步：获取工具调用
    completion = client.chat.completions.create(
        model="moonshot-v1-128k", messages=messages,
        temperature=0.3, tools=tools
    )

    tool_call = completion.choices[0].message.tool_calls[0]
    messages.extend([completion.choices[0].message, {
        "role": "tool", "content": tool_call.function.arguments,
        "name": "$web_search", "tool_call_id": tool_call.id
    }])

    # 第二步：流式响应
    web_search = client.chat.completions.create(
        model="moonshot-v1-128k", messages=messages,
        temperature=0.2, tools=tools, stream=True
    )
    for chunk in web_search:
        print(chunk)
        yield chunk.model_dump_json()

# FastAPI 应用
fastapi = FastAPI()

# Pydantic 模型用于接收请求体
class ChatRequest(BaseModel):
    api_key: str
    content: str

# 接口：用户输入和用户 API Key
@fastapi.post("/v1/chat/completions")
async def web_search(request: ChatRequest):
    # 动态创建 client
    client = OpenAI(
        base_url="https://api.moonshot.cn/v1",
        api_key=request.api_key,
    )

    messages = [
        {"role": "system", "content": "你是 Kimi。"},
        {"role": "user", "content": request.content}
    ]
    generate = chat(messages, client)
    return EventSourceResponse(generate, media_type="text/event-stream")

# 本地运行
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(fastapi, host="localhost", port=8000)
