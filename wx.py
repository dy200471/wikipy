import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


url = "https://wxapp.webportal.top/ajax/wxAppNews_h.jsp"
headers = {
    "Cookie": "cliid=xKEvsSgLbMpC23IQ; grayUrl=; loginCacct=taolitakefu; loginCaid=29041591; loginSacct=yd549061725; loginUseSacct=1; knownModuleDraggable=true; knownRecord=true; infoIssueSysOpen_29041591=true; loginSign=_XsgpZFfB0waLqZ3ldXC0HO9K8hXtI9cJufDlhatsvrYXW7AyQlaFA9JX5u38nqbtGKzftAL8V3mVi4o1CRwoV_9jQQRwHHEl8PSetuxNtQ; _FSESSIONID=W_zTMRLNArmjUVA4; _autoLoginCount=1; _sid4ue=101; enterManage2816405-101=true; todayHasLogin_2=true",
    "User-Agent": "Mozilla/5.0"
}

total_pages = 76
max_workers = 10  # 同时并发的线程数，建议 5~10 之间

def fetch_page(page_no):
    params = {
        "_TOKEN": "28ffb5c61fe7d3b8803a840423017fc9",
        "cmd": "getList",
        "wxappAid": "2816405",
        "wxappId": "101",
        "pageSize": "60",
        "pageNo": str(page_no),
        "groupId": "-1",
        "title": ""
    }

    try:
        res = requests.get(url, params=params, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()
        news_list = data.get("data", {}).get("newsList", [])
        return [
            {"id": item["id"], "title": item["title"]}
            for item in news_list
        ]
    except Exception as e:
        print(f"[第 {page_no} 页] 出错: {e}")
        return []

def main():
    all_items = []
    seen_ids = set()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(fetch_page, page) for page in range(1, total_pages + 1)]

        for future in as_completed(futures):
            result = future.result()
            for item in result:
                if item["id"] not in seen_ids:
                    seen_ids.add(item["id"])
                    all_items.append(item)

    # 排序
    all_items.sort(key=lambda x: x["id"])

    # 保存 JS 文件
    js_code = "const items = " + json.dumps(all_items, indent=2, ensure_ascii=False) + ";"
    with open("news_list.js", "w", encoding="utf-8") as f:
        f.write(js_code)

    print(f"\n✅ 全部完成，共导出 {len(all_items)} 条记录，已保存为 news_list.js")

if __name__ == "__main__":
    main()