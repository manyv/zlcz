from fastapi import FastAPI
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from typing import List
import time

app = FastAPI()

# 输入模型
class SearchRequest(BaseModel):
    query: str

# 输出模型
class SearchResult(BaseModel):
    title: str
    link: str
    snippet: str

# 核心函数：执行 Selenium 搜索并提取数据
def perform_search(query: str) -> List[SearchResult]:
    options = Options()
    #options.add_argument("--headless")  # 无头浏览器
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    results = []
    try:
        driver.get("https://www.google.com")
        time.sleep(2)

        # 接受 cookies
        try:
            agree_button = driver.find_element(By.XPATH, "//button[contains(., '接受') or contains(., '同意') or contains(., 'Accept')]")
            agree_button.click()
            time.sleep(1)
        except:
            pass

        # 输入搜索内容
        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        time.sleep(3)

        # 提取搜索结果
        result_elements = driver.find_elements(By.CLASS_NAME, "MjjYud")
        for element in result_elements[:6]:
            try:
                title = element.find_element(By.CLASS_NAME, "VuuXrf").text
                raw_link = element.find_element(By.CSS_SELECTOR, "cite").text
                link = raw_link.split('›')[0].strip()
                snippet_elem = element.find_element(By.CSS_SELECTOR, "div.VwiC3b")
                snippet = snippet_elem.text
                results.append(SearchResult(title=title, link=link, snippet=snippet))
            except Exception:
                continue
    finally:
        driver.quit()

    return results

# 接口定义
@app.post("/search", response_model=List[SearchResult])
def search(request: SearchRequest):
    return perform_search(request.query)

# 启动服务（如 python thisfile.py）
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
