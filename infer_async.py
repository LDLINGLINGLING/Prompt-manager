import grpc
# import grpc_model.model_service_pb2
from grpc_model import model_service_pb2
# import grpc_model.model_service_pb2_grpc
from grpc_model import model_service_pb2_grpc
import asyncio
import uuid
from utils import model_config, model_service_address


async def predict(stub, prompt_template, input_dict, model_name, top_p=0.7, temperature=0.7, repetition_penalty=1.0):
    history = [
        model_service_pb2.ChatMessage(
            role="user",
            prompt_template=prompt_template,
            inputs=input_dict
            )
    ]
    _id = str(uuid.uuid4())
    request = model_service_pb2.ChatCompletionRequest(
        id=_id,
        model=model_name,
        history=history,
        response_format="json",
        temperature=temperature,
        top_p=top_p,
        top_k=-1,
        max_tokens=4096,
        n=1,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        repetition_penalty=repetition_penalty,
        seed=42,
        stop=[],
        timeout=180,
        stream=False,
        tools='',
        tool_choice='',
    )
    response = await stub.Chat(request)
    return response.choices[0].messages.content, history


async def main(prompt_template, input_dict, model_name, top_p=0.7, temperature=0.7, repetition_penalty=1.0, model_name_v=None):
    if model_name_v is not None:
        model_name = model_name_v
    else:
        model_name = model_config[model_name]
    async with grpc.aio.insecure_channel(model_service_address, options=[('grpc.idle_timeout', 180)]) as channel:
        model_service_stub = model_service_pb2_grpc.ModelServiceStub(channel)
        # return await predict(model_service_stub, prompt_template, input_dict, model_name)
        return await predict(model_service_stub, prompt_template, input_dict, model_name, top_p=float(top_p), temperature=float(temperature), repetition_penalty=float(repetition_penalty))
