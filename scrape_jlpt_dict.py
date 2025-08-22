from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import numpy as np
import pandas as pd
import time

# chrome headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# 결과 데이터 저장용 배열
total_data = []

# 품사별 분류 (명사, 형용사, 형용동사, 동사)
word_types = {
    "noun": "명사",
    "adjective": "형용사", 
    "adjectival_verb": "형용동사",
    "verb": "동사"
}

# JLPT 급수
levels = ["1", "2", "3", "4", "5"]

def get_word_details(driver, word_element):
    """개별 단어의 상세 정보를 가져오는 함수"""
    try:
        # 단어 클릭
        word_element.click()
        time.sleep(1)
        
        # 상세 정보 대기
        wait = WebDriverWait(driver, 10)
        
        # 단어 정보 추출
        word_text = ""
        furigana = ""
        meaning = ""
        example = ""
        
        try:
            # 단어와 후리가나 추출
            word_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".mean_item")))
            word_text = word_elem.get_attribute("data-items") or word_elem.text
            
            # 후리가나 추출 (있는 경우)
            furigana_elems = driver.find_elements(By.CSS_SELECTOR, ".mean_item ruby rt")
            if furigana_elems:
                furigana = furigana_elems[0].text
                
            # 뜻 추출
            meaning_elems = driver.find_elements(By.CSS_SELECTOR, ".mean_list .mean_item .mean_desc")
            if meaning_elems:
                meaning = meaning_elems[0].text
                
            # 예문 추출
            example_elems = driver.find_elements(By.CSS_SELECTOR, ".example_item")
            if example_elems:
                example = example_elems[0].text
                
        except Exception as e:
            print(f"상세 정보 추출 오류: {e}")
            
        return word_text, furigana, meaning, example
        
    except Exception as e:
        print(f"단어 클릭 오류: {e}")
        return "", "", "", ""

def scrape_jlpt_words():
    """JLPT 단어 스크래핑 메인 함수"""
    
    for level in levels:
        print(f"=== JLPT {level}급 단어 수집 시작 ===")
        
        for word_type, type_name in word_types.items():
            print(f"품사: {type_name} ({word_type})")
            page = 1
            
            while True:
                driver = webdriver.Chrome(options=chrome_options)
                
                try:
                    # URL 생성
                    url = f"https://ja.dict.naver.com/#/jlpt/list?level={level}&part={word_type}&page={page}"
                    driver.get(url)
                    
                    # 페이지 로딩 대기
                    wait = WebDriverWait(driver, 10)
                    time.sleep(3)
                    
                    # 단어 목록 요소 찾기
                    try:
                        word_list = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#my_jlpt_list_template")))
                        word_items = driver.find_elements(By.CSS_SELECTOR, "#my_jlpt_list_template .mean_item")
                        
                        if not word_items:
                            print(f"페이지 {page}에 단어가 없습니다. 다음 품사로...")
                            break
                            
                        print(f"페이지 {page}: {len(word_items)}개 단어 발견")
                        
                        # 각 단어에 대해 상세 정보 수집
                        for idx, word_item in enumerate(word_items):
                            try:
                                # 기본 단어 정보 추출
                                word_text = word_item.text.split('\n')[0] if word_item.text else ""
                                
                                # 단어 클릭하여 상세 정보 가져오기
                                detailed_word, furigana, meaning, example = get_word_details(driver, word_item)
                                
                                if not detailed_word:
                                    detailed_word = word_text
                                
                                # 데이터 저장
                                word_data = {
                                    "급수": level,
                                    "품사": type_name,
                                    "단어": detailed_word,
                                    "후리가나": furigana,
                                    "뜻": meaning,
                                    "예문": example
                                }
                                
                                total_data.append(word_data)
                                print(f"  {idx+1}. {detailed_word} ({furigana}) - {meaning[:30]}...")
                                
                                # 뒤로 가기 또는 목록으로 돌아가기
                                driver.back()
                                time.sleep(1)
                                
                                # 목록 다시 로드
                                word_items = driver.find_elements(By.CSS_SELECTOR, "#my_jlpt_list_template .mean_item")
                                
                            except Exception as e:
                                print(f"단어 처리 오류: {e}")
                                continue
                                
                        page += 1
                        
                    except Exception as e:
                        print(f"페이지 로딩 오류: {e}")
                        break
                        
                except Exception as e:
                    print(f"전체 페이지 오류: {e}")
                    break
                    
                finally:
                    driver.quit()
                    
                # 페이지 간 대기
                time.sleep(2)

def save_to_excel():
    """데이터를 엑셀 파일로 저장"""
    if total_data:
        df = pd.DataFrame(total_data)
        filename = "naver_jlpt_words_detailed.xlsx"
        df.to_excel(filename, index=False, encoding='utf-8-sig')
        print(f"\n=== 데이터 저장 완료 ===")
        print(f"파일명: {filename}")
        print(f"총 수집된 단어 수: {len(total_data)}")
        
        # 급수별, 품사별 통계
        stats = df.groupby(['급수', '품사']).size().unstack(fill_value=0)
        print("\n=== 수집 통계 ===")
        print(stats)
    else:
        print("수집된 데이터가 없습니다.")

if __name__ == "__main__":
    try:
        scrape_jlpt_words()
        save_to_excel()
        print("\n스크래핑 완료!")
        
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단되었습니다.")
        save_to_excel()  # 중단되어도 현재까지 수집한 데이터는 저장
        
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
        save_to_excel()  # 오류가 발생해도 현재까지 수집한 데이터는 저장
