from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
import csv
import time
import datetime
import signal
import sys
from bs4 import BeautifulSoup

# 중간 저장용 리스트
data_rows = []

# Ctrl+C 시 중간 저장
def save_on_exit(signal_received, frame):
    print("\n중간 저장 진행...")
    if data_rows:
        with open("n5_words_partial.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data_rows)
        print(f"✅ 중간 저장 완료: n5_words_partial.csv ({len(data_rows)}개 단어)")
    sys.exit(0)

signal.signal(signal.SIGINT, save_on_exit)

# CSV 필드
fieldnames = [
    "id", "level_name", "part_of_speech", "word", "reading", "meaning",
    "example_sentence", "example_translation", "created_at"
]

# 단어 정보 추출 함수
def fetch_n5_words():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        parts = ["noun", "adjective", "adjective_na", "verb"]
        word_id = 1
        for part in parts:
            page = 1
            while True:
                url = f"https://ja.dict.naver.com/#/jlpt/list?level=5&part={part}&page={page}"
                print(f"\n접속: {url}")
                driver.get(url)
                time.sleep(8)

                rows = driver.find_elements("css selector", "li.row")
                if not rows:
                    print("단어 없음, 페이지 종료")
                    break

                print(f"총 {len(rows)}개의 단어 발견")

                for idx, row in enumerate(rows, start=1):
                    try:
                        word_elem = row.find_element("css selector", "div.origin a.link")
                        word = word_elem.text.strip()
                        link = word_elem.get_attribute("href")
                        reading_elem = row.find_element("css selector", "div.origin span.pronunciation")
                        reading = reading_elem.text.strip("[]")
                        meaning_elem = row.find_element("css selector", "ul.mean_list li.mean_item p.mean")
                        pos_elem = meaning_elem.find_element("css selector", "span.word_class")
                        part_of_speech = pos_elem.text.strip()
                        meaning = meaning_elem.text.replace(part_of_speech, "").strip()

                        print(f"\n[{word_id}] 단어: {word}, 품사: {part_of_speech}, 의미: {meaning}")

                        # 예문 추출
                        driver.execute_script("window.open('');")
                        driver.switch_to.window(driver.window_handles[1])
                        driver.get(link)
                        time.sleep(5)

                        example_sentence = ""
                        example_translation = ""
                        try:
                            example_elem = driver.find_element("css selector", "div.example_item p.origin.my_origin")
                            html = example_elem.get_attribute("innerHTML")

                            # BeautifulSoup으로 파싱
                            soup = BeautifulSoup(html, "html.parser")

                            # ruby 태그 처리: rb만 남기고 rt는 무시
                            for ruby in soup.find_all("ruby"):
                                rb_text = ruby.rb.get_text() if ruby.rb else ""
                                ruby.replace_with(rb_text)

                            # 최종 텍스트 (원문만)
                            text_span = soup.find("span", class_="text")
                            if text_span:
                                example_sentence = text_span.get_text(strip=True)
                            else:
                                example_sentence = soup.get_text(strip=True)

                            # 번역문 추출
                            translation_elem = driver.find_element("css selector", "div.example_item p.translate")
                            example_translation = translation_elem.text.strip()
                        except WebDriverException:
                            print("예문 없음")

                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])

                        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        data_rows.append({
                            "id": word_id,
                            "level_name": "N5",
                            "part_of_speech": part_of_speech.lower(),
                            "word": word,
                            "reading": reading,
                            "meaning": meaning,
                            "example_sentence": example_sentence,
                            "example_translation": example_translation,
                            "created_at": created_at
                        })

                        word_id += 1

                    except WebDriverException as e:
                        print(f"단어 추출 실패: {e}")
                        continue

                page += 1

        # 최종 CSV 저장
        with open("n5_words.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data_rows)
        print(f"\n✅ 최종 CSV 저장 완료: n5_words.csv ({len(data_rows)}개 단어)")

    finally:
        driver.quit()

if __name__ == "__main__":
    fetch_n5_words()
