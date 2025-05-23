import requests
import pandas as pd
import os

query = """
{
  items(lang: zh) {
    id
    name
    description
    shortName
    types
    updated
    velocity
    weight
    width
    normalizedName
    loudness
    lastOfferCount
    lastLowPrice
    avg24hPrice
    high24hPrice
  }
}
"""

columns_zh = {
    "id": "ID",
    "name": "名称",
    "shortName": "简称",
    "description": "描述",
    "types": "类型",
    "updated": "更新时间",
    "velocity": "初速",
    "weight": "重量（kg）",
    "width": "宽度（格）",
    "normalizedName": "标准名称",
    "loudness": "响度",
    "lastOfferCount": "当前上架数量",
    "lastLowPrice": "最低价格",
    "avg24hPrice": "24小时均价",
    "high24hPrice": "24小时最高价"
}

# 请求
url = "https://api.tarkov.dev/graphql"
headers = {"Content-Type": "application/json"}
response = requests.post(url, json={"query": query}, headers=headers)
data = response.json()["data"]["items"]

# 转换为 DataFrame 并替换中文列名
df = pd.DataFrame(data)
df = df[list(columns_zh.keys())]  # 保留需要的列顺序
df.rename(columns=columns_zh, inplace=True)

# 输出路径
output_dir = r"C:\Users\54906\Desktop\AItarkov"
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "塔科夫物品数据_API完整.xlsx")

# 保存 Excel
df.to_excel(output_path, index=False, engine="openpyxl")
print(f"✅ 成功导出至：{output_path}")
