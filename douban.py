from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import openpyxl

def extract_field(info_text, label):
    for line in info_text.split('\n'):
        if line.startswith(label):
            return line.replace(label, '').strip()
    return "无"

def save_to_excel(data, filename="douban_movies.xlsx"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Movies_info"

    headers = ["movie_id","tile","director", "screenwriter", "cast", "type", "country", "language", "release_date",
               "duration", "title_alternate", "IMDb", "rate", "rate_num","url"]
    ws.append(headers)

    for idx, item in enumerate(data, start=1):
        ws.append([
            idx,
            item.get("title", "无"),
            item.get("director", "无"),
            item.get("screenwriter", "无"),
            item.get("cast", "无"),
            item.get("genres", "无"),
            item.get("country", "无"),
            item.get("language", "无"),
            item.get("release_date", "无"),
            item.get("duration", "无"),
            item.get("title_alternate", "无"),
            item.get("IMDb", "无"),
            item.get("rate", "无"),
            item.get("rate_num", "无"),
            item.get("url","无")
        ])
    wb.save(filename)
    print(f"数据已保存到 {filename}")

def main():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    wait = WebDriverWait(driver, 15)
    driver.get("https://movie.douban.com/explore")
    driver.maximize_window()

    # 筛选地区和年代
    wait.until(EC.element_to_be_clickable((By.XPATH, '//ul[@class="explore-menu"]/li[1]'))).click()
    time.sleep(1)
    wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="base-selector-title"]/span[text()="地区"]'))).click()
    time.sleep(1)
    wait.until(EC.element_to_be_clickable((By.XPATH, '//li[@class="tag-group-item"]/span/span[text()="中国大陆"]'))).click()
    time.sleep(1)
    wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="base-selector-title"]/span[text()="年代"]'))).click()
    time.sleep(1)
    wait.until(EC.element_to_be_clickable((By.XPATH, '//li[@class="tag-group-item"]/span/span[text()="2024"]'))).click()
    time.sleep(2)

    # 点击“加载更多”次数
    MAX_LOAD_MORE = 150
    for i in range(MAX_LOAD_MORE):
        try:
            load_more_btn = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'div.subject-list-more > button.drc-button')))
            load_more_btn.click()
            print(f"点击加载更多第{i + 1}次")
            time.sleep(5)
        except Exception:
            print("无更多加载按钮或按钮不可点击，停止加载更多")
            break
    # while True:
    #     try:
    #         load_more_btn = wait.until(EC.element_to_be_clickable(
    #             (By.CSS_SELECTOR, 'div.subject-list-more > button.drc-button')))
    #         load_more_btn.click()
    #         print("点击加载更多按钮")
    #         time.sleep(3)  # 等待新电影加载出来
    #     except:
    #         print("没有更多加载按钮或不可点击，停止加载更多")
    #         break

    movie_list = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'subject-list-list')))
    movie_items = movie_list.find_elements(By.TAG_NAME, 'li')
    print(f"加载完成，共有{len(movie_items)}部电影")

    all_movies_info = []
    main_window = driver.current_window_handle

    for idx, movie_li in enumerate(movie_items):
        try:
            movie_link = movie_li.find_element(By.TAG_NAME, 'a')
            movie_url = movie_link.get_attribute("href")

            driver.execute_script("window.open(arguments[0]);", movie_url)
            driver.switch_to.window(driver.window_handles[-1])

            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h1 span[property="v:itemreviewed"]')))
            time.sleep(1)

            movie_info = {
                "title": "未获取到",
                "director": "无",
                "screenwriter": "无",
                "cast": "无",
                "genres": "无",
                "country": "无",
                "language": "无",
                "release_date": "无",
                "duration": "无",
                "title_alternate": "无",
                "IMDb": "无",
                "rate": "无",
                "rate_num": "无",
                "url": movie_url  # 加这里
            }

            try:
                movie_info["title"] = driver.find_element(By.CSS_SELECTOR, 'h1 span[property="v:itemreviewed"]').text.strip()
            except:
                pass

            try:
                info_div = wait.until(EC.presence_of_element_located((By.ID, "info")))
                info_text = info_div.text
                movie_info.update({
                    "director": extract_field(info_text, "导演:"),
                    "screenwriter": extract_field(info_text, "编剧:"),
                    "cast": extract_field(info_text, "主演:"),
                    "genres": extract_field(info_text, "类型:"),
                    "country": extract_field(info_text, "制片国家/地区:"),
                    "language": extract_field(info_text, "语言:"),
                    "release_date": extract_field(info_text, "上映日期:"),
                    "duration": extract_field(info_text, "片长:"),
                    "title_alternate": extract_field(info_text, "又名:"),
                    "IMDb": extract_field(info_text, "IMDb:")
                })
            except:
                pass

            try:
                rating_div = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "rating_self")))
                movie_info["rate"] = rating_div.find_element(By.CSS_SELECTOR, 'strong.rating_num').text.strip()
                movie_info["rate_num"] = rating_div.find_element(By.CSS_SELECTOR, 'span[property="v:votes"]').text.strip()
            except:
                pass

            all_movies_info.append(movie_info)

        except Exception as e:
            print(f"第{idx + 1}个电影抓取失败: {e}")

        finally:
            driver.close()
            driver.switch_to.window(main_window)
            time.sleep(1)

    driver.quit()
    save_to_excel(all_movies_info)

if __name__ == "__main__":
    main()
