import time
import re
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import logging
import os
from typing import Dict
from config import setup_logging


logger = logging.getLogger('scrapping')
logger.info("Скраппинг запущен.")


def get_area(text):
    match = re.search(r'(\d+[.,]?\d*)\s*м', text)
    if match:
        return float(match.group(1).replace(',', '.'))
    return None


options = Options()
options.add_argument('--headless')
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

service = Service(ChromeDriverManager().install())

all_rents = []
seen_ids = set()


def scraping_cian_commercial_rent(regions: Dict[int, str]):
    driver = webdriver.Chrome(service=service, options=options)

    for region_id, region_name in regions.items():
        url = f'https://www.cian.ru/cat.php?deal_type=rent&engine_version=2&offer_type=offices&region={region_id}&minarea=150&maxarea=700'
        max_pages_per_city = 15

        for page in range(1, max_pages_per_city + 1):
            url = f'{url}&p={page}'
            print(
                f'Получение объявлений со страницы {page} города {region_name}'
            )
            logger.info(
                f'Получение объявлений со страницы {page} города {region_name}'
            )

            driver.get(url)
            time.sleep(2)

            soup = BeautifulSoup(driver.page_source, 'html.parser')

            cards = soup.find_all(
                'div',
                attrs={'data-name': 'CommercialOfferCard'}
            )

            if not cards:
                print(f'Страница {page}: объявлений не найдено.')
                logger.info(f'Страница {page}: объявлений не найдено')
                break

            for card in cards:
                link_tag = card.find(
                    'a',
                    attrs={'data-name': 'CommercialTitle'},
                    href=lambda href: href and '/rent/commercial/' in str(href)
                )
                if not link_tag:
                    continue

                rent_url = link_tag['href']

                id_match = re.search(r'/(\d+)/', rent_url)
                if not id_match:
                    continue
                rent_id = int(id_match.group(1))

                if rent_id in seen_ids:
                    continue
                seen_ids.add(rent_id)

                address = None
                address_from_span = card.find(
                    'span',
                    attrs={'itemProp': 'name'}
                )
                if address_from_span:
                    address = address_from_span.get('content')

                if not address:
                    address_items = card.find_all(
                        'a',
                        attrs={'data-name': 'AddressPathItem'}
                    )
                    address = ", ".join([
                        item.get_text(strip=True) for item in address_items
                    ])

                areas = []
                for area in card.find_all('a', attrs={'data-name': 'AreaLink'}):
                    float_area = get_area(area.get_text())
                    if float_area:
                        areas.append(float_area)

                for area in set(areas):
                    if 150 <= area <= 700:
                        all_rents.append({
                            'id': rent_id,
                            'address': address,
                            'area_m2': area,
                            'url': rent_url
                        })

            time.sleep(2)
        time.sleep(2)

    driver.quit()


regions = {
    1: 'Москва',
    2: 'Санкт-Петербург',
    4777: 'Казань',
    4959: 'Ростов-на-Дону',
    4743: 'Екатеринбург',
    4897: 'Новосибирск',
    4820: 'Краснодар',
    4966: 'Самара'
}

scraping_cian_commercial_rent(regions)
df = pd.DataFrame(all_rents)
df = df.drop_duplicates(subset=['id', 'area_m2'])

if not os.path.exists('data'):
    os.makedirs('data')
df.to_csv('data/cian_commercial_150_700.csv', index=False, encoding='utf-8')

print(f'Собрано {len(df)} помещений.')
logger.info(f'Собрано {len(df)} помещений. Скрапинг завершен.')
