from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import pandas as pd


main_url = "https://www.samsung.com/sec/washers-and-dryers/all-washers-and-dryers/"
base_url = "https://www.samsung.com"

options = webdriver.ChromeOptions()
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
driver.get(main_url)
driver.implicitly_wait(10)
time.sleep(2)

# 1. 스크롤을 끝까지 내림
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(2)  # 스크롤 후 로딩 대기

# 2. 더보기 버튼 찾고 클릭
try:
    more_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "div.pf-btn-box button#morePrd"))
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", more_btn)
    time.sleep(1)
    driver.execute_script("arguments[0].click();", more_btn)
    print("더보기 버튼 클릭 완료")
    time.sleep(2)
except Exception as e:
    print("더보기 버튼 클릭 실패 또는 버튼 없음:", e)

# 3. 상세페이지 주소 수집
html = driver.page_source
soup = BeautifulSoup(html, "html.parser")
item_buttons = soup.select("li.item button.btn.btn-d.btn-type2")

detail_urls = []
for btn in item_buttons:
    onclick = btn.get("onclick")
    if onclick:
        start = onclick.find("('") + 2
        end = onclick.find("')", start)
        path = onclick[start:end]
        detail_url = base_url + path
        detail_urls.append(detail_url)
        print(detail_url)

print(f"\n총 수집된 상세페이지 url 개수: {len(detail_urls)}")

# 결과 저장용 리스트
results = []

def get_spec_data(driver, url):
    driver.get(url)
    time.sleep(2)

    # 1. 스크롤을 끝까지 내림
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    # 2. id="specDropBtn"인 a태그 클릭 (스펙 펼치기)
    try:
        spec_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "specDropBtn"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", spec_btn)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", spec_btn)
        time.sleep(2)
    except Exception as e:
        print(f"specDropBtn 클릭 실패: {e}")

    # 3. BeautifulSoup으로 파싱
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    spec_table = soup.find("div", class_="spec-table")
    if not spec_table:
        print("spec-table 없음")
        return

    for dl in spec_table.find_all("dl"):
        dt = dl.find("dt")
        if not dt:
            continue
        dt_text = dt.get_text(strip=True)
        dd = dl.find("dd")
        if not dd:
            continue
        for li in dd.find_all("li"):
            # strong태그 추출
            strong = li.find("strong")
            if strong:
                strong_text = strong.get_text(strip=True)
            else:
                # strong이 없으면 button 하위 텍스트
                button = li.find("button")
                strong_text = button.get_text(strip=True) if button else ""

            # p태그 추출 (& 전까지만)
            p = li.find("p")
            if p:
                p_text = p.get_text(strip=True)
                if '&' in p_text:
                    p_text = p_text.split('&')[0].strip()
            else:
                p_text = ""

            results.append({
                "url": url,
                "dt": dt_text,
                "strong": strong_text,
                "p": p_text
            })


# ===========================
# 수집된 모든 상세페이지에 대해 get_spec_data 적용
# ===========================

for url in detail_urls:
    print(f"\n==== {url} ====")
    get_spec_data(driver, url)

driver.quit()

df = pd.DataFrame(results)
df.to_csv("samsung_washer_specs.csv", index=False, encoding="utf-8-sig")
print("csv 저장 완료!")