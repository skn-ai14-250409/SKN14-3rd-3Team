import requests
from bs4 import BeautifulSoup

# Selenium 관련 import
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

urls = [
    # 엘지 세탁기
    "https://search.danawa.com/dsearch.php?query=%EC%97%98%EC%A7%80+%EC%84%B8%ED%83%81%EA%B8%B0&originalQuery=%EC%97%98%EC%A7%80+%EC%84%B8%ED%83%81%EA%B8%B0&checkedInfo=N&volumeType=allvs&page={page}&limit=40&sort=saveDESC&list=list&boost=true&tab=main&addDelivery=N&coupangMemberSort=N&simpleDescOpen=Y&maker=2137&attribute=30846-1019005-OR&mode=simple&isInitTireSmartFinder=N&recommendedSort=N&defaultUICategoryCode=10239280&defaultPhysicsCategoryCode=72%7C73%7C220133%7C0&defaultVmTab=1835&defaultVaTab=160177&isZeroPrice=Y&quickProductYN=N&priceUnitSort=N&priceUnitSortOrder=A",
    # 엘지 건조기
    "https://search.danawa.com/dsearch.php?query=%EC%97%98%EC%A7%80+%EA%B1%B4%EC%A1%B0%EA%B8%B0&originalQuery=%EC%97%98%EC%A7%80+%EA%B1%B4%EC%A1%B0%EA%B8%B0&checkedInfo=N&volumeType=allvs&page={page}&limit=40&sort=saveDESC&list=list&boost=true&tab=main&addDelivery=N&coupangMemberSort=N&simpleDescOpen=Y&maker=2137&attribute=90-518-OR%2C30846-937405-OR&mode=simple&isInitTireSmartFinder=N&recommendedSort=N&defaultUICategoryCode=10221615&defaultPhysicsCategoryCode=72%7C73%7C11163%7C0&defaultVmTab=1020&defaultVaTab=57225&isZeroPrice=Y&quickProductYN=N&priceUnitSort=N&priceUnitSortOrder=A"
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
}

def get_product_names_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    main_div = soup.find('div', class_='main_prodlist main_prodlist_list')
    names = []
    if main_div:
        li_tags = main_div.find_all('li')
        for li in li_tags:
            p_tag = li.find('p', class_='prod_name')
            if p_tag:
                a_tag = p_tag.find('a')
                if a_tag and a_tag.text:
                    last_word = a_tag.text.strip().split(' ')[-1]
                    names.append(last_word)
    return names

def has_page_2(html):
    soup = BeautifulSoup(html, 'html.parser')
    paging = soup.find('div', class_='paging_number_wrap')
    if paging and paging.find('a', {'data-page': '2'}):
        return True
    return False

# 모든 모델명을 담을 리스트
all_product_names = []

# requests + BeautifulSoup 크롤링 (2개 url)
for url in urls:
    url1 = url.format(page=1)
    response1 = requests.get(url1, headers=headers)
    response1.raise_for_status()
    html1 = response1.text
    all_product_names.extend(get_product_names_from_html(html1))

    if has_page_2(html1):
        url2 = url.format(page=2)
        response2 = requests.get(url2, headers=headers)
        response2.raise_for_status()
        html2 = response2.text
        all_product_names.extend(get_product_names_from_html(html2))

# Selenium 크롤링 함수
def get_tower_product_names():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)
    tower_url = "https://prod.danawa.com/list/?cate=10347846"
    driver.get(tower_url)
    time.sleep(3)  # 페이지 로딩 대기

    # spec_list 내 LG전자 체크박스 클릭
    lg_label = driver.find_element(By.CSS_SELECTOR, 'div.spec_list label[title="LG전자"] input[type="checkbox"]')
    driver.execute_script("arguments[0].click();", lg_label)
    time.sleep(2)  # 필터 적용 대기

    # spec_list 내 2025년형 체크박스 클릭
    y2025_label = driver.find_element(By.CSS_SELECTOR, 'div.spec_list label[title="2025년형"] input[type="checkbox"]')
    driver.execute_script("arguments[0].click();", y2025_label)
    time.sleep(3)  # 필터 적용 대기

    html = driver.page_source
    product_names = get_product_names_from_html(html)

    driver.quit()
    return product_names

# Selenium 크롤링 실행 (1개 url)
tower_product_names = get_tower_product_names()
all_product_names.extend(tower_product_names)

# 결과 확인
for name in all_product_names:
    print(name)
print(f"총 추출된 모델명 개수: {len(all_product_names)}")

import csv

# all_product_names 리스트에 모델명이 모두 들어있다고 가정
# 중복 제거 (순서 보존)
unique_names = list(dict.fromkeys(all_product_names))

# CSV 파일로 저장
with open('lg_danawa_all_models.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    for name in unique_names:
        writer.writerow([name])
