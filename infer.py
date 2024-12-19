
def main(client,input_dic,model,query,top_p,max_tokens,presence_penalty,temperature):
    def replace_placeholders(A, B):
        import re

        # 使用正则表达式匹配所有的{}中的内容
        placeholders = re.findall(r'\{(.*?)\}', A)

        # 遍历所有占位符，检查它们是否在字典B中
        for placeholder in placeholders:
            if placeholder not in B:
                return f"关键字 '{placeholder}' 不存在于字典中",True

        # 替换占位符
        for placeholder in placeholders:
            A = A.replace(f'{{{placeholder}}}', B[placeholder])

        return A,False
    input_text,replace_flag = replace_placeholders(query, input_dic)
    if replace_flag:
        return input_text
    chat_completion = client.chat.completions.create(
        messages=[{
            "role": "system",
            "content": "You are a helpful assistant."
        }, {
            "role": "user",
            "content": input_text
        }],
        model=model,
        top_p=top_p,
        max_tokens=max_tokens,
        presence_penalty=presence_penalty,
        seed=42,
        temperature=temperature
        
    )
    print(chat_completion.choices[0].message.content)
    return chat_completion.choices[0].message.content