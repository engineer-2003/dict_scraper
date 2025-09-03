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
verb_conjugation_rows = []
adj_conjugation_rows = []

# Ctrl+C 시 중간 저장
def save_on_exit(signal_received, frame):
    print("\n중간 저장 진행...")
    if data_rows:
        with open("n5_words_partial.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames_words)
            writer.writeheader()
            writer.writerows(data_rows)
        print(f"✅ 중간 저장 완료: n5_words_partial.csv ({len(data_rows)}개 단어)")

    if verb_conjugation_rows:
        with open("n5_conjugations_verbs_partial.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames_verb_conj)
            writer.writeheader()
            writer.writerows(verb_conjugation_rows)
        print(f"✅ 중간 저장 완료: n5_conjugations_verbs_partial.csv ({len(verb_conjugation_rows)}개 활용형)")

    if adj_conjugation_rows:
        with open("n5_conjugations_adjectives_partial.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames_adj_conj)
            writer.writeheader()
            writer.writerows(adj_conjugation_rows)
        print(f"✅ 중간 저장 완료: n5_conjugations_adjectives_partial.csv ({len(adj_conjugation_rows)}개 활용형)")

    sys.exit(0)

signal.signal(signal.SIGINT, save_on_exit)

# CSV 필드
fieldnames_words = [
    "id", "level_name", "part_of_speech", "word", "reading", "meaning",
    "example_sentence", "example_translation", "created_at"
]

fieldnames_verb_conj = [
    "id", "word_id", "masu_form", "negative_form", "volitional_form",
    "conditional_form", "imperative_form", "potential_form"
]

fieldnames_adj_conj = [
    "id", "word_id", "mizen_form", "negative_form", "te_form", "past_form",
    "conditional_form", "polite_form", "adverbial_form", "noun_form"
]

# 품사 매핑 (네이버 사전 URL 구조 대응)
part_url_map = {
    "noun": "noun",
    "adjective": "measurement",      # 형용사
    "adjective_na": "pronoun",       # 형용동사
    "verb": "adjective"              # 동사
}

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
        verb_conj_id = 1
        adj_conj_id = 1

        for part in parts:
            url_part = part_url_map[part]
            page = 1

            while True:
                url = f"https://ja.dict.naver.com/#/jlpt/list?level=5&part={url_part}&page={page}"
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

                        # 상세 페이지 열기
                        driver.execute_script("window.open('');")
                        driver.switch_to.window(driver.window_handles[1])
                        driver.get(link)
                        time.sleep(5)

                        # === 예문 추출 ===
                        example_sentence = ""
                        example_translation = ""
                        try:
                            example_elem = driver.find_element("css selector", "div.example_item p.origin.my_origin")
                            html = example_elem.get_attribute("innerHTML")
                            soup = BeautifulSoup(html, "html.parser")
                            for ruby in soup.find_all("ruby"):
                                rb_text = ruby.rb.get_text() if ruby.rb else ""
                                ruby.replace_with(rb_text)
                            text_span = soup.find("span", class_="text")
                            if text_span:
                                example_sentence = text_span.get_text(strip=True)
                            else:
                                example_sentence = soup.get_text(strip=True)
                            translation_elem = driver.find_element("css selector", "div.example_item p.translate")
                            example_translation = translation_elem.text.strip()
                        except WebDriverException:
                            print("예문 없음")

                        # === 활용형 추출 ===
                        html_full = driver.page_source
                        soup = BeautifulSoup(html_full, "html.parser")

                        if part == "verb":
                            masu_form = negative_form = volitional_form = ""
                            conditional_form = imperative_form = potential_form = ""

                            for dt in soup.select("dl.entry_conjugation_list dt.tit"):
                                form_type = dt.get("scrolltitle", "")
                                dd = dt.find_next_sibling("dd")
                                if not dd:
                                    continue
                                form_word = dd.get_text(strip=True)

                                if form_type == "ます형":
                                    masu_form = form_word
                                elif form_type == "부정형":
                                    negative_form = form_word
                                elif form_type == "청유형":
                                    volitional_form = form_word
                                elif form_type == "가정형":
                                    conditional_form = form_word
                                elif form_type == "명령형":
                                    imperative_form = form_word
                                elif form_type == "가능형":
                                    potential_form = form_word

                            verb_conjugation_rows.append({
                                "id": verb_conj_id,
                                "word_id": word_id,
                                "masu_form": masu_form,
                                "negative_form": negative_form,
                                "volitional_form": volitional_form,
                                "conditional_form": conditional_form,
                                "imperative_form": imperative_form,
                                "potential_form": potential_form
                            })
                            verb_conj_id += 1

                        elif part == "adjective":
                            mizen_form = negative_form = te_form = past_form = ""
                            conditional_form = polite_form = adverbial_form = noun_form = ""

                            for dt in soup.select("dl.entry_conjugation_list dt.tit"):
                                form_type = dt.get("scrolltitle", "")
                                dd = dt.find_next_sibling("dd")
                                if not dd:
                                    continue
                                form_word = dd.get_text(strip=True)

                                if form_type == "미연형":
                                    mizen_form = form_word
                                elif form_type == "부정형":
                                    negative_form = form_word
                                elif form_type == "て형":
                                    te_form = form_word
                                elif form_type == "과거형":
                                    past_form = form_word
                                elif form_type == "가정형":
                                    conditional_form = form_word
                                elif form_type == "정중형":
                                    polite_form = form_word

                            adj_conjugation_rows.append({
                                "id": adj_conj_id,
                                "word_id": word_id,
                                "mizen_form": mizen_form,
                                "negative_form": negative_form,
                                "te_form": te_form,
                                "past_form": past_form,
                                "conditional_form": conditional_form,
                                "polite_form": polite_form,
                                "adverbial_form": adverbial_form,
                                "noun_form": noun_form
                            })
                            adj_conj_id += 1

                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])

                        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        # 단어 저장
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
            writer = csv.DictWriter(f, fieldnames=fieldnames_words)
            writer.writeheader()
            writer.writerows(data_rows)
        print(f"\n✅ 최종 CSV 저장 완료: n5_words.csv ({len(data_rows)}개 단어)")

        if verb_conjugation_rows:
            with open("n5_conjugations_verbs.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames_verb_conj)
                writer.writeheader()
                writer.writerows(verb_conjugation_rows)
            print(f"✅ 최종 CSV 저장 완료: n5_conjugations_verbs.csv ({len(verb_conjugation_rows)}개 활용형)")

        if adj_conjugation_rows:
            with open("n5_conjugations_adjectives.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames_adj_conj)
                writer.writeheader()
                writer.writerows(adj_conjugation_rows)
            print(f"✅ 최종 CSV 저장 완료: n5_conjugations_adjectives.csv ({len(adj_conjugation_rows)}개 활용형)")

    finally:
        driver.quit()

if __name__ == "__main__":
    fetch_n5_words()
