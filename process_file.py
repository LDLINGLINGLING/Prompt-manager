import pandas as pd
import re
import asyncio
from infer import main
from datetime import datetime
import os
import concurrent.futures
from openai import OpenAI
openai_api_key = "token-abc123"
openai_api_base = "http://localhost:8000/v1"

client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key=openai_api_key,
    base_url=openai_api_base,
)

models = client.models.list()
model = models.data[0].id
model_config = {m.id.split('/')[-1]:m.id for index, m in enumerate(models)}
def read_text(file):
    with open(file.name, 'r', encoding='utf-8') as f:
        content = f.read()
    return content
def save_prompt_batch(text,task_name):
    time_stamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
    file_path = 'save_prompt_batch/{}_{}_.txt'.format(task_name, time_stamp)
    if not os.path.exists('save_prompt_batch'):
        os.mkdir('save_prompt_batch')
    try:
        with open(file_path,'w',encoding='utf-8') as file:
            file.write(text)
    except Exception as e:
        return e
    return '输入作为提示词保存到{}'.format(file_path)

def read_xlsx(file):

    if file.name.endswith('xlsx'):
        df = pd.read_excel(file.name)
    elif file.name.endswith('jsonl'):
        df = pd.read_json(file.name, lines=True)
    elif file.name.endswith('json'):
        df = pd.read_json(file.name, lines=True)

    return df

def dispaly_top5_rows(df):
    return df.head(5)


def download_xlsx(df, task_name):
    time_stamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
    file_path = 'save_dir/{}_{}_.xlsx'.format(task_name, time_stamp)
    df.to_excel(file_path, index=False)

    return file_path


def replace_value(v, col_name, task_name):
    #v zyjd的值   col_name zyjd  task_name 庭审预设问题
    if ('庭审预设问题' in task_name) or ('争议焦点' in task_name) or ('审理要点' in task_name and '民间借贷' in task_name):
        if v == '无':
            return f'无输入'
    return v
        

def replace_cqcl(col_names, row):
    # 构造一审输入
    yishen = '空'
    if row[col_names[0]].strip() =='无' and row[col_names[1]].strip() =='无':
        yishen = '空'
    elif row[col_names[0]].strip() =='无' and row[col_names[1]].strip() !='无':
        yishen = row[col_names[1]].strip()
    elif row[col_names[0]].strip() !='无' and row[col_names[1]].strip() =='无':
        yishen = row[col_names[0]].strip()
    elif row[col_names[0]].strip() !='无' and row[col_names[1]].strip() !='无':
        yishen = row[col_names[0]].strip()+'\n'+row[col_names[1]].strip()

    # 构造二审输入
    ershen = '空'
    if row[col_names[2]].strip() =='无' and row[col_names[3]].strip() =='无':
        ershen = '空'
    elif row[col_names[2]].strip() =='无' and row[col_names[3]].strip() !='无':
        ershen = row[col_names[3]].strip()
    elif row[col_names[2]].strip() !='无' and row[col_names[3]].strip() =='无':
        ershen = row[col_names[2]].strip()
    elif row[col_names[2]].strip() !='无' and row[col_names[3]].strip() !='无':
        ershen = row[col_names[2]].strip()+'\n'+row[col_names[3]].strip()
    return yishen, ershen


def find_missing_values(list1, list2):
    """
    查找list1中不在list2中的元素
    """
    missing_values = set(list1) - set(list2)
    return missing_values


def process_files(processed_text, df, param_input_top_p, param_input_temperture, param_input_max_tokens, param_input_repetition, model_selection_text, model_selection_button, task_name, pos_result='result'):
    
    # 之后会根据选择的模型名称用字典映射为部署端的模型名称
    model_selection_v = None
    model_selection_k = None
    if model_selection_text != '':
        # 选择的模型名称
        model_selection_v = model_selection_text
        model_name = model_selection_v
    else:
        # 输入的模型名称
        model_selection_k = model_selection_button
        model_name = model_selection_k
    pos_result = '_'+pos_result +'_'+ datetime.now().strftime("%Y%m%d%H%M")
    df[task_name + pos_result] = None
    df[task_name + '_inputs'] = None
    df[task_name +'prompt_template'] = None

    pattern = r'\{([^}]*)\}'
    col_names = re.findall(pattern, processed_text)

    missing_values = find_missing_values(col_names, df.columns.tolist())
    if missing_values:
        return "请检查提示词与输入数据中输入项: \n {} \n 上述提示词中的待输入项未出现在输入数据中".format(", ".join(missing_values)), pd.DataFrame({'请检查': ['输入有误']})

    # 定义线程池执行的任务
    def process_row(inx, row, input_dic_, model_name, processed_text):
        
        cur_instruct = input_dic_
        cur_instruct['prompt_teamplate'] = processed_text
        res = main(client=client, input_dic=input_dic_, model=model_config[model_name], query=processed_text,
                    top_p=float(param_input_top_p), max_tokens=float(param_input_max_tokens),
                    presence_penalty=float(param_input_repetition), temperature=float(param_input_temperture))
        try:
            df.loc[inx, task_name +pos_result] = res
            df.loc[inx, task_name + '_inputs'] = str(cur_instruct)
            df.loc[inx, task_name + 'prompt_template'] = processed_text
            df.loc[inx, task_name + 'sampling_parma'] = str({'model_name': model_name, 'top_p': param_input_top_p,  'temperature': param_input_temperture, 'repetition_penalty': param_input_repetition})
        except Exception as e:
            print(f"Error processing row {inx}: {e}")
            df.loc[inx, task_name + pos_result] = ''
            df.loc[inx, task_name + '_inputs'] = 'error'
            df.loc[inx, task_name + 'prompt_template'] = processed_text
            df.loc[inx, task_name + 'sampling_parma'] = str({'model_name': model_name, 'top_p': param_input_top_p, 'temperature': param_input_temperture, 'repetition_penalty': param_input_repetition})

    # 创建一个线程池，限制最大线程数为32
    with concurrent.futures.ThreadPoolExecutor(max_workers=32) as executor:
        futures = []
        for inx, row in df.iterrows():
            input_dic = {}
            if '常情常理' in task_name:
                yishen, ershen = replace_cqcl(col_names, row)
                input_dic['一审的文本'] = yishen
                input_dic['二审的文本'] = ershen
            else:
                for col_name in col_names:
                    v = replace_value(row[col_name], col_name, task_name)
                    input_dic[col_name] = v

            input_dic_ = {k: v for k, v in input_dic.items()}
            futures.append(executor.submit(process_row, inx, row, input_dic_, model_name, processed_text))
        
        # 等待所有线程完成
        for future in concurrent.futures.as_completed(futures):
            future.result()

    # 替换 processed_text 中的占位符
    for key, value in input_dic_.items():
        processed_text = processed_text.replace(key, value.strip())
    
    first_column_name = df.columns[0]  # 获取第一列的名称
    df = df[[task_name + pos_result, first_column_name] + [col for col in df.columns if col not in [task_name + pos_result, first_column_name]]]
    
    return processed_text, df
    