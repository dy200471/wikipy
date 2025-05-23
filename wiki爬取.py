import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from difflib import get_close_matches

# ------------------------
# 工具函数
# ------------------------

def run_query(query, lang="en"):
    headers = {"Content-Type": "application/json"}
    response = requests.post("https://api.tarkov.dev/graphql", headers=headers, json={"query": query})
    response.raise_for_status()
    return response.json()["data"]["items"]

def clean_text(text):
    return re.sub(r'\[\d+\]', '', text).strip()

def match_name(name, name_pool):
    """用于模糊匹配英文名"""
    matches = get_close_matches(name, name_pool, n=1, cutoff=0.8)
    return matches[0] if matches else None

# ------------------------
# 获取 Tarkov.dev 数据
# ------------------------

query_base = """
{{
  items(lang: {lang}) {{
    id
    name
    shortName
  }}
}}
"""

items_en = run_query(query_base.format(lang="en"))
en_name_pool = [item["name"] for item in items_en]
en_lookup = {item["name"]: {"id": item["id"], "shortName": item["shortName"]} for item in items_en}
id_lookup_en = {item["id"]: item for item in items_en}

items_zh = run_query(query_base.format(lang="zh"))
zh_lookup = {item["id"]: {"name": item["name"], "shortName": item["shortName"]} for item in items_zh}

# ------------------------
# 抓取 Wiki 表格
# ------------------------

wiki_url = "https://escapefromtarkov.fandom.com/wiki/Jacket_(204_key)"
headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(wiki_url, headers=headers)
response.raise_for_status()
soup = BeautifulSoup(response.text, "html.parser")

table = soup.find("table", class_="wikitable")
columns = [th.text.strip() for th in table.find_all("th")]

rows = []
for tr in table.find_all("tr")[1:]:
    cells = [clean_text(td.text) for td in tr.find_all(["td", "th"])]
    if len(cells) < len(columns):
        cells += [''] * (len(columns) - len(cells))
    rows.append(cells)

df = pd.DataFrame(rows, columns=columns)

# ------------------------
# 匹配 ID 和 中文名
# ------------------------

def resolve_id(name):
    if name in en_lookup:
        return en_lookup[name]["id"]
    matched = match_name(name, en_name_pool)
    if matched:
        return en_lookup[matched]["id"]
    return ""

df["ID"] = df["Item"].map(resolve_id)
df["中文名"] = df["ID"].map(lambda item_id: zh_lookup.get(item_id, {}).get("name", ""))

# 输出无法匹配的项
unmatched = df[df["ID"] == ""]
if not unmatched.empty:
    print("⚠️ 无法匹配的物品名称：")
    print(unmatched["Item"].to_list())

# 可选排序
if "Type" in df.columns:
    df.sort_values(by=["Type", "Item"], inplace=True)
df.reset_index(drop=True, inplace=True)

# ------------------------
# 生成 HTML 输出
# ------------------------

def generate_html(row):
    item_id = row["ID"]
    short_name_zh = zh_lookup.get(item_id, {}).get("shortName", row["Item"])
    image_url = f"https://assets.tarkov.dev/{item_id}-icon.webp" if item_id else ""
    
    return f"""<div class="icon-and-link-wrapper" style="display:flex;justify-content:center;padding:1px;align-items:center;"><div style="background-color:#151d0f;background-image:linear-gradient(to right, #4951547d 1px, transparent 1px), linear-gradient(to bottom, #4951547d 1px, transparent 1px);background-position:0 0;background-size:100% 100%;position:relative;outline:#495154 solid 2px;outline-offset:-2px;max-height:inherit;max-width:inherit;" contenteditable="true"><p style="text-align:center;"><img src="{image_url}" style="text-wrap:wrap;width:55px;filter:drop-shadow(#000000 0px 0px 3px);height:55px;float:none;margin-left:0px;margin-right:0px;" unlocked="0">&ZeroWidthSpace;</p><p style="position:absolute;top:0px;right:2.5px;cursor:pointer;color:#A4AEB4;text-shadow:#000000 1px 1px 1px, #000000 -1px -1px 1px, #000000 1px -1px 1px, #000000 -1px 1px 1px;font-size:9px;text-align:right;line-height:normal;"><span style="background-color:inherit;font-size:inherit;color:inherit;">{short_name_zh}</span></p></div></div>""".strip()

df["HTML"] = df.apply(generate_html, axis=1)

with open("wooden_crate_icons.html", "w", encoding="utf-8") as f:
    f.write("<html><body>\n")
    f.write('<div style="background-color:#363636;box-shadow:0 2px 4px rgba(0, 0, 0, 0.2);border-radius:5px;flex-wrap:wrap;display:flex;justify-content:center;padding:10px;margin-bottom:5px;">\n')
    for html_snippet in df["HTML"]:
        f.write(html_snippet)
    f.write("</div></body></html>")
