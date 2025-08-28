from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def fetch_n5_noun_html():
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

        page_source = driver.page_source
        print(f"HTML 길이: {len(page_source)}")

        # 앞부분만 콘솔에 출력 (너무 길어질 수 있으니)
        print("\n=== HTML 미리보기 (앞 2000자) ===")
        print(page_source[:2000])

        # 필요하다면 파일로 저장
        with open("n5_noun_page1.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        print("✅ HTML 저장 완료: n5_noun_page1.html")

    finally:
        driver.quit()

if __name__ == "__main__":
    fetch_n5_noun_html()
