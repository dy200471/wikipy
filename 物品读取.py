from bs4 import BeautifulSoup
import json

# 路径
html_path = r"C:\Users\54906\Desktop\AItarkov\Untitled-1.html"
js_output_path = r"C:\Users\54906\Desktop\AItarkov\胸挂.js"

# 读取 HTML
with open(html_path, 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'html.parser')

# 提取信息
results = []
for div in soup.find_all('div', class_='icon-and-link-wrapper'):
    a_tag = div.find('a')
    span_tag = div.find('span')
    img_tag = div.find('img')

    if a_tag and span_tag and img_tag:
        name = a_tag.get('_n', '')
        qzi = a_tag.get('_qzi', '')
        href = a_tag.get('href', '')
        id_part = href.split('id=')[-1] if 'id=' in href else ''
        short = span_tag.get_text(strip=True)
        image = img_tag.get('src', '')

        results.append({
            'name': name,
            'short': short,
            'qzi': qzi,
            'id': id_part,
            'image': image
        })

# 转换为 JS 内容
js_content = "const items = " + json.dumps(results, ensure_ascii=False, indent=2) + ";"

# 写入 JS 文件
with open(js_output_path, 'w', encoding='utf-8') as f:
    f.write(js_content)

print(f"[✓] 导出成功：{js_output_path}")
