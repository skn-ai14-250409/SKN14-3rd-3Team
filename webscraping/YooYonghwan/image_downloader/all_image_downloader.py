import pandas as pd
import requests
import os
import re
import time
import json
from urllib.parse import urlparse, urljoin
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from datetime import datetime, timedelta


class SamsungWasherDryerScraper:
    def __init__(self):
        self.base_url = "https://www.samsung.com/sec/washers-and-dryers/all-washers-and-dryers/"
        self.images_folder = './samsung_img'
        self.csv_file = 'samsung_washer_dryer_products.csv'
        self.setup_folders()
        self.driver = None

        # 진행상태 추적 변수들
        self.total_images_downloaded = 0
        self.download_start_time = None
        self.last_progress_time = None

    def setup_folders(self):
        """이미지 다운로드 폴더 생성"""
        if not os.path.exists(self.images_folder):
            os.makedirs(self.images_folder)
            print(f"📁 폴더 생성: {self.images_folder}")
        else:
            print(f"📁 폴더 확인: {self.images_folder}")

    def setup_driver(self):
        """Selenium 웹드라이버 설정"""
        print("🚀 웹드라이버 설정 시작...")
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # 디버깅을 위해 비활성화
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        # 다운로드 설정
        prefs = {
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_settings.popups": 0,
            "profile.default_content_setting_values.automatic_downloads": 1
        }
        chrome_options.add_experimental_option("prefs", prefs)

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        print("✅ 웹드라이버 초기화 완료")

    def close_driver(self):
        """웹드라이버 종료"""
        if self.driver:
            self.driver.quit()
            print("🛑 웹드라이버 종료")

    def handle_out_of_stock_filter(self):
        """품절상품 제외 필터 해제"""
        print("🔍 품절상품 제외 버튼 탐색 중...")

        try:
            exclude_sold_out_label = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "label[for='toggle-check-on-pc']"))
            )
            print("   ✅ 품절상품 제외 체크박스 라벨 감지")

            exclude_sold_out_checkbox = self.driver.find_element(By.CSS_SELECTOR, "input#toggle-check-on-pc")

            if exclude_sold_out_checkbox.is_selected():
                exclude_sold_out_label.click()
                print("   ✅ 품절상품 제외 체크박스 해제 완료")
            else:
                print("   ℹ️  품절상품 제외 체크박스가 이미 해제되어 있음")

            time.sleep(2)

        except Exception as e:
            print(f"   ❌ 품절상품 제외 체크박스 처리 실패: {str(e)}")

    def scroll_and_load_all_products(self):
        """더보기 버튼 클릭으로 모든 제품 로드"""
        print("📜 더보기 버튼 클릭으로 모든 제품 로드 시작...")

        click_count = 0
        max_clicks = 10

        while click_count < max_clicks:
            try:
                more_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-type1.btn-d.btn-readmore"))
                )

                print(f"   [{click_count + 1}] ✅ 더보기 버튼 감지")

                try:
                    current_page_elem = self.driver.find_element(By.ID, "presentPageCount")
                    total_pages_elem = self.driver.find_element(By.ID, "totalPageCount")

                    current_page_text = current_page_elem.text.strip()
                    total_pages_text = total_pages_elem.text.strip()

                    if current_page_text and total_pages_text:
                        current_page = int(current_page_text)
                        total_pages = int(total_pages_text)
                        print(f"      📄 현재 페이지: {current_page}/{total_pages}")

                        if current_page >= total_pages:
                            print("      ✅ 마지막 페이지에 도달했습니다.")
                            break

                except Exception as e:
                    print(f"      ⚠️  페이지 번호 확인 실패: {str(e)} - 계속 진행")

                if not more_button.is_displayed() or not more_button.is_enabled():
                    print("      ❌ 더보기 버튼이 클릭할 수 없는 상태")
                    break

                self.driver.execute_script("arguments[0].click();", more_button)
                print(f"      🖱️  더보기 버튼 클릭 완료")
                click_count += 1

                time.sleep(3)

                try:
                    new_more_button = self.driver.find_element(By.CSS_SELECTOR,
                                                               "button.btn.btn-type1.btn-d.btn-readmore")
                    self.driver.execute_script("arguments[0].scrollIntoView();", new_more_button)
                except:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                time.sleep(2)

            except TimeoutException:
                print(f"   ✅ 더보기 버튼을 찾을 수 없음 - 모든 제품 로드 완료")
                break
            except Exception as e:
                print(f"   ❌ 더보기 버튼 처리 실패: {str(e)}")
                break

        print(f"✅ 더보기 버튼 클릭 완료. 총 {click_count}번 클릭")
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        print("🎯 모든 제품 로딩 완료!")

    def extract_product_names_from_html(self, parent_element):
        """HTML에서 한글 모델명과 영문 모델명 추출"""
        print(f"      🔍 HTML에서 모델명 추출 시도...")

        korean_name = ""
        english_code = ""

        try:
            # 한글 모델명 찾기: prd-name 클래스
            korean_element = parent_element.select_one('span.prd-name')
            if korean_element:
                korean_name = korean_element.get_text(strip=True)
                print(f"         📋 한글 모델명: {korean_name}")

            # 영문 모델명 찾기: prd-num 클래스
            english_element = parent_element.select_one('span.prd-num')
            if english_element:
                english_code = english_element.get_text(strip=True)
                print(f"         📋 영문 모델명: {english_code}")

            # 대체 방법: 다른 선택자들도 시도
            if not korean_name:
                # title 속성에서 찾기
                title_elements = parent_element.select('[title]')
                for elem in title_elements:
                    title = elem.get('title', '').strip()
                    if title and any(keyword in title for keyword in ['Bespoke', 'AI', '콤보', 'kg']):
                        korean_name = title
                        print(f"         📋 한글 모델명 (title): {korean_name}")
                        break

            if not english_code:
                # 영문 코드 패턴으로 찾기
                all_text = parent_element.get_text()
                model_patterns = [
                    r'WD[0-9A-Z]{8,}',
                    r'WF[0-9A-Z]{8,}',
                    r'DV[0-9A-Z]{8,}',
                    r'WA[0-9A-Z]{8,}'
                ]
                for pattern in model_patterns:
                    matches = re.findall(pattern, all_text)
                    if matches:
                        english_code = matches[0]
                        print(f"         📋 영문 모델명 (패턴): {english_code}")
                        break

        except Exception as e:
            print(f"         ⚠️ 모델명 추출 오류: {str(e)}")

        return korean_name, english_code

    def get_all_products_improved(self):
        """개선된 전체 제품 정보 수집"""
        print("📊 전체 제품 정보 수집 중...")

        try:
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            # 더 많은 선택자 시도
            product_selectors = [
                'div.item-inner a[href*="washers-and-dryers"]',
                'div.item-inner > div.card-detail > a',
                '.product-card a',
                '.pd-item a',
                '.product-item a',
                'a[href*="/washers-and-dryers/"]',
                'div.card-detail a'
            ]

            product_elements = []
            for selector in product_selectors:
                elements = soup.select(selector)
                if elements:
                    product_elements = elements
                    print(f"   ✅ 제품 요소 발견: {selector} ({len(elements)}개)")
                    break

            if not product_elements:
                print("   ❌ 제품 요소를 찾을 수 없음")
                return []

            products = []
            max_products = len(product_elements)  # 모든 제품 처리
            print(f"   📦 전체 {max_products}개 제품 처리 시작...")

            for i in range(max_products):
                try:
                    element = product_elements[i]
                    print(f"\n   [{i + 1:2d}] 제품 정보 추출 중...")

                    # href 추출 및 정리
                    href = element.get('href', '')
                    if "'" in href:
                        relative_link = href.split("'")[1]
                    else:
                        relative_link = href

                    if not relative_link.startswith('http'):
                        product_link = urljoin("https://www.samsung.com", relative_link)
                    else:
                        product_link = relative_link

                    print(f"        완전한 URL: {product_link}")

                    # 부모 요소에서 한글/영문 모델명 추출
                    parent_div = element.find_parent('div', class_='item-inner')
                    if parent_div:
                        korean_name, english_code = self.extract_product_names_from_html(parent_div)
                    else:
                        korean_name, english_code = "", ""

                    if product_link and (korean_name or english_code):
                        product_info = {
                            'index': i + 1,
                            'korean_name': korean_name,
                            'english_code': english_code,
                            'product_link': product_link,
                            'image_url': ""
                        }
                        products.append(product_info)
                        print(f"        ✅ 제품 정보 추가 완료")
                    else:
                        print(f"        ❌ 필수 정보 누락")

                except Exception as e:
                    print(f"        ❌ 제품 {i + 1} 정보 추출 실패: {str(e)}")
                    continue

            print(f"\n✅ {len(products)}개 제품 정보 추출 완료")
            return products

        except Exception as e:
            print(f"❌ 제품 정보 추출 중 오류: {str(e)}")
            return []

    def estimate_total_images(self, products):
        """전체 예상 이미지 수 계산 (대략적)"""
        # 제품당 평균 색상 수와 슬라이드 수를 추정
        avg_colors_per_product = 3  # 평균 색상 수
        avg_slides_per_color = 4  # 색상당 평균 슬라이드 수
        estimated_total = len(products) * avg_colors_per_product * avg_slides_per_color
        return estimated_total

    def format_time_duration(self, seconds):
        """초를 시:분:초 형태로 포맷"""
        if seconds < 60:
            return f"{seconds:.1f}초"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            remaining_seconds = int(seconds % 60)
            return f"{minutes}분 {remaining_seconds}초"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            remaining_seconds = int(seconds % 60)
            return f"{hours}시간 {minutes}분 {remaining_seconds}초"

    def print_download_progress(self, current_product, total_products, current_color="", total_colors=0):
        """다운로드 진행상태 출력"""
        if self.download_start_time is None:
            return

        current_time = time.time()
        elapsed_time = current_time - self.download_start_time

        # 제품 진행률
        product_progress = (current_product / total_products) * 100

        # 속도 계산 (이미지/초)
        if elapsed_time > 0:
            download_speed = self.total_images_downloaded / elapsed_time
        else:
            download_speed = 0

        # 예상 남은 시간 (단순 추정)
        if download_speed > 0 and current_product < total_products:
            remaining_products = total_products - current_product
            estimated_remaining_time = (remaining_products / current_product) * elapsed_time
        else:
            estimated_remaining_time = 0

        # 진행상태 바 생성
        bar_length = 30
        filled_length = int(bar_length * current_product // total_products)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)

        color_info = f" | 색상: {current_color}" if current_color else ""

        print(f"\n📈 [다운로드 진행상태]")
        print(f"   진행률: [{bar}] {product_progress:.1f}% ({current_product}/{total_products}){color_info}")
        print(f"   다운로드 완료: {self.total_images_downloaded}개 이미지")
        print(f"   경과시간: {self.format_time_duration(elapsed_time)}")
        print(f"   다운로드 속도: {download_speed:.1f}개/초")
        if estimated_remaining_time > 0:
            print(f"   예상 남은 시간: {self.format_time_duration(estimated_remaining_time)}")

    def download_all_color_slide_images(self, products):
        """리스트에서 직접 모든 색상의 모든 슬라이드 이미지 다운로드"""
        print(f"\n📸 전체 {len(products)}개 제품의 모든 색상별 슬라이드 이미지 다운로드 시작...")
        print("=" * 60)

        # 다운로드 시작 시간 기록
        self.download_start_time = time.time()
        self.total_images_downloaded = 0

        # 예상 총 이미지 수 출력
        estimated_total = self.estimate_total_images(products)
        print(f"📊 예상 총 이미지 수: 약 {estimated_total}개")
        print(f"⏰ 다운로드 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        total_success = 0

        for i in range(len(products)):
            product = products[i]

            try:
                print(f"\n🖼️  [{i + 1}/{len(products)}] 제품 처리 중 (리스트 페이지에서)")
                print(f"      한글명: {product['korean_name'][:30]}...")
                print(f"      영문코드: {product['english_code']}")

                # 진행상태 출력
                self.print_download_progress(i + 1, len(products))

                # 매번 새로 제품 아이템 찾기
                product_items = self.find_product_items()
                if i >= len(product_items):
                    print(f"      ❌ 제품 {i + 1}을 찾을 수 없음")
                    continue

                product_item = product_items[i]

                # 제품 아이템을 화면에 보이도록 스크롤
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth'});", product_item)
                time.sleep(2)

                # 색상 옵션 찾기
                color_options = self.find_color_options_in_item(product_item)

                if not color_options:
                    print(f"      ⚠️ 색상 옵션을 찾을 수 없음 - 기본 슬라이드만 다운로드")
                    # 기본 색상으로 슬라이드 다운로드
                    slide_count = self.download_item_slide_images(
                        product_item,
                        product['korean_name'],
                        product['english_code'],
                        "기본색상"
                    )
                    total_success += slide_count
                    continue

                print(f"      🎨 발견된 색상 옵션: {len(color_options)}개")

                # 각 색상별로 슬라이드 이미지 다운로드
                for color_idx in range(len(color_options)):
                    try:
                        # 매번 새로 색상 옵션들 찾기
                        current_product_items = self.find_product_items()
                        if i >= len(current_product_items):
                            break
                        current_product_item = current_product_items[i]
                        current_color_options = self.find_color_options_in_item(current_product_item)

                        if color_idx >= len(current_color_options):
                            break

                        color_option = current_color_options[color_idx]

                        # 색상명 추출
                        color_name = self.extract_color_name_safe(color_option, color_idx)
                        print(f"\n      [{color_idx + 1}/{len(current_color_options)}] 색상: {color_name}")

                        # 색상별 진행상태 출력
                        self.print_download_progress(i + 1, len(products), color_name, len(current_color_options))

                        # 색상 클릭
                        try:
                            # input radio 버튼 찾아서 클릭
                            parent_li = color_option.find_element(By.XPATH, "./ancestor::li[1]")
                            radio_input = parent_li.find_element(By.CSS_SELECTOR, "input[type='radio']")
                            self.driver.execute_script("arguments[0].click();", radio_input)
                            print(f"         ✅ 색상 라디오 버튼 클릭")

                            time.sleep(4)  # 이미지 로딩 대기
                        except Exception as e:
                            print(f"         ⚠️ 색상 클릭 실패: {str(e)}")
                            continue

                        # 다시 제품 아이템 찾기
                        updated_product_items = self.find_product_items()
                        if i < len(updated_product_items):
                            updated_product_item = updated_product_items[i]

                            # 해당 색상의 모든 슬라이드 이미지 다운로드
                            slide_count = self.download_item_slide_images(
                                updated_product_item,
                                product['korean_name'],
                                product['english_code'],
                                color_name
                            )
                            total_success += slide_count

                        time.sleep(2)

                    except Exception as e:
                        print(f"         ❌ 색상 {color_idx + 1} 처리 실패: {str(e)}")

                time.sleep(2)

            except Exception as e:
                print(f"      ❌ 제품 {i + 1} 처리 실패: {str(e)}")

        # 최종 완료 상태 출력
        total_time = time.time() - self.download_start_time
        print(f"\n" + "=" * 60)
        print(f"✅ 전체 슬라이드 이미지 다운로드 완료!")
        print(f"📊 최종 통계:")
        print(f"   - 다운로드된 이미지: {total_success}개")
        print(f"   - 총 소요시간: {self.format_time_duration(total_time)}")
        print(f"   - 평균 다운로드 속도: {total_success / total_time:.1f}개/초")
        print(f"   - 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return total_success

    def find_product_items(self):
        """현재 페이지에서 제품 아이템들 찾기"""
        product_selectors = ['.item-inner', '.product-item', '[class*="item"]', '.product', '.prd-item']

        for selector in product_selectors:
            try:
                items = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if items:
                    return items
            except:
                continue
        return []

    def find_color_options_in_item(self, product_item):
        """특정 제품 아이템 내에서 색상 옵션 찾기"""
        color_selectors = [
            '.itm-color-object',
            '.color-option',
            '.pd-g-color-chip',
            '.color-chip',
            '.pd-color-chip',
            '[class*="color"][class*="chip"]',
            '[data-omni*="color"]',
            '.color-selector'
        ]

        for selector in color_selectors:
            try:
                elements = product_item.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"         ✅ 색상 옵션 발견 (셀렉터: {selector})")
                    return elements
            except:
                continue

        return []

    def extract_color_name_safe(self, color_element, index):
        """안전한 색상명 추출 (data-itemnm 우선 사용)"""
        try:
            color_name = ""

            # 1. 부모 input의 data-itemnm 속성에서 추출
            try:
                parent_li = color_element.find_element(By.XPATH, "./ancestor::li[1]")
                input_element = parent_li.find_element(By.CSS_SELECTOR, "input[type='radio']")
                data_itemnm = input_element.get_attribute('data-itemnm')
                if data_itemnm:
                    color_name = data_itemnm.strip()
                    print(f"         📋 색상명 (data-itemnm): {color_name}")
            except:
                pass

            # 2. data-omni 속성에서 추출
            if not color_name:
                try:
                    data_omni = color_element.get_attribute('data-omni')
                    if data_omni and '|' in data_omni:
                        color_name = data_omni.split('|')[0].replace('color_', '').strip()
                        print(f"         📋 색상명 (data-omni): {color_name}")
                except:
                    pass

            # 3. 텍스트 내용에서 추출
            if not color_name:
                try:
                    text = color_element.text.strip()
                    if text:
                        color_name = text
                        print(f"         📋 색상명 (text): {color_name}")
                except:
                    pass

            # 색상명이 없으면 기본값 사용
            if not color_name:
                color_name = f"색상{index + 1}"

            # 파일명에 사용할 수 없는 문자 제거
            color_name = re.sub(r'[<>:"/\\|?*]', '_', color_name)
            color_name = re.sub(r'\s+', '_', color_name)

            return color_name

        except Exception as e:
            print(f"         ⚠️ 색상명 추출 실패: {str(e)}")
            return f"색상{index + 1}"

    def download_item_slide_images(self, product_item, korean_name, english_code, color_name):
        """제품 아이템에서 특정 색상의 모든 슬라이드 이미지 다운로드 - 개선된 버전"""
        try:
            print(f"         🔍 슬라이드 이미지 탐색 중...")

            # 슬라이드 페이지네이션 버튼 찾기
            pagination_buttons = product_item.find_elements(By.CSS_SELECTOR, ".swiper-pagination-dot")

            if not pagination_buttons:
                print(f"         ⚠️ 페이지네이션 없음 - 현재 이미지들 수집")
                return self.download_current_images_from_item(product_item, korean_name, english_code, color_name)

            print(f"         ✅ 페이지네이션 버튼 발견: {len(pagination_buttons)}개")
            success_count = 0
            downloaded_urls = set()  # 중복 URL 방지

            # 각 슬라이드별 이미지 다운로드
            for slide_idx in range(len(pagination_buttons)):
                try:
                    print(f"         [{slide_idx + 1}/{len(pagination_buttons)}] 슬라이드 처리 중...")

                    # 페이지네이션 버튼 다시 찾기 (DOM 변경 대비)
                    current_buttons = product_item.find_elements(By.CSS_SELECTOR, ".swiper-pagination-dot")
                    if slide_idx >= len(current_buttons):
                        break

                    button = current_buttons[slide_idx]

                    # 슬라이드 버튼 클릭
                    self.driver.execute_script("arguments[0].click();", button)
                    print(f"            ✅ 슬라이드 {slide_idx + 1} 버튼 클릭")
                    time.sleep(3)  # 이미지 로딩 충분한 대기

                    # 현재 활성화된 슬라이드의 이미지 찾기
                    # 여러 방법으로 현재 표시된 이미지 찾기
                    image_selectors = [
                        "img[src*='samsung.com'][src*='kdp/goods']",  # Samsung 제품 이미지
                        ".swiper-slide-active img",  # 활성 슬라이드의 이미지
                        ".swiper-slide img",  # 모든 슬라이드 이미지
                        "img[src*='images.samsung.com']"  # Samsung 이미지 도메인
                    ]

                    current_image = None
                    for selector in image_selectors:
                        try:
                            images = product_item.find_elements(By.CSS_SELECTOR, selector)
                            for img in images:
                                image_url = img.get_attribute('src')
                                if (image_url and 'samsung.com' in image_url
                                        and 'kdp/goods' in image_url
                                        and image_url not in downloaded_urls):
                                    current_image = img
                                    break
                            if current_image:
                                break
                        except:
                            continue

                    if current_image:
                        image_url = current_image.get_attribute('src')
                        if image_url and image_url not in downloaded_urls:
                            # 고화질 이미지 URL로 변경
                            image_url = self.optimize_samsung_image_url(image_url)

                            # 파일명 생성
                            filename = self.generate_slide_filename(
                                korean_name, english_code, color_name, slide_idx + 1
                            )

                            # 이미지 다운로드
                            if self.download_image_improved(image_url, filename, korean_name, english_code, color_name):
                                success_count += 1
                                downloaded_urls.add(image_url)
                                print(f"            ✅ 슬라이드 {slide_idx + 1} 이미지 다운로드 성공")
                            else:
                                print(f"            ❌ 슬라이드 {slide_idx + 1} 이미지 다운로드 실패")
                        else:
                            print(f"            ⚠️ 슬라이드 {slide_idx + 1} 이미지 URL 없거나 중복")
                    else:
                        print(f"            ❌ 슬라이드 {slide_idx + 1} 이미지를 찾을 수 없음")

                except Exception as e:
                    print(f"            ❌ 슬라이드 {slide_idx + 1} 처리 실패: {str(e)}")

            print(f"         ✅ 색상 '{color_name}' 슬라이드 다운로드: {success_count}개")
            return success_count

        except Exception as e:
            print(f"         ❌ 슬라이드 이미지 다운로드 실패: {str(e)}")
            return 0

    def download_current_images_from_item(self, product_item, korean_name, english_code, color_name):
        """현재 보이는 이미지들 다운로드 (페이지네이션이 없는 경우)"""
        try:
            images = product_item.find_elements(By.CSS_SELECTOR, "img[src*='samsung.com']")
            success_count = 0

            for img_idx, img in enumerate(images):
                try:
                    image_url = img.get_attribute('src')
                    if image_url and 'samsung.com' in image_url:
                        image_url = self.optimize_samsung_image_url(image_url)
                        filename = self.generate_slide_filename(
                            korean_name, english_code, color_name, img_idx + 1
                        )

                        if self.download_image_improved(image_url, filename, korean_name, english_code, color_name):
                            success_count += 1
                except:
                    continue

            return success_count
        except:
            return 0

    def optimize_samsung_image_url(self, url):
        """Samsung 이미지 URL을 고화질로 최적화"""
        try:
            if 'samsung.com' in url:
                # 기존 크기 파라미터 제거
                url = re.sub(r'\$.*?\$', '', url)
                url = url.split('?')[0]

                # 고화질 파라미터 추가
                if not url.endswith('?'):
                    url += '?$PF_PRD_KDP_PNG$'

            return url
        except:
            return url

    def generate_slide_filename(self, korean_name, english_code, color_name, slide_index):
        """슬라이드 파일명 생성: 한글명_영문코드_색상명_슬라이드번호.png"""
        try:
            # 한글명 정리
            clean_korean = re.sub(r'[^\w\s가-힣]', '', korean_name)
            clean_korean = re.sub(r'\s+', '_', clean_korean.strip())

            # 영문코드 정리
            clean_english = re.sub(r'[^\w]', '', english_code.strip())

            # 색상명 정리
            clean_color = re.sub(r'[^\w가-힣]', '', color_name.strip())

            # 슬라이드 번호 (4자리)
            slide_num = str(slide_index).zfill(4)

            # 최종 파일명: 한글명_영문코드_색상명_슬라이드번호.png
            filename = f"{clean_korean}_{clean_english}_{clean_color}_{slide_num}.png"

            # 파일시스템에서 사용할 수 없는 문자 처리
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)

            # 파일명이 너무 길면 자르기
            if len(filename) > 150:
                clean_korean = clean_korean[:30]
                clean_english = clean_english[:20]
                clean_color = clean_color[:15]
                filename = f"{clean_korean}_{clean_english}_{clean_color}_{slide_num}.png"

            return filename

        except Exception as e:
            print(f"         ⚠️ 파일명 생성 실패: {str(e)}")
            return f"product_{slide_index:04d}.png"

    def download_image_improved(self, image_url, filename, korean_name, english_code, color_name):
        """개선된 이미지 다운로드 - 디렉토리 구조 생성"""
        if not image_url:
            return False

        try:
            # URL 정리
            if image_url.startswith('//'):
                image_url = 'https:' + image_url
            elif image_url.startswith('/'):
                image_url = 'https://images.samsung.com' + image_url

            # 제품명 폴더 생성
            clean_korean = re.sub(r'[^\w\s가-힣]', '', korean_name)
            clean_korean = re.sub(r'\s+', '_', clean_korean.strip())
            clean_english = re.sub(r'[^\w]', '', english_code.strip())

            product_folder_name = f"{clean_korean}_{clean_english}"
            product_folder_name = re.sub(r'[<>:"/\\|?*]', '_', product_folder_name)

            # 색상 폴더명 정리
            clean_color = re.sub(r'[^\w가-힣]', '', color_name.strip())
            clean_color = re.sub(r'[<>:"/\\|?*]', '_', clean_color)

            # 전체 경로 생성: ./samsung_img/제품명/색상명/
            product_dir = os.path.join(self.images_folder, product_folder_name)
            color_dir = os.path.join(product_dir, clean_color)

            # 디렉토리 생성
            if not os.path.exists(color_dir):
                os.makedirs(color_dir)
                print(f"            📁 디렉토리 생성: {color_dir}")

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
                'Referer': 'https://www.samsung.com/',
                'Connection': 'keep-alive'
            }

            response = requests.get(image_url, headers=headers, timeout=30, stream=True)

            if response.status_code == 200:
                file_path = os.path.join(color_dir, filename)

                # 이미 파일이 존재하는지 확인
                if os.path.exists(file_path):
                    print(f"            ⚠️ 파일 이미 존재: {filename}")
                    return True

                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                file_size = os.path.getsize(file_path)
                if file_size > 1000:  # 1KB 이상인 경우만 성공으로 간주
                    self.total_images_downloaded += 1  # 성공적으로 다운로드된 이미지 수 증가
                    print(
                        f"            ✅ 다운로드 완료: {filename} ({file_size:,} bytes) [총 {self.total_images_downloaded}개]")
                    return True
                else:
                    os.remove(file_path)
                    return False
            else:
                return False

        except Exception as e:
            print(f"            ❌ 다운로드 오류: {str(e)}")
            return False

    def save_products_to_csv(self, products):
        """제품 정보를 CSV 파일로 저장"""
        print(f"\n💾 제품 정보 CSV 저장 중...")

        csv_data = []
        for product in products:
            csv_data.append({
                'index': product['index'],
                'korean_name': product['korean_name'],
                'english_code': product['english_code'],
                'product_url': product['product_link'],
                'image_url': product['image_url']
            })

        df = pd.DataFrame(csv_data)
        df.to_csv(self.csv_file, index=False, encoding='utf-8-sig')
        print(f"✅ 제품 정보 CSV 저장 완료: {self.csv_file} ({len(products)}개)")

    def run_scraping(self):
        """전체 스크래핑 프로세스 실행"""
        try:
            print("🚀 삼성 세탁기/건조기 스크래핑 시작!")
            print("=" * 60)

            self.setup_driver()

            print(f"\n🌐 페이지 접속: {self.base_url}")
            self.driver.get(self.base_url)
            time.sleep(5)

            # 품절상품 제외 필터 해제
            self.handle_out_of_stock_filter()

            # 더보기 버튼으로 모든 제품 로드
            self.scroll_and_load_all_products()

            # 전체 제품 정보 수집
            products = self.get_all_products_improved()

            if not products:
                print("❌ 추출된 제품이 없습니다.")
                return

            self.save_products_to_csv(products)

            # 모든 색상별 슬라이드 이미지 다운로드
            image_success = self.download_all_color_slide_images(products)

            # 결과 요약
            print("\n" + "=" * 60)
            print("🎉 모든 작업 완료!")
            print(f"📊 최종 결과:")
            print(f"   - 처리된 제품 수: {len(products)}개")
            print(f"   - 다운로드된 이미지: {image_success}개")
            print(f"   - 이미지 폴더: {self.images_folder}")
            print(f"   - 제품 정보 CSV: {self.csv_file}")

            # 폴더 내 파일 목록 확인
            try:
                image_files = [f for f in os.listdir(self.images_folder)
                               if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]

                print(f"\n📂 다운로드된 파일 현황:")
                print(f"   - 이미지 파일: {len(image_files)}개")

                if image_files:
                    print(f"\n🖼️ 이미지 파일 예시:")
                    for i, filename in enumerate(image_files[:10], 1):
                        file_path = os.path.join(self.images_folder, filename)
                        file_size = os.path.getsize(file_path)
                        print(f"   {i}. {filename} ({file_size:,} bytes)")

            except Exception as e:
                print(f"   ⚠️ 폴더 확인 실패: {str(e)}")

        except KeyboardInterrupt:
            print(f"\n⚠️ 사용자에 의해 중단되었습니다.")
            print(f"📊 중단 시점까지의 결과:")
            if 'products' in locals():
                print(f"   - 처리 시도된 제품 수: {len(products)}개")
            print(f"   - 다운로드된 이미지: {self.total_images_downloaded}개")
            print(f"   - 이미지 폴더: {self.images_folder}")
        except Exception as e:
            print(f"❌ 스크래핑 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()

        finally:
            self.close_driver()


def main():
    scraper = SamsungWasherDryerScraper()
    scraper.run_scraping()


if __name__ == "__main__":
    main()