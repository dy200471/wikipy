import requests
from bs4 import BeautifulSoup
import re
from difflib import get_close_matches
import json
import re
import os
from collections import defaultdict

# ------------------------
# 工具函数
# ------------------------

# 读取 data.js 中的 short → image 映射
short_to_image = {}
name_to_qzi = {}
name_to_id = {}
data_js_path = r"C:\Users\54906\Desktop\AItarkov\wp.js"
url = "https://escapefromtarkov.fandom.com/wiki/Virtex_programmable_processor"

if os.path.exists(data_js_path):
    with open(data_js_path, "r", encoding="utf-8") as f:
        js_text = f.read()
        match = re.search(r"=\s*(\[\s*\{.*\}\s*\])", js_text, re.DOTALL)
        if match:
            try:
                items_data = json.loads(match.group(1))
                short_to_image = {
                    item["name"]: item["image"]
                    for item in items_data if "name" in item and "image" in item
                }
                name_to_qzi = {
                    item["name"]: item.get("qzi")
                    for item in items_data if "name" in item and "qzi" in item
                }
                name_to_id = {
                    item["name"]: item.get("id")
                    for item in items_data if "name" in item and "id" in item
                }
            except Exception as e:
                print("❌ data.js 解析失败:", e)
        else:
            print("❌ data.js 未找到数组结构")
else:
    print("❌ 找不到 data.js 文件")
    
def run_query(query, lang="en"):
    headers = {"Content-Type": "application/json"}
    response = requests.post("https://api.tarkov.dev/graphql", headers=headers, json={"query": query})
    response.raise_for_status()
    return response.json()["data"]["items"]

def clean_text(text):
    return re.sub(r'\[\d+\]', '', text).strip()

def match_name(name, name_pool):
    matches = get_close_matches(name, name_pool, n=1, cutoff=0.8)
    return matches[0] if matches else None

# ------------------------
# 拉取 Tarkov.dev 中英数据
# ------------------------

query_base = """
{{
  items(lang: {lang}) {{
    id
    name
    shortName
    image8xLink
    description
    backgroundColor
    craftsUsing {{
      duration
      id
      level
      requiredItems {{
        quantity
        item {{
          name
          shortName
          iconLink
        }}
      }}
      rewardItems {{
        quantity
        item {{
          name
          shortName
          iconLink
        }}
      }}
      station {{
        name
        imageLink
      }}
    }}
    bartersFor {{
      id
      level
      requiredItems {{
        quantity
        item {{
          name
          shortName
          iconLink
        }}
      }}
      rewardItems {{
        quantity
        item {{
          name
          shortName
          iconLink
        }}
      }}
      trader {{
        name
        imageLink
      }}
    }}
    bartersUsing {{
      id
      level
      requiredItems {{
        quantity
        item {{
          name
          shortName
          iconLink
        }}
      }}
      rewardItems {{
        quantity
        item {{
          name
          shortName
          iconLink
        }}
      }}
      trader {{
        name
        imageLink
      }}
    }}
    craftsFor {{
      duration
      id
      level
      requiredItems {{
        quantity
        item {{
          name
          shortName
          iconLink
        }}
      }}
      station {{
        name
        imageLink
      }}
    }}
  }}
}}
"""

# 基础信息 - 介绍
items_en = run_query(query_base.format(lang="en"))
en_name_pool = [item["name"] for item in items_en]
en_lookup = {item["name"]: {"id": item["id"], "shortName": item["shortName"]} for item in items_en}
zh_lookup = {item["id"]: {"name": item["name"], "shortName": item["shortName"]} for item in run_query(query_base.format(lang="zh"))}
zh_image8xLink = {item["id"]: {"name": item["name"], "image8xLink": item["image8xLink"]} for item in run_query(query_base.format(lang="zh"))}
zh_backgroundColor = {item["id"]: {"name": item["name"], "backgroundColor": item["backgroundColor"]} for item in run_query(query_base.format(lang="zh"))}
zh_description = {item["id"]: {"name": item["name"], "description": item["description"]} for item in run_query(query_base.format(lang="zh"))}

# 工艺
zh_craftsUsing = {item["id"]: {"name": item["name"], "craftsUsing": item["craftsUsing"]} for item in run_query(query_base.format(lang="zh"))}
zh_craftsFor = {item["id"]: {"name": item["name"], "craftsFor": item["craftsFor"]} for item in run_query(query_base.format(lang="zh"))}

# 易货
zh_bartersUsing = {item["id"]: {"name": item["name"], "bartersUsing": item["bartersUsing"]} for item in run_query(query_base.format(lang="zh"))}
zh_bartersFor = {item["id"]: {"name": item["name"], "bartersFor": item["bartersFor"]} for item in run_query(query_base.format(lang="zh"))}

# ------------------------
# 读取 infobox 页面
# ------------------------


headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

# 获取主标题
title_div = soup.find("span", class_="mw-page-title-main")
item_name = clean_text(title_div.text) if title_div else "Unknown Item"

# 提取 infobox 字段
infobox = soup.find("tr", id="va-infobox0-content")
info_data = {}
if infobox:
    for row in infobox.find_all("tr"):
        label = row.find("td", class_="va-infobox-label")
        content = row.find("td", class_="va-infobox-content")
        if label and content:
            key = clean_text(label.text)
            val = clean_text(content.text)
            info_data[key] = val

# 提取图标图片
icon_img = soup.select_one("td.va-infobox-icon img")
icon_url = "https:" + icon_img["src"] if icon_img else ""

# ------------------------
# 匹配 tarkov.dev ID 和中文名
# ------------------------

item_id = ""
if item_name in en_lookup:
    item_id = en_lookup[item_name]["id"]
else:
    matched = match_name(item_name, en_name_pool)
    if matched:
        item_id = en_lookup[matched]["id"]
        print(f"模糊匹配：'{item_name}' → '{matched}'")

zh_name = zh_lookup.get(item_id, {}).get("name", "")
zh_icon = zh_image8xLink.get(item_id, {}).get("image8xLink", "")
zh_js = zh_description.get(item_id, {}).get("description", "")
zh_ys = zh_backgroundColor.get(item_id, {}).get("backgroundColor", "")
short_name_zh = zh_lookup.get(item_id, {}).get("shortName", item_name)

# 工艺 使用
zh_cring = zh_craftsUsing.get(item_id, {}).get("craftsUsing", "")
# 工艺 制作
zh_crFor = zh_craftsFor.get(item_id, {}).get("craftsFor", "")

# 易货 使用
zh_baing = zh_bartersUsing.get(item_id, {}).get("bartersUsing", "")
# 易货 制作
zh_baFor = zh_bartersFor.get(item_id, {}).get("bartersFor", "")


