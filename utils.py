# k8s上暴露的接口
model_service_address = '172.17.104.6:31847' 
# dibo
# model_service_address = '172.17.100.2:30772'
# 测试地址
#model_service_address = '172.17.103.23:8051'

#model_config = {'千问2.5-72b': 'qwen2.5-72b-instruct', '千问2.5-3b': 'qwen2.5-3b-instruct'}


def _parse_text(text):
    lines = text.split('\n')
    lines = [line for line in lines if line != ""]
    count = 0
    for i, line in enumerate(lines):
        if "```" in line:
            count += 1
            items = line.split('`')
            if count %2 == 1:
                line[i] = f'<pre><code class="language-{items[-1]}">'
            else:
                lines[i] = f"<br></code></pre>"
        else:
            if i > 0:
                if count %2 ==1:
                    line = line.replace("`", r"\`")
                    line = line.replace("<", "&lt;")
                    line = line.replace(">", "&gt;")
                    line = line.replace(" ", "&nbsp;")
                    line = line.replace("*", "&ast;")
                    line = line.replace("_", "&lowbar;")
                    line = line.replace("-", "&#45;")
                    line = line.replace(".", "&#46")
                    line = line.replace("!", "&#33")
                    line = line.replace("(", "&#40")
                    line = line.replace(")", "&#41")
                    line = line.replace("$", "&#36")
                lines[i] = "<br>" + line
    text = "".join(lines)
    return text