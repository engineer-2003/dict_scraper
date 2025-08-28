from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import csv
import re

def fetch_n5_noun_to_csv():
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
        time.sleep(8)  # 페이지 로딩 대기

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # 단어 리스트
        word_items = soup.select("ul#my_jlpt_list_template li.row")
        data_list = []

        for item in word_items:
            word = item.select_one(".origin .link").text.strip()
            pronunciation = item.select_one(".origin .pronunciation").text.strip()

            # 의미 추출
            meanings = item.select(".mean_list .mean_item .mean")
            first_mean = ""
            if meanings:
                text = meanings[0].get_text(strip=True)
                # 품사 제거
                cls = meanings[0].select_one(".word_class")
                if cls:
                    text = text.replace(cls.text.strip(), "")
                # 첫 번째 의미만 가져오기 (숫자 제거)
                first_mean = re.split(r'\d+\.', text)[1].strip() if re.search(r'\d+\.', text) else text

            data_list.append({
                "word": word,
                "pronunciation": pronunciation,
                "meaning": first_mean
            })

        # CSV 저장
        csv_file = "n5_nouns.csv"
        with open(csv_file, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["word", "pronunciation", "meaning"])
            writer.writeheader()
            for d in data_list:
                writer.writerow(d)

        print(f"✅ CSV 저장 완료: {csv_file}")

    finally:
        driver.quit()

if __name__ == "__main__":
    fetch_n5_noun_to_csv()
