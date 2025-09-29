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
        with open("jlpt_words_partial.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames_words)
            writer.writeheader()
            writer.writerows(data_rows)
        print(f"✅ 중간 저장 완료: jlpt_words_partial.csv ({len(data_rows)}개 단어)")

    if verb_conjugation_rows:
        with open("jlpt_conjugations_verbs_partial.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames_verb_conj)
            writer.writeheader()
            writer.writerows(verb_conjugation_rows)
        print(f"✅ 중간 저장 완료: jlpt_conjugations_verbs_partial.csv ({len(verb_conjugation_rows)}개 활용형)")

    if adj_conjugation_rows:
        with open("jlpt_conjugations_adjectives_partial.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames_adj_conj)
            writer.writeheader()
            writer.writerows(adj_conjugation_rows)
        print(f"✅ 중간 저장 완료: jlpt_conjugations_adjectives_partial.csv ({len(adj_conjugation_rows)}개 활용형)")

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

# JLPT 급수
jlpt_levels = ["1", "2", "3", "4", "5"]

# 활용형에서 순수 단어만 추출하는 함수
def extract_conjugation_word(dd_element):
    """
    dd 요소에서 순수한 활용형 단어만 추출 (더보기 버튼 제외)
    """
    try:
        # span.word 요소를 찾아서 텍스트 추출
        word_span = dd_element.find("span", class_="word")
        if word_span:
            # HTML을 파싱해서 루비 태그 처리
            html = str(word_span)
            soup = BeautifulSoup(html, "html.parser")
            
            # 루비 태그가 있으면 rb 텍스트만 사용
            for ruby in soup.find_all("ruby"):
                rb_text = ruby.rb.get_text() if ruby.rb else ""
                ruby.replace_with(rb_text)
            
            # 최종 텍스트 추출
            word_text = soup.get_text(strip=True)
            return word_text
        else:
            # span.word가 없으면 전체 텍스트에서 "더보기" 제거
            full_text = dd_element.get_text(strip=True)
            return full_text.replace("더보기", "").strip()
    except Exception as e:
        print(f"활용형 추출 오류: {e}")
        return ""

# 단어 정보 추출 함수
def fetch_jlpt_words():
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

        # 모든 JLPT 급수에 대해 반복
        for level in jlpt_levels:
            print(f"\n{'='*50}")
            print(f"JLPT {level}급 단어 수집 시작")
            print(f"{'='*50}")
            
            for part in parts:
                url_part = part_url_map[part]
                page = 1

                print(f"\n--- {part} 품사 수집 시작 ---")

                while True:
                    url = f"https://ja.dict.naver.com/#/jlpt/list?level={level}&part={url_part}&page={page}"
                    print(f"\n접속: {url}")
                    driver.get(url)
                    time.sleep(8)

                    rows = driver.find_elements("css selector", "li.row")
                    if not rows:
                        print(f"JLPT {level}급 {part} 품사 페이지 {page}: 단어 없음, 다음 품사로 이동")
                        break

                    print(f"JLPT {level}급 {part} 품사 페이지 {page}: {len(rows)}개의 단어 발견")

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

                            print(f"[{word_id}] N{level} {word} ({reading}) - {part_of_speech}: {meaning[:30]}...")

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
                                print(f"  -> 예문 없음")

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
                                    
                                    # 순수 단어만 추출
                                    form_word = extract_conjugation_word(dd)

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

                                if any([masu_form, negative_form, volitional_form, conditional_form, imperative_form, potential_form]):
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
                                    
                                    # 순수 단어만 추출
                                    form_word = extract_conjugation_word(dd)

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

                                if any([mizen_form, negative_form, te_form, past_form, conditional_form, polite_form]):
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
                                "level_name": f"N{level}",
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
                            print(f"  -> 단어 추출 실패: {e}")
                            continue

                    page += 1

                print(f"--- {part} 품사 수집 완료 ---")

            print(f"\nJLPT {level}급 수집 완료!")
            print(f"현재까지 총 {len(data_rows)}개 단어 수집됨")

        # 최종 CSV 저장
        with open("jlpt_all_words.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames_words)
            writer.writeheader()
            writer.writerows(data_rows)
        print(f"\n✅ 최종 CSV 저장 완료: jlpt_all_words.csv ({len(data_rows)}개 단어)")

        if verb_conjugation_rows:
            with open("jlpt_all_conjugations_verbs.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames_verb_conj)
                writer.writeheader()
                writer.writerows(verb_conjugation_rows)
            print(f"✅ 최종 CSV 저장 완료: jlpt_all_conjugations_verbs.csv ({len(verb_conjugation_rows)}개 활용형)")

        if adj_conjugation_rows:
            with open("jlpt_all_conjugations_adjectives.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames_adj_conj)
                writer.writeheader()
                writer.writerows(adj_conjugation_rows)
            print(f"✅ 최종 CSV 저장 완료: jlpt_all_conjugations_adjectives.csv ({len(adj_conjugation_rows)}개 활용형)")

        # 급수별 통계 출력
        print(f"\n{'='*50}")
        print("수집 통계")
        print(f"{'='*50}")
        for level in jlpt_levels:
            level_count = len([row for row in data_rows if row['level_name'] == f'N{level}'])
            print(f"N{level}급: {level_count}개 단어")
        print(f"총 단어 수: {len(data_rows)}개")
        print(f"동사 활용형: {len(verb_conjugation_rows)}개")
        print(f"형용사 활용형: {len(adj_conjugation_rows)}개")

    finally:
        driver.quit()

if __name__ == "__main__":
    fetch_jlpt_words()
