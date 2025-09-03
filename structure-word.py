from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def fetch_first_example_item_html():
    # Chrome headless mode 설정
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        url = "https://ja.dict.naver.com/#/entry/jako/a922737407f9496db77ae3fcb8e7226d"
        print(f"접속: {url}")
        driver.get(url)

        # 페이지 로딩 및 JS 렌더링 대기 (필요 시 시간 조정 가능)
        time.sleep(8)

        # 첫 번째 div.example_item 가져오기
        example_div = driver.find_element("css selector", "div.component_entry")
        outer_html = example_div.get_attribute("outerHTML")

        print("\n=== 첫 번째 div.example_item HTML ===")
        print(outer_html)

        # 파일로 저장 (선택사항)
        with open("first_example_item.html", "w", encoding="utf-8") as f:
            f.write(outer_html)
        print("✅ div.example_item HTML 저장 완료: first_example_item.html")

    except Exception as e:
        print("❌ 오류 발생:", e)

    finally:
        driver.quit()

if __name__ == "__main__":
    fetch_first_example_item_html()
