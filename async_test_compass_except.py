import gradio as gr 
# import mdtex2htmls
import pandas as pd
import io
# import grpc
# import model_service_pb2
# import model_service_pb2_grpc
import asyncio
import uuid
from datetime import datetime
from process_file import process_files, read_text, read_xlsx, download_xlsx, dispaly_top5_rows
from infer import main
from utils import _parse_text
from utils import model_config
import json
import aiofiles

gsm8k_list = []
math_list = []
mmlu_list = []
gsm8k_exist_list = []
math_exist_list = []
mmlu_exist_list = []


with open('/data/czyd/gradio_ui/评测数据/result/gsm8k.jsonl','r',encoding='utf-8') as file:
    for line in file:
        obj = json.loads(line)
        if obj['prediction'] == 'this line is error':
            gsm8k_list.append(obj)
        else:
            gsm8k_exist_list.append(obj)

with open('/data/czyd/gradio_ui/评测数据/result/math1.jsonl','r',encoding='utf-8') as file:
    for line in file:
        obj = json.loads(line)
        if obj['prediction'] == 'this line is error':
            math_list.append(obj)
        else:
            math_exist_list.append(obj)
        
with open('/data/czyd/gradio_ui/评测数据/result/mmlu.jsonl','r',encoding='utf-8') as file:
    for line in file:
        obj = json.loads(line)
        if obj['prediction'] == 'this line is error':
            mmlu_list.append(obj)
        else:
            mmlu_exist_list.append(obj)


model_name = "mb-large-80b"
top_p = 1
temperature = 0
repetition_penalty = 1
 
async def process_item_with_semaphore(index,item,semaphore):
    async with semaphore:
        try:
            if item['prediction'] == """this line is error""":
                _query = item['prompt'][0]['content']
                res = await main(prompt_template=_query, input_dict={}, model_name=model_name, top_p=float(top_p), temperature=float(temperature), repetition_penalty=float(repetition_penalty),model_name_v=model_name)
                item['prediction'] = res[0]
                print(res[0])
                return item
            else:
                return item
        except Exception as e:
            print(e)
            return item




async def process_test(file_list,save_path,max_concurrent_tasks):
    
        semaphore = asyncio.Semaphore(max_concurrent_tasks)
        tasks = []
        no_error_lines = []
        for index,i in enumerate(file_list):
            task = asyncio.create_task(process_item_with_semaphore(index,i,semaphore))
            tasks.append(task)
        predictions = await asyncio.gather(*tasks)
        predictions.extend(no_error_lines)
        async with aiofiles.open(save_path,'w',encoding='utf-8') as file:
            for item in predictions:
                #print(item['prediction'])
                await file.write(json.dumps(item,ensure_ascii=False)+'\n')

        
# asyncio.run(process_test(math_list,'/data/czyd/gradio_ui/评测数据/result/math.jsonl',5
# ))
# with open('/data/czyd/gradio_ui/评测数据/result/math.jsonl','a',encoding='utf-8') as file:
#     for item in math_exist_list:
#         file.write(json.dumps(item,ensure_ascii=False)+'\n')

asyncio.run(process_test(gsm8k_list,'/data/czyd/gradio_ui/评测数据/result/gsm8k.jsonl',2))
with open('/data/czyd/gradio_ui/评测数据/result/gsm8k.jsonl','a',encoding='utf-8') as file:
    for item in gsm8k_exist_list:
        file.write(json.dumps(item,ensure_ascii=False)+'\n')
#asyncio.run(process_test(mmlu_list,'/data/czyd/gradio_ui/评测数据/result/mmlu.jsonl',5))


