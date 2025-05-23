from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

# 配置 Chrome 无头模式
options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')

# 启动 Chrome 浏览器
driver = webdriver.Chrome(options=options)

try:
    driver.get("https://changes.tarkov-changes.com/")
    time.sleep(5)  # 等待 JavaScript 渲染

    # 抓取所有改动条目
    entries = driver.find_elements(By.CLASS_NAME, "changelog-entry")

    if not entries:
        print("[×] 没有找到改动条目，请确认网页是否正确加载。")

    for entry in entries:
        print(entry.text)
        print("-" * 80)

finally:
    driver.quit()
