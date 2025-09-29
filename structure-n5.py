from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def fetch_n5_noun_rows():
    # Chrome headless mode 설정
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        url = "https://ja.dict.naver.com/#/jlpt/list?level=5&part=noun&page=1"
        print(f"접속: {url}")
        driver.get(url)

        # 페이지 로딩 대기
        time.sleep(8)

        # class="row"인 li 요소들 가져오기
        rows = driver.find_elements("css selector", "li.row")

        print(f"총 {len(rows)}개의 li.row 요소 발견")

        for idx, row in enumerate(rows, start=1):
            html = row.get_attribute("outerHTML")
            print(f"\n=== li.row #{idx} ===")
            print(html)

        # 필요하다면 파일로 저장
        with open("n5_noun_rows.html", "w", encoding="utf-8") as f:
            for row in rows:
                f.write(row.get_attribute("outerHTML") + "\n")
        print("✅ li.row HTML 저장 완료: n5_noun_rows.html")

    finally:
        driver.quit()

if __name__ == "__main__":
    fetch_n5_noun_rows()