def format_duration(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    parts = []
    if h > 0:
        parts.append(f"{h}h")
    if m > 0:
        parts.append(f"{m}m")
    if s > 0 or not parts:
        parts.append(f"{s}s")
    return ' '.join(parts)

# ⚠️ 在插入图片 HTML 时可使用以下函数包装

def generate_icon_html(icon, name2, name):
    qzi = name_to_qzi.get(name2, name)
    id_ = name_to_id.get(name2, name)
    if qzi and id_:
        return f'''<a href="#/newsDetail?id={id_}" astyle_h="1" data_ue_src="#/newsDetail?id={id_}" stylehover="" wbackcolor_h="" lsc="" _t="6" _qzi="{qzi}" _n="{name}" target="" textvalue="" style=""><img src="{icon}" style="text-wrap:wrap;max-width:100%;max-height:100%;float:none;margin-left:0px;margin-right:0px;" unlocked="1" width="64" height="64"></a>'''
    else:
        return f'''<img src="{icon}" style="text-wrap:wrap;max-width:100%;max-height:100%;float:none;margin-left:0px;margin-right:0px;" unlocked="1" width="64" height="64">'''
def sort_and_group_by_station(data):
    return sorted(
        data,
        key=lambda item: (
            item.get('station', {}).get('name', '') if 'station' in item else item.get('trader', {}).get('name', ''),
            item.get('level', 0)
        )
    )

def generate_html_table(data, type_name):
    html = '<table><tbody>'
    for item_set in data:
        if not item_set.get('requiredItems') and not item_set.get('rewardItems'):
            continue
        # 所需材料
        html += '<table><tbody><tr><th style="background:#f1efee;border:1px solid #C0C0C0;word-break:break-all;text-align:center;">'
        required_items = item_set.get('requiredItems', [])
        for i, req in enumerate(required_items):
            name = req["item"]["shortName"]
            name2 = req["item"]["name"]
            icon = short_to_image.get(name2, req["item"]["iconLink"])
            quantity = req["quantity"]
            html += f'''<div class="icon-and-link-wrapper" style="/*  *//*  */display:flex;justify-content:center;align-items:center;"><div style="background:#1f2831;position:relative;outline:#495154 solid 2px;outline-offset:-2px;max-height:inherit;max-width:inherit;" contenteditable="true"><p style="text-align:center;">{generate_icon_html(icon, name2, name)}</p><p style="position:absolute;top:2px;right:2.5px;cursor:pointer;color:#A4AEB4;font-weight:bold;text-shadow:#000000 1px 1px 0px, #000000 -1px -1px 0px, #000000 1px -1px 0px, #000000 -1px 1px 0px;font-size:12px;text-align:right;line-height:normal;pointer-events:none;">{name}</p><div style="position:absolute;bottom:1px;right:1px;display:flex;flex-direction:column;align-items:flex-end;"><span style="background-color:rgba(0, 0, 0, 0.8);border-top-left-radius:3px;color:#C7C5B3;font-size:14px;height:18px;line-height:20px;text-align:center;padding:0px 5px;">{quantity}</span></div></div></div>'''
            # 如果不是最后一个，就加一个加号
            if i < len(required_items) - 1:
                html += '<p style="line-height:1.7em;"><strong><span style="font-size:14px;color:#333333;">+</span></strong></p>'
                
        level = item_set.get("level", "-")
        trader = item_set.get('trader')
        if trader:
            icon = trader["imageLink"]
            name = trader["name"]
        # 类型 + 等级信息单元格
        html += f'''<th style="background:#f1efee;border:1px solid #C0C0C0;word-break:break-all;text-align:center;"><p style="text-align:center;"><big><img src="{icon}" style="font-weight:700;text-align:center;text-wrap:wrap;background-color:#F7F7F7;width:100px;height:100px;"></big></p><p style="text-align:center;"><strong><span style="color:#333333;">{name} LL{level}</span></strong></p></th>'''
        
        # 产出物品
        for reward in item_set.get('rewardItems', []):
            name = reward["item"]["shortName"]
            name2 = reward["item"]["name"]
            icon = short_to_image.get(name2, reward["item"]["iconLink"])
            quantity = reward["quantity"]
            html += f'''<th style="border:1px solid #C0C0C0;word-break:break-all;background:#f1efee;"><div class="icon-and-link-wrapper" style="/*  *//*  */display:flex;justify-content:center;align-items:center;"><div style="background:#1f2831;position:relative;outline:#495154 solid 2px;outline-offset:-2px;max-height:inherit;max-width:inherit;" contenteditable="true"><p style="text-align:center;">{generate_icon_html(icon, name2, name)}&ZeroWidthSpace;</p><p style="position:absolute;top:2px;right:2.5px;cursor:pointer;color:#A4AEB4;font-weight:bold;text-shadow:#000000 1px 1px 0px, #000000 -1px -1px 0px, #000000 1px -1px 0px, #000000 -1px 1px 0px;font-size:12px;text-align:right;line-height:normal;pointer-events:none;">{name}</p><div style="position:absolute;bottom:1px;right:1px;display:flex;flex-direction:column;align-items:flex-end;"><span style="background-color:rgba(0, 0, 0, 0.8);border-top-left-radius:3px;color:#C7C5B3;font-size:14px;height:18px;line-height:20px;text-align:center;padding:0px 5px;">{quantity}</span></div></div></div></th>'''
        html += '</tr>'
        html += '</tbody>'
        html += '</table>'
    return html

def generate_html_table1(data, type_name):
    html = '<table><tbody>'
    for item_set in data:
        if not item_set.get('requiredItems') and not item_set.get('rewardItems'):
            continue

        # 所需材料
        html += '<table><tbody><tr><th style="background:#f1efee;border:1px solid #C0C0C0;word-break:break-all;text-align:center;">'
        required_items = item_set.get('requiredItems', [])
        for i, req in enumerate(required_items):
            name = req["item"]["shortName"]
            name2 = req["item"]["name"]
            icon = short_to_image.get(name2, req["item"]["iconLink"])
            quantity = req["quantity"]
            html += f'''<div class="icon-and-link-wrapper" style="/*  *//*  */display:flex;justify-content:center;align-items:center;"><div style="background:#1f2831;position:relative;outline:#495154 solid 2px;outline-offset:-2px;max-height:inherit;max-width:inherit;" contenteditable="true"><p style="text-align:center;">{generate_icon_html(icon, name2, name)}</p><p style="position:absolute;top:2px;right:2.5px;cursor:pointer;color:#A4AEB4;font-weight:bold;text-shadow:#000000 1px 1px 0px, #000000 -1px -1px 0px, #000000 1px -1px 0px, #000000 -1px 1px 0px;font-size:12px;text-align:right;line-height:normal;pointer-events:none;">{name}</p><div style="position:absolute;bottom:1px;right:1px;display:flex;flex-direction:column;align-items:flex-end;"><span style="background-color:rgba(0, 0, 0, 0.8);border-top-left-radius:3px;color:#C7C5B3;font-size:14px;height:18px;line-height:20px;text-align:center;padding:0px 5px;">{quantity}</span></div></div></div>'''
            # 如果不是最后一个，就加一个加号
            if i < len(required_items) - 1:
                html += '<p style="line-height:1.7em;"><strong><span style="font-size:14px;color:#333333;">+</span></strong></p>'
                
        level = item_set.get("level", "-")
        trader = item_set.get('station')
        duration_str = format_duration(item_set.get("duration", 0))
        if trader:
            name = trader["name"]
        # 类型 + 等级信息单元格
        html += f'''<th style="background:#f1efee;border:1px solid #C0C0C0;word-break:break-all;text-align:center;"><p style="text-align:center;"><strong>{name}(Level&nbsp;{level})</strong><br></p><p style="text-align:center;line-height:1.5em;"><span style="font-size:12px;"><span style="font-size:12px;color:#333333;">{duration_str}</span></span></p></th>'''
        
        # 产出物品
        for reward in item_set.get('rewardItems', []):
            name = reward["item"]["shortName"]
            name2 = reward["item"]["name"]
            icon = short_to_image.get(name2, reward["item"]["iconLink"])
            quantity = reward["quantity"]
            html += f'''<th style="border:1px solid #C0C0C0;word-break:break-all;background:#f1efee;"><div class="icon-and-link-wrapper" style="/*  *//*  */display:flex;justify-content:center;align-items:center;"><div style="background:#1f2831;position:relative;outline:#495154 solid 2px;outline-offset:-2px;max-height:inherit;max-width:inherit;" contenteditable="true"><p style="text-align:center;">{generate_icon_html(icon, name2, name)}&ZeroWidthSpace;</p><p style="position:absolute;top:2px;right:2.5px;cursor:pointer;color:#A4AEB4;font-weight:bold;text-shadow:#000000 1px 1px 0px, #000000 -1px -1px 0px, #000000 1px -1px 0px, #000000 -1px 1px 0px;font-size:12px;text-align:right;line-height:normal;pointer-events:none;">{name}</p><div style="position:absolute;bottom:1px;right:1px;display:flex;flex-direction:column;align-items:flex-end;"><span style="background-color:rgba(0, 0, 0, 0.8);border-top-left-radius:3px;color:#C7C5B3;font-size:14px;height:18px;line-height:20px;text-align:center;padding:0px 5px;">{quantity}</span></div></div></div></th>'''
        html += '</tr>'
        html += '</tbody>'
        html += '</table>'
    return html


# 调用生成
zh_cring_sorted = sort_and_group_by_station(zh_cring)
zh_crFor_sorted = sort_and_group_by_station(zh_crFor)
zh_baing_sorted = sort_and_group_by_station(zh_baing)
zh_baFor_sorted = sort_and_group_by_station(zh_baFor)

craft_html = generate_html_table1(zh_cring_sorted, "Craft")
craftFor_html = generate_html_table1(zh_crFor_sorted, "CraftFor")
barter_html = generate_html_table(zh_baing_sorted, "Barter")
barterFor_html = generate_html_table(zh_baFor_sorted, "BarterFor")
# ------------------------
# 提取 Location 部分的链接
# ------------------------

location_section = soup.find("span", {"id": "Location"})
locations = []
if location_section:
    ul = location_section.find_parent().find_next("ul")
    if ul:
        for li in ul.find_all("li"):
            a_tag = li.find("a", href=True)
            if a_tag:
                location_name = clean_text(a_tag.text)
                location_url = "https://escapefromtarkov.fandom.com" + a_tag["href"]
                locations.append({"name": location_name, "url": location_url})

# ------------------------
# 字段值汉化映射
# ------------------------

color_map = {
    "blue": "#1f2831",
    "default": "#393939",
    "violet": "#241a27",
    "grey": "#151d0f",
    "yellow": "#2f2f1c",
    "orange": "#251b13",
    # 可以在这里添加其他颜色和代码映射
}

type_map = {
    "Other": "其他",
    "Building material": "建筑材料",
    "Electronics": "电子产品",
    "Energy element": "能源物品",
    "Flammable material": "易燃物品",
    "Household item": "家居用品",
    "Medical supply": "医疗用品",
    "Tool": "工具",
    "Valuable": "贵重物品",
    "Info item": "情报物品",
    "Special item": "特殊装备"
}
effect_map = {
    "Generic loot item": "一般战利品"
}

item_type = info_data.get("Type", "")
weight = info_data.get("Weight", "")
grid_size = info_data.get("Grid size", "")
effect = info_data.get("Effect", "")

# 应用翻译（没有对应项则原样保留）
item_type_zh = type_map.get(item_type, item_type)
effect_zh = effect_map.get(effect, effect)

# 使用字典映射来获取对应的颜色代码
color_code = color_map.get(zh_ys, "#000000")  # 默认颜色为黑色 #000000

# ------------------------
# 生成 HTML 输出
# ------------------------

location_html = ""
for location in locations:
    location_name = location['name']
    if location_name == "PC block":  # 机箱
        location_name = '''<a href="#/newsDetail?id=1705" astyle_h="1" data_ue_src="#/newsDetail?id=1705" stylehover="" wbackcolor_h="" lsc="" _t="6" _qzi="AAYIqQ0SABoG5py6566x" _n="机箱" target="" textvalue="机箱" style=""><span style="background-color: inherit; font-size: inherit; color: inherit;">机箱</span></a>'''
    if location_name == "Safe":  # 保险箱
        location_name = '''<a href="#/newsDetail?id=1708" astyle_h="1" data_ue_src="#/newsDetail?id=1708" stylehover="" wbackcolor_h="" lsc="" _t="6" _qzi="AAYIrA0SABoJ5L+d6Zmp566x" _n="保险箱" target="" textvalue="保险箱" style=""><span style="background-color: inherit; font-size: inherit; color: inherit;">保险箱</span></a>'''
    if location_name == "Toolbox":  # 工具箱
        location_name = '''<a href="#/newsDetail?id=1711" astyle_h="1" data_ue_src="#/newsDetail?id=1711" stylehover="" wbackcolor_h="" lsc="" _t="6" _qzi="AAYIrw0SABoJ5bel5YW3566x" _n="工具箱" target="" textvalue="工具箱" style=""><span style="background-color: inherit; font-size: inherit; color: inherit;">工具箱</span></a>'''
    if location_name == "Wooden ammo box":  # 木制弹药箱
        location_name = '''<a href="#/newsDetail?id=1716" astyle_h="1" data_ue_src="#/newsDetail?id=1716" stylehover="" wbackcolor_h="" lsc="" _t="6" _qzi="AAYItA0SABoP5pyo5Yi25by56I2v566x" _n="木制弹药箱" target="" textvalue="木制弹药箱" style=""><span style="background-color: inherit; font-size: inherit; color: inherit;">木制弹药箱</span></a>'''
    if location_name == "Wooden crate":  # 木制板条箱
        location_name = '''<a href="#/newsDetail?id=1717" astyle_h="1" data_ue_src="#/newsDetail?id=1717" stylehover="" wbackcolor_h="" lsc="" _t="6" _qzi="AAYItQ0SABoP5pyo5Yi25p2/5p2h566x" _n="木制板条箱" target="" textvalue="木制板条箱" style=""><span style="background-color: inherit; font-size: inherit; color: inherit;">木制板条箱</span></a>'''
    if location_name == "Weapon box (4x4)":  # 武器箱（4x4）
        location_name = '''<a href="#/newsDetail?id=1712" astyle_h="1" data_ue_src="#/newsDetail?id=1712" stylehover="" wbackcolor_h="" lsc="" _t="6" _qzi="AAYIsA0SABoS5q2m5Zmo566x77yINHg077yJ" _n="武器箱（4x4）" target="" textvalue="武器箱（4x4）" style=""><span style="background-color: inherit; font-size: inherit; color: inherit;">武器箱（4x4）</span></a>'''
    if location_name == "Weapon box (5x2)":  # 武器箱（5x2）
        location_name = '''<a href="#/newsDetail?id=1714" astyle_h="1" data_ue_src="#/newsDetail?id=1714" stylehover="" wbackcolor_h="" lsc="" _t="6" _qzi="AAYIsg0SABoS5q2m5Zmo566x77yINXgy77yJ" _n="武器箱（5x2）" target="" textvalue="武器箱（5x2）" style=""><span style="background-color: inherit; font-size: inherit; color: inherit;">武器箱（5x2）</span></a>'''
    if location_name == "Weapon box (5x5)":  # 武器箱（5x5）
        location_name = '''<a href="#/newsDetail?id=1713" astyle_h="1" data_ue_src="#/newsDetail?id=1713" stylehover="" wbackcolor_h="" lsc="" _t="6" _qzi="AAYIsQ0SABoS5q2m5Zmo566x77yINXg177yJ" _n="武器箱（5x5）" target="" textvalue="武器箱（5x5）" style=""><span style="background-color: inherit; font-size: inherit; color: inherit;">武器箱（5x5）</span></a>'''
    if location_name == "Weapon box (6x3)":  # 武器箱（6x3）
        location_name = '''<a href="#/newsDetail?id=1715" astyle_h="1" data_ue_src="#/newsDetail?id=1715" stylehover="" wbackcolor_h="" lsc="" _t="6" _qzi="AAYIsw0SABoS5q2m5Zmo566x77yINngz77yJ" _n="武器箱（6x3）" target="" textvalue="武器箱（6x3）" style=""><span style="background-color: inherit; font-size: inherit; color: inherit;">武器箱（6x3）</span></a>'''
    if location_name == "Sport bag":  # 旅行包
        location_name = '''<a href="#/newsDetail?id=1709" astyle_h="1" data_ue_src="#/newsDetail?id=1709" stylehover="" wbackcolor_h="" lsc="" _t="6" _qzi="AAYIrQ0SABoJ5peF6KGM5YyF" _n="旅行包" target="" textvalue="旅行包" style=""><span style="background-color: inherit; font-size: inherit; color: inherit;">旅行包</span></a>'''
    if location_name == "Dead Scav":  # 死去的Scav
        location_name = '''<a href="#/newsDetail?id=1695" astyle_h="1" data_ue_src="#/newsDetail?id=1695" stylehover="" wbackcolor_h="" lsc="" _t="6" _qzi="AAYInw0SABoN5q275Y6755qEU2Nhdg==" _n="死去的Scav" target="" textvalue="死去的Scav" style=""><span style="background-color: inherit; font-size: inherit; color: inherit;">死去的Scav</span></a>'''
    if location_name == "Ground cache":  # 物资埋藏箱
        location_name = '''<a href="#/newsDetail?id=1698" astyle_h="1" data_ue_src="#/newsDetail?id=1698" stylehover="" wbackcolor_h="" lsc="" _t="6" _qzi="AAYIog0SABoP54mp6LWE5Z+L6JeP566x" _n="物资埋藏箱" target="" textvalue="物资埋藏箱" style=""><span style="background-color: inherit; font-size: inherit; color: inherit;">物资埋藏箱</span></a>'''
    if location_name == "Buried barrel cache":  # 物资埋藏桶
        location_name = '''<a href="#/newsDetail?id=1690" astyle_h="1" data_ue_src="#/newsDetail?id=1690" stylehover="" wbackcolor_h="" lsc="" _t="6" _qzi="AAYImg0SABoP54mp6LWE5Z+L6JeP5qG2" _n="物资埋藏桶" target="" textvalue="物资埋藏桶" style=""><span style="background-color: inherit; font-size: inherit; color: inherit;">物资埋藏桶</span></a>'''
    if location_name == "Ration supply crate":  # 配给物资箱
        location_name = '''<a href="#/newsDetail?id=1707" astyle_h="1" data_ue_src="#/newsDetail?id=1707" stylehover="" wbackcolor_h="" lsc="" _t="6" _qzi="AAYIqw0SABoP6YWN57uZ54mp6LWE566x" _n="配给物资箱" target="" textvalue="配给物资箱" style=""><span style="background-color: inherit; font-size: inherit; color: inherit;">配给物资箱</span></a>'''
    if location_name == "Medical supply crate":  # 医疗物资箱
        location_name = '''<a href="#/newsDetail?id=1704" astyle_h="1" data_ue_src="#/newsDetail?id=1704" stylehover="" wbackcolor_h="" lsc="" _t="6" _qzi="AAYIqA0SABoP5Yy755aX54mp6LWE566x" _n="医疗物资箱" target="" textvalue="医疗物资箱" style=""><span style="background-color: inherit; font-size: inherit; color: inherit;">医疗物资箱</span></a>'''
    if location_name == "Technical supply crate":  # 技术物资箱
        location_name = '''<a href="#/newsDetail?id=1710" astyle_h="1" data_ue_src="#/newsDetail?id=1710" stylehover="" wbackcolor_h="" lsc="" _t="6" _qzi="AAYIrg0SABoP5oqA5pyv54mp6LWE566x" _n="技术物资箱" target="" textvalue="技术物资箱" style=""><span style="background-color: inherit; font-size: inherit; color: inherit;">技术物资箱</span></a>'''
    if location_name == "Jacket":  # 夹克
        location_name = '''<a href="#/newsDetail?id=1699" astyle_h="1" data_ue_src="#/newsDetail?id=1699" stylehover="" wbackcolor_h="" lsc="" _t="6" _qzi="AAYIow0SABoG5aS55YWL" _n="夹克" target="" textvalue="夹克" style=""><span style="background-color: inherit; font-size: inherit; color: inherit;">夹克</span></a>'''
    if location_name == "Drawer":  # 抽屉
        location_name = '''<a href="#/newsDetail?id=1696" astyle_h="1" data_ue_src="#/newsDetail?id=1696" stylehover="" wbackcolor_h="" lsc="" _t="6" _qzi="AAYIoA0SABoG5oq95bGJ" _n="抽屉" target="" textvalue="抽屉" style=""><span style="background-color: inherit; font-size: inherit; color: inherit;">抽屉</span></a>'''
    if location_name == "Plastic suitcase":  # 塑料手提箱
        location_name = '''<a href="#/newsDetail?id=1706" astyle_h="1" data_ue_src="#/newsDetail?id=1706" stylehover="" wbackcolor_h="" lsc="" _t="6" _qzi="AAYIqg0SABoP5aGR5paZ5omL5o+Q566x" _n="塑料手提箱" target="" textvalue="塑料手提箱" style=""><span style="background-color: inherit; font-size: inherit; color: inherit;">塑料手提箱</span></a>'''
    if location_name == "Common fund stash":  # Сommon fund储藏处
        location_name = '''<a href="#/newsDetail?id=1694" astyle_h="1" data_ue_src="#/newsDetail?id=1694" stylehover="" wbackcolor_h="" lsc="" _t="6" _qzi="AAYIng0SABoV0KFvbW1vbiBmdW5k5YKo6JeP5aSE" _n="Сommon fund储藏处" target="" textvalue="Сommon&nbsp;fund储藏处" style=""><span style="background-color: inherit; font-size: inherit; color: inherit;">Сommon&nbsp;fund储藏处</span></a>'''
    if location_name == "Grenade box":  # 手榴弹箱（盒）
        location_name = '''<a href="#/newsDetail?id=1697" astyle_h="1" data_ue_src="#/newsDetail?id=1697" stylehover="" wbackcolor_h="" lsc="" _t="6" _qzi="AAYIoQ0SABoV5omL5qa05by5566x77yI55uS77yJ" _n="手榴弹箱（盒）" target="" textvalue="手榴弹箱（盒）" style=""><span style="background-color: inherit; font-size: inherit; color: inherit;">手榴弹箱（盒）</span></a>'''
    if location_name == "Medbag SMU06":  # SMU06医疗包
        location_name = '''<a href="#/newsDetail?id=1702" astyle_h="1" data_ue_src="#/newsDetail?id=1702" stylehover="" wbackcolor_h="" lsc="" _t="6" _qzi="AAYIpg0SABoOU01VMDbljLvnlpfljIU=" _n="SMU06医疗包" target="" textvalue="SMU06医疗包" style=""><span style="background-color: inherit; font-size: inherit; color: inherit;">SMU06医疗包</span></a>'''
    if location_name == "Medcase":  # 医药箱
        location_name = '''<a href="#/newsDetail?id=1703" astyle_h="1" data_ue_src="#/newsDetail?id=1703" stylehover="" wbackcolor_h="" lsc="" _t="6" _qzi="AAYIpw0SABoJ5Yy76I2v566x" _n="医药箱" target="" textvalue="医药箱" style=""><span style="background-color: inherit; font-size: inherit; color: inherit;">医药箱</span></a>'''
    if location_name == "Jacket (204 key)":  # 夹克（204钥匙）
        location_name = '''<a href="#/newsDetail?id=4881" astyle_h="1" data_ue_src="#/newsDetail?id=4881" stylehover="" wbackcolor_h="" lsc="" _t="6" _qzi="AAYIkSYSABoV5aS55YWL77yIMjA06ZKl5YyZ77yJ" _n="夹克（204钥匙）" target="" textvalue="夹克（204钥匙）" style=""><span style="background-color: inherit; font-size: inherit; color: inherit;">夹克（204钥匙）</span></a>'''
    # 生成 HTML
    location_html += f"""<p style="text-align:left;"><span style="color:#9A8866;font-family:Verdana, Arial, Tahoma;letter-spacing:5px;">•</span><span style="background-color:inherit;font-size:inherit;color:inherit;">{location_name}</span></p>"""


html_snippet = f"""
<table width="425.2187805175781" cellpadding="0" cellspacing="0" class="va-infobox"><tbody style="box-sizing:inherit;"><tr style="box-sizing:inherit;"><td class="va-infobox-cont" bgcolor="transparent" bselect="top,right,bottom,left" bordercolor="rgb(0, 0, 0)" valign="top" align="center" height="334.19032287597656" width="429" style="font-size:14px;box-sizing:inherit;margin:0px;background:transparent;border-width:1px;border-style:solid;border-color:#000000;word-break:break-all;"><table class="va-infobox-group" cellspacing="0" cellpadding="0" width="510.3229503631592"><tbody style="box-sizing:inherit;"><tr><th class="va-infobox-header" colspan="2" _msttexthash="11630060" _msthash="145" style="border-width:1px;border-right-style:solid;border-bottom-style:solid;border-left-style:solid;border-color:#C0C0C0;background-color:#F1EFEE;font-size:12px;word-break:break-all;text-align:center;width:206.997px;padding-right:3px;padding-left:3px;" height="22"><span style="font-size:14px;color:#333333;">{short_name_zh}</span></th></tr><tr><th class="va-infobox-header" colspan="2" _msttexthash="11630060" _msthash="146" bgcolor="rgb(0, 0, 0)" bselect="top,right,bottom,left" bordercolor="rgb(0, 0, 0)" valign="top" align="center" height="204.9573745727539" style="background-image:url(https://32714989.s21i.faiusr.com/4/ABUIABAEGAAgotL0tgYowvLZogEwvQY4iAM.png);background-repeat:no-repeat;background-size:cover;background-position:center center;padding:1px 2px;border-width:1px;border-right-style:solid;border-bottom-style:solid;border-left-style:solid;border-color:#000000;background-color:#000000;box-sizing:inherit;vertical-align:middle;word-break:break-all;"><div class="icon-and-link-wrapper" style="/*  *//*  *//* display:flex;*//* justify-content:center;*//* align-items:center;*/"><div class="icon-and-link-wrapper"><div style="position:relative;outline-offset:-2px;max-height:inherit;max-width:inherit;" contenteditable="true"><p style="text-align:center;"><img src="{zh_icon}" style="text-wrap:wrap;width:233px;height:233px;float:none;filter:drop-shadow(#000000 0px 0px 3px);margin-left:0px;margin-right:0px;" unlocked="1"></p><div style="position:absolute;top:5px;right:1px;display:flex;flex-direction:column;align-items:flex-end;padding:0px 1px 0px 0px;"><div style="background-color:{color_code};background-image:linear-gradient(to right, #4951547d 1px, transparent 1px),    linear-gradient(to bottom, #4951547d 1px, transparent 1px);background-position:0 0;background-size:100% 100%;position:relative;outline:#495154 solid 2px;outline-offset:-2px;max-height:inherit;max-width:inherit;" contenteditable="true"><p style="text-align:center;display:flex;justify-content:center;align-items:center;"><img src="{zh_icon}" style="text-wrap:wrap;width:64px;filter:drop-shadow(#000000 0px 0px 3px);height:64px;float:none;margin-left:0px;margin-right:0px;" unlocked="1"></p><p style="position:absolute;top:0px;right:2.5px;cursor:pointer;color:#A4AEB4;/* font-weight:bold;*/text-shadow:#000000 1px 1px 0px, #000000 -1px -1px 0px, #000000 1px -1px 0px, #000000 -1px 1px 0px;font-size:11px;text-align:right;line-height:normal;pointer-events:none;"><span style="background-color:inherit;font-size:inherit;color:inherit;">{short_name_zh}</span></p><div style="position:absolute;bottom:1px;right:1px;display:flex;flex-direction:column;align-items:flex-end;padding:0px 1px 0px 0px;"></div></div></div></div></div></div></th></tr><tr><th class="va-infobox-header" colspan="2" _msttexthash="11630060" _msthash="145" style="border-width:1px;border-right-style:solid;border-bottom-style:solid;border-left-style:solid;border-color:#C0C0C0;background-color:#F1EFEE;font-size:12px;word-break:break-all;text-align:center;width:206.997px;padding-right:3px;padding-left:3px;"><span style="font-size:14px;color:#333333;">总览</span></th></tr><tr><td bgcolor="rgb(241, 239, 238)" bselect="top,right,bottom,left" bordercolor="rgb(192, 192, 192)" valign="top" align="center" style="background-color:#F1EFEE;font-size:12px;word-break:break-all;border-width:1px;border-style:solid;border-color:#C0C0C0;text-align:right;width:256px;padding-right:3px;padding-left:3px;"><p style="line-height:2em;"><span style="font-family:sans-serif;font-weight:700;font-size:14px;color:#333333;">类型</span><br></p></td><td style="word-break:break-all;text-align:justify;width:270px;padding-right:3px;padding-left:3px;"><p>{item_type_zh}</p></td></tr><tr><td bgcolor="rgb(241, 239, 238)" bselect="top,right,bottom,left" bordercolor="rgb(192, 192, 192)" valign="top" align="center" style="background-color:#F1EFEE;font-size:12px;word-break:break-all;border-width:1px;border-style:solid;border-color:#C0C0C0;text-align:right;width:256px;padding-right:3px;padding-left:3px;"><p style="line-height:2em;"><span style="font-family:sans-serif;font-weight:700;font-size:14px;color:#333333;">重量</span><br></p></td><td style="font-size:12px;word-break:break-all;text-align:justify;width:270px;padding-right:3px;padding-left:3px;"><p style="line-height:1.7em;"><span style="font-size:14px;"></span><span style="font-size:14px;"><span><span><span><span><span><span><span>{weight}</span></span></span></span></span></span></span></span></p></td></tr><tr><td bgcolor="rgb(241, 239, 238)" bselect="top,right,bottom,left" bordercolor="rgb(192, 192, 192)" valign="top" align="center" style="background-color:#F1EFEE;font-size:12px;word-break:break-all;border-width:1px;border-style:solid;border-color:#C0C0C0;text-align:right;width:256px;padding-right:3px;padding-left:3px;"><p style="line-height:2em;"><span style="font-family:sans-serif;font-weight:700;font-size:14px;color:#333333;">占用格数</span><br></p></td><td style="font-size:12px;word-break:break-all;text-align:justify;width:270px;padding-right:3px;padding-left:3px;"><p style="line-height:1.7em;"><span style="font-size:14px;"></span><span style="font-size:14px;"><span>{grid_size}</span></span></p></td></tr><tr><th class="va-infobox-header" colspan="2" _msttexthash="11630060" _msthash="145" style="border-width:1px;border-style:solid;border-color:#C0C0C0;background-color:#F1EFEE;font-size:12px;word-break:break-all;width:206.997px;padding-right:3px;padding-left:3px;" bgcolor="rgb(241, 239, 238)" bselect="top,right,bottom,left" bordercolor="rgb(192, 192, 192)" valign="middle" align="center"><span style="font-size:14px;color:#333333;">效果</span></th></tr><tr><td bgcolor="rgb(241, 239, 238)" bselect="top,right,bottom,left" bordercolor="rgb(192, 192, 192)" valign="top" align="center" style="background-color:#F1EFEE;font-size:12px;word-break:break-all;border-width:1px;border-style:solid;border-color:#C0C0C0;text-align:right;width:256px;padding-right:3px;padding-left:3px;"><p style="line-height:2em;"><span style="font-family:sans-serif;font-weight:700;font-size:14px;color:#333333;">效果</span><br></p></td><td style="word-break:break-all;text-align:justify;width:270px;padding-right:3px;padding-left:3px;">{effect_zh}</td></tr></tbody></table></td></tr></tbody></table>
<h2 style="padding:0px 0px 0.3em;margin:1em 0px 16px;box-sizing:border-box;line-height:1.225;font-size:1.75em;position:relative;border-bottom:1px solid #222222;border-top-color:#222222;border-right-color:#222222;border-left-color:#222222;color:#888888;font-family:&quot;Microsoft YaHei&quot;, Helvetica, &quot;Meiryo UI&quot;, &quot;Malgun Gothic&quot;, &quot;Segoe UI&quot;, &quot;Trebuchet MS&quot;, Monaco, monospace, Tahoma, STXihei, 华文细黑, STHeiti, &quot;Helvetica Neue&quot;, &quot;Droid Sans&quot;, &quot;wenquanyi micro hei&quot;, FreeSans, Arimo, Arial, SimSun, 宋体, Heiti, 黑体, sans-serif;">介绍</h2><p style="line-height:1.5em;">{zh_js}</p>
<h2 style="padding:0px 0px 0.3em;margin:1em 0px 16px;box-sizing:border-box;line-height:1.225;font-size:1.75em;position:relative;border-bottom:1px solid #222222;border-top-color:#222222;border-right-color:#222222;border-left-color:#222222;color:#888888;font-family:&quot;Microsoft YaHei&quot;, Helvetica, &quot;Meiryo UI&quot;, &quot;Malgun Gothic&quot;, &quot;Segoe UI&quot;, &quot;Trebuchet MS&quot;, Monaco, monospace, Tahoma, STXihei, 华文细黑, STHeiti, &quot;Helvetica Neue&quot;, &quot;Droid Sans&quot;, &quot;wenquanyi micro hei&quot;, FreeSans, Arimo, Arial, SimSun, 宋体, Heiti, 黑体, sans-serif;text-align:left;">生成地点</h2>{location_html}
<h2 style="padding:0px 0px 0.3em;margin:1em 0px 16px;box-sizing:border-box;line-height:1.225;font-size:1.75em;position:relative;border-bottom:1px solid #222222;border-top-color:#222222;border-right-color:#222222;border-left-color:#222222;color:#888888;font-family:&quot;Microsoft YaHei&quot;, Helvetica, &quot;Meiryo UI&quot;, &quot;Malgun Gothic&quot;, &quot;Segoe UI&quot;, &quot;Trebuchet MS&quot;, Monaco, monospace, Tahoma, STXihei, 华文细黑, STHeiti, &quot;Helvetica Neue&quot;, &quot;Droid Sans&quot;, &quot;wenquanyi micro hei&quot;, FreeSans, Arimo, Arial, SimSun, 宋体, Heiti, 黑体, sans-serif;">商人交换</h2>{barter_html}{barterFor_html}
<h2 style="padding:0px 0px 0.3em;margin:1em 0px 16px;box-sizing:border-box;line-height:1.225;font-size:1.75em;position:relative;border-bottom:1px solid #222222;border-top-color:#222222;border-right-color:#222222;border-left-color:#222222;color:#888888;font-family:&quot;Microsoft YaHei&quot;, Helvetica, &quot;Meiryo UI&quot;, &quot;Malgun Gothic&quot;, &quot;Segoe UI&quot;, &quot;Trebuchet MS&quot;, Monaco, monospace, Tahoma, STXihei, 华文细黑, STHeiti, &quot;Helvetica Neue&quot;, &quot;Droid Sans&quot;, &quot;wenquanyi micro hei&quot;, FreeSans, Arimo, Arial, SimSun, 宋体, Heiti, 黑体, sans-serif;">藏身处制作</h2>{craft_html}{craftFor_html}
</div>
"""

# 保存 HTML 输出
with open("apollo_icon_with_location.html", "w", encoding="utf-8") as f:
    f.write("<html><head><meta charset='utf-8'></head><body>\n")
    f.write(html_snippet)
    f.write("</body></html>")
    
with open(r"C:\Users\54906\Desktop\wiki.txt", "w", encoding="utf-8") as f:
    f.write(html_snippet)

# 打印最终的 HTML
print(html_snippet)