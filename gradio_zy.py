import gradio as gr 
# import mdtex2htmls
import pandas as pd
import io
import os
# import grpc
# import model_service_pb2
# import model_service_pb2_grpc
import asyncio
import uuid
from datetime import datetime
from process_file import process_files, read_text, read_xlsx, download_xlsx, dispaly_top5_rows,save_prompt_batch,client,model,models,model_config
from infer import main
from utils import _parse_text


def get_file_names():
    file_names = []
    directory1 = './save_prompt_batch'
    for f in os.listdir(directory1):
        if os.path.isfile(os.path.join(directory1,f)):
            file_names.append(f)
    directory2 = './save_prompt_chat'
    for f in os.listdir(directory2):
        if os.path.isfile(os.path.join(directory2,f)):
            file_names.append(f)
    print(file_names)
    return gr.update(choices=file_names)

def read_file_content(filename):
    directory1 = './save_prompt_batch'
    directory2 = './save_prompt_chat'
    if filename in os.listdir(directory1):
        with open(os.path.join(directory1,filename),'r',encoding='utf-8') as f:
            return f.read()
    
    elif filename in os.listdir(directory2):
        with open(os.path.join(directory2,filename),'r',encoding='utf-8') as f:
            return f.read()
    else:
        return '该文件不存在'

def read_prompt_from_server(directory,seach_key_word):
    if len(directory) < 3:
        directory = './save_prompt_batch'
    html_content_head = ''
    html_content_tail = ''
    key_flag = False
    for filename in os.listdir(directory):
        if filename.endswith('.txt'):
            file_path = os.path.join(directory,filename)
            with open(file_path,'r',encoding='utf-8') as  file:
                content = file.read()
            if seach_key_word in filename or seach_key_word in content:
                key_flag = True
                highlight_filename = filename.replace(seach_key_word,f'<mark>{seach_key_word}</mark>')
                highlight_content = content.replace(seach_key_word,f'<mark>{seach_key_word}</mark>')
                html_content_head += f"<b>文件名：</b>{highlight_filename}<br><b>内容：</b><pre>{highlight_content}</pre><hr>"
            else:
                html_content_tail += f"<b>文件名：</b>{filename}<br><b>内容：</b><pre>{content}</pre><hr>"
    if key_flag:
        return html_content_head
    return html_content_head+html_content_tail

def postprocess(self, data):
    if data is None:
        return []
    
    for i, (message, response) in enumerate(data):
        # data[i] = (
        #     None if message is None else mdtex2html.convert(message),
        #     None if response is None else mdtex2html.convert(response)
        # )
        data[i] = (
            None if message is None else _parse_text(message),
            None if response is None else _parse_text(response)
        )
    return data

gr.Chatbot.postprocess = postprocess


css = """
.custom-dataframe.column {
    width: 100px;
}
"""
gr.Markdown(f"<style>{css}</style")

def _launch_demo():
    def predict_(_query, _chatbot, max_tokens,_task_history, model_choice, top_p, temperature, repetition_penalty):
        _chatbot = list(_chatbot)
        _chatbot.append((_query, ""))
        res = main(client=client,input_dic={},model=model,query=_query,top_p=top_p,max_tokens=max_tokens,presence_penalty=repetition_penalty,temperature=temperature)
        
        #res = asyncio.run(main(prompt_template=_query, input_dict={}, model_name=model_choice, top_p=float(top_p), temperature=float(temperature), repetition_penalty=float(repetition_penalty)))
        full_response = res
        print(_query, '  \n',full_response)
        _chatbot[-1] = (_query, full_response)

        #_task_history = list(_task_history)
        _task_history.append((_query, full_response))
        print('task_history',_task_history)
        return _chatbot
    def save_prompt_chat(_query,prompt_task_name,task_history):
        time_stamp = str(datetime.now().strftime('%Y%m%d%H%M%S%f'))
        if not os.path.exists('save_prompt_chat'):
            os.mkdir('save_prompt_chat')
        file_path = 'save_prompt_chat/{}_{}_.txt'.format(prompt_task_name, time_stamp) 
        if len(task_history)>=1:       
            prompt,_ = task_history[-1]
            with open(file_path,'w',encoding='utf-8') as file:
                file.write(prompt)
        else:
            prompt = _query
            with open(file_path,'w',encoding='utf-8') as file:
                file.write(_query)
            
        out_put = '输入作为提示词保存到{}'.format(file_path)
        
        #temaple_text = out_put
        return out_put
        
    # def predict_(_query, _chatbot, _task_history, model_choice, top_p, temperature, repetition_penalty):
    #     _chatbot = list(_chatbot)
    #     _chatbot.append((_parse_text(_query), ""))

    #     res = asyncio.run(main(prompt_template=_query, input_dict={}, model_name=model_choice, top_p=float(top_p), temperature=float(temperature), repetition_penalty=float(repetition_penalty)))
    #     full_response = _parse_text(res[0])

    #     _chatbot[-1] = (_parse_text(_query), _parse_text(full_response))

    #     _task_history.append((_query, full_response))

    #     return _chatbot


    def regenerate(_chatbot, _task_history, max_tokens,model_choice, parm_top_p, parm_temperture, parm_repetition_penalty):
        if not _task_history:
            return
        
        item = _task_history.pop(-1)
        _chatbot.pop(-1)

        return predict_(item[0], _chatbot, max_tokens,_task_history, model_choice, top_p=parm_top_p, temperature=parm_temperture, repetition_penalty=parm_repetition_penalty)


    def reset_user_input():
        return gr.update(value="")


    def reset_state(_chatbot, _task_history):
        _task_history.clear()
        _chatbot.clear()
        return _chatbot
    
    def display_success_message(message):
        import time
        time.sleep(3)
        return ''


    with gr.Blocks() as demo:

        with gr.Tab('对话'):
            chatbot = gr.Chatbot(label='Chat', elem_classes="control-height")
            query = gr.Textbox(lines=2, label='Input')
            task_history = gr.State([])
            #temaple_text = gr.Textbox(label='系统提示')

            with gr.Row():
                task_name = gr.Textbox(label="任务名称",placeholder="任务名称，可以自定义",value='Agent对话')
                empty_btn = gr.Button("Clear History （清除历史）")
                submit_btn = gr.Button("Submit（发送）")
                regen_btn = gr.Button("Regenerate（重试）")
                save_btn = gr.Button('Save prompt to server （保存提示词到服务器）')
            success_message = gr.Markdown("")

            
            model_choice = gr.Radio(
                choices = list(model_config.keys()),
                label = '请选择一个模型',
                value = list(model_config.keys())[0]
            )

            parm_top_p = gr.Textbox(label="top_p输入参数", placeholder='top_p在这里输入参数', value=0.85)
            parm_temperture = gr.Textbox(label="temperture输入参数", placeholder='temperture在这里输入参数', value=0.8)
            parm_repetition_penalty = gr.Textbox(label="重复惩罚输入参数", placeholder='temperture在这里输入参数', value=1.02)
            parm_max_tokens = gr.Textbox(label="max_tokens输入参数",placeholder="max_tokens在这里输入参数",value = 4096)


            submit_btn.click(predict_, [query, chatbot, parm_max_tokens,task_history,model_choice, parm_top_p, parm_temperture, parm_repetition_penalty], [chatbot], show_progress=True)
            save_btn.click(save_prompt_chat, [query,task_name,task_history], [success_message], show_progress=True)
            success_message.change(display_success_message,[success_message],[success_message],show_progress=False)

            submit_btn.click(reset_user_input, [], [query])
            empty_btn.click(reset_state, [chatbot, task_history], outputs=[chatbot], show_progress=True)
            regen_btn.click(regenerate, [chatbot, task_history, model_choice, parm_top_p, parm_temperture, parm_repetition_penalty], [chatbot], show_progress=True)


        with gr.Tab('文档'):
            gr.Markdown("# 同时上传 TXT 和 XLSX 文件并处理示例")
        
            # 上传按钮放在文本框下面
            with gr.Column():
                upload_txt_button = gr.UploadButton("上传 提示词TXT 文件", file_types=[".txt"])
                output_txt = gr.Textbox(label="TXT 文件内容", lines=10, interactive=True, max_lines=10)
                upload_txt_button.upload(read_text, upload_txt_button, output_txt)
                save_prompt_btn = gr.Button("保存提示词到服务器")
            batch_success_message = gr.Markdown("")
            
            # XLSX 文件上传与显示
            with gr.Column():
                upload_xlsx = gr.UploadButton("上传 XLSX 文件", file_types=[".xlsx"])
                output_xlsx = gr.Dataframe(label="XLSX 文件内容", interactive=True, elem_classes='custom-dataframe')
                # display_df = gr.Dataframe(label="XLSX 文件内容", interactive=True)
                # output_xlsx = gr.State()
                upload_xlsx.upload(read_xlsx, upload_xlsx, output_xlsx)
                # upload_xlsx.upload(lambda file: (read_xlsx(file), dispaly_top5_rows(read_xlsx(file))), upload_xlsx, [output_xlsx, display_df])
            
            # 处理按钮
            with gr.Row():  
                model_selection_button = gr.Radio(
                    choices=list(model_config.keys()),
                    label="请选择一个模型",
                    value = list(model_config.keys())[0]
                )
                model_selection_text = gr.Textbox(label="模型名称",placeholder="如果模型按钮没有你要的模型，在此输入模型名称",value='') 
            with gr.Row():    
                task_name = gr.Textbox(label="任务名称",placeholder="任务名称，可以自定义",value='Agent对话')
                
                param_input_top_p = gr.Textbox(label="top_p输入参数", placeholder="top_p在这里输入参数",value=0.85)
                # 参数输入框
                param_input_temperture = gr.Textbox(label="temperture输入参数",placeholder="temperture在这里输入参数",value = 0.8)
                param_input_max_tokens = gr.Textbox(label="max_tokens输入参数",placeholder="max_tokens在这里输入参数",value = 4096)
                param_input_repetition = gr.Textbox(label="重复惩罚输入参数",placeholder="重复惩罚在这里输入参数",value = 1.02)
                pos_result = gr.Textbox(label="生成结果的列名后缀",placeholder="生成结果列名的后缀",value = '_'+datetime.now().strftime("%Y%m%d%H%M"))
                


            process_button = gr.Button("处理文件")

            # 处理后的输出
            processed_txt = gr.Textbox(label="替换后的 TXT 内容", lines=10)
            processed_xlsx = gr.Dataframe(label="生成结果后的 XLSX 内容")

            # 绑定处理按钮事件

            save_prompt_btn.click(save_prompt_batch, [output_txt,task_name], [batch_success_message])
            batch_success_message.change(display_success_message,[batch_success_message],[batch_success_message],show_progress=False)

            process_button.click(
                fn=process_files,
                inputs=[output_txt, output_xlsx, param_input_top_p, param_input_temperture,param_input_max_tokens,param_input_repetition, model_selection_text,model_selection_button,task_name,pos_result], 
                outputs=[processed_txt, processed_xlsx]
            )

            download_button = gr.Button("下载处理后的 XLSX 文件")
            download_button.click(
                fn=download_xlsx,
                inputs=[processed_xlsx,task_name],
                outputs=gr.File(label="下载 XLSX 文件")
            )
        with gr.Tab('提示词查找'):
            with gr.Column():
                seach_key_word = gr.Textbox(label='搜索关键词',value = '')
                prompt_btn1 = gr.Button('展示提示词模板')
                prompt_btn2 = gr.Button('展示历史提示词')
                prompt_display = gr.HTML(label = '所有提示词模板展示')
                
                # with gr.Row():
                path1 = gr.Textbox(label="提示词模板地址",value ='./save_prompt_batch' ,visible = False)
                path2 = gr.Textbox(label="历史提示词地址",value = './save_prompt_chat', visible = False)
                prompt_btn1.click(read_prompt_from_server,[path1,seach_key_word],[prompt_display])
                prompt_btn2.click(read_prompt_from_server,[path2,seach_key_word],[prompt_display])
        file_names = []
        with gr.Tab('提示词管理'):
            with gr.Column():
                #get_file_names('./save_prompt_batch')
                flush_prompt_file = gr.Button('获取已存在的prompt')
                file_selector = gr.Dropdown(choices=file_names,label="选择一个prompt",interactive=True)
                flush_prompt_file.click(fn=get_file_names,inputs=[],outputs=file_selector)
                file_content_display = gr.Textbox(label='prompt内容',interactive=False,lines=15)
                file_selector.change(fn=read_file_content,inputs=[file_selector],outputs=[file_content_display])

    demo.launch(
        share=True,
        inbrowser=True,
        server_name='0.0.0.0',
        server_port=10002)

if __name__ == '__main__':
    _launch_demo()
