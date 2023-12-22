import configparser
import json
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import SqlLite
from save_DB import save_db

from undetectable import Undectable
from threading import currentThread, Thread
from time import sleep
from itertools import islice

address = '127.0.0.1'
port_from_settings_browser = '25325'
chrome_driver_path = 'chromedriver.exe'
name_profile = '7476818'
TAG_NAME = 'parse'

categories = {'laptops': 'https://www.amazon.com/s?k=Traditional+Laptop+Computers&i=computers',
              'tablets': 'https://www.amazon.com/s?k=Tablets&i=computers&rh=n%3A1232597011',
              'toys&games': 'https://www.amazon.com/s?i=toys-and-games-intl-ship&rh=n%3A16225015011&page=2',
              'sport_men': 'https://www.amazon.com/s?k=sport+men&i=fashion-mens&rh=n%3A7147441011&dc',
              }
count = 0


@dataclass
class Card:
    name: str
    price: str
    link: str
    date: str


@dataclass
class Card_full:
    name: str
    categories: str
    price: str
    features: str
    about: str
    link: str
    date: str


def start_profiles(browser, tag, max_count=None):
    """
    This function starts multiple browser profiles with the specified tag.
    Parameters
    ----------
    tag : str
        The tag to search for in the browser profiles.

    Returns
    -------
    drivers : list
        A list of WebDriver objects for the started profiles.
    """
    print(f'Start profiles')

    # proxy = browser.get_proxy(name_profile)
    id_profiles = browser.get_ids_by_tag(tag=tag)
    drivers = []
    for id in id_profiles[:max_count]:
        debug_port = browser.startProfile_get_debug_port(id)
        driver = browser.start_driver(debug_port)
        time.sleep(1)
        drivers.append(driver)
    print(f'Start profiles complete')
    return drivers, id_profiles


def batched(iterable, n):
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        raise ValueError('n must be at least one')
    it = iter(iterable)
    while batch := tuple(islice(it, n)):
        yield batch


def get_max_pages(browser: WebDriver):
    max_page = browser.find_element(By.XPATH, '//*[contains(@class, "s-pagination-item")]')
    return int(max_page.text)


def parse_prices(html):
    # parse_prices('https://www.amazon.com/s?k=Traditional+')
    # "//*[@data-asin and @data-index]//*[@class='a-price']/span[@class='a-offscreen']")))
    # prices = [price.text for price in prices]

    soup = BeautifulSoup(html, 'html.parser')
    prices = soup.select('div[data-asin][data-index] [class=a-price] span[class=a-offscreen]')
    return [price.text.strip() for price in prices]


def parse_catalog(driver: WebDriver, batch, num_profile):
    global count
    name_category = 'sport_men'
    url = categories.get(name_category)
    data = []
    for num in batch:
        url = url + f'&page={num}'
        driver.get(url)
        cards = driver.find_elements(By.XPATH, '//h2')
        links = driver.find_elements(By.XPATH, '//h2/a')
        links = [link.get_attribute('href') for link in links]

        names = [card.text for card in cards]
        prices = parse_prices(driver.page_source)
        result = list(
            map(lambda name, price, link:
                Card(name, price, link, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                names, prices, links))
        data.extend(result)
        print(result)

        print(f'Page: {num} of {num_profile} profiles')

    save_db(pd.DataFrame(data), 'data_parse/Amazon.db', name_category)
    print(f'Parse is complete')


def parse_card(driver: WebDriver, batch, num_profile):
    """
    Эта функция используется для парсинга карточки товара Amazon.
    Параметры:
    driver (WebDriver): Объект WebDriver, который используется для управления браузером.
    batch (list): Список URL-адресов, которые используются для парсинга карточки товара.
    num_profile (int): Номер профиля, который используется.
    """
    data = []
    for url in batch:
        try:
            driver.get(url)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            try:
                title = soup.find('span', {'id': 'productTitle'}).text.strip()
            except:
                continue

            categories_ = soup.find('div', {'id': 'wayfinding-breadcrumbs_feature_div'}).text.strip()

            try:
                price = soup.find('span', {'class': re.compile("a-price *")}) \
                    .find('span', {'class': 'a-offscreen'}).text.strip()
            except:
                price = None

            try:
                table = soup.find('div', {'id': "productOverview_feature_div"})
                rows = table.find_all('tr')
                features = list()
                for row in rows:
                    name_feature = row.find_all('td')[0].text.strip()
                    value_feature = row.find_all('td')[1].text.strip()
                    features.append(f'{name_feature}: {value_feature}')
            except:
                features = None

            if features:
                features = ', '.join(features)

            # описание
            about = soup.find('div', {'id': 'featurebullets_feature_div'}).text.strip()

            result = Card_full(title, categories_, price, features, about, url,
                               datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            data.append(result)
            print(f'{num_profile} profile {title}')
        except Exception as ex:
            print(ex)
            continue

    data = pd.DataFrame(data)
    data.features = data.features.astype(str)
    save_db(data, 'data_parse/Amazon.db', 'Advanced_parse_Sport_men')
    print(f'Parse is complete')


def download_data(name_table):
    """
    Функция загрузки данных:
         Эта функция получает данные из базы данных SQLite и возвращает их в виде Pandas DataFrame.
         Имя базы данных и имя таблицы задаются параметрам функции.
         Функция использует класс SqlLite.SQLite_operations для выполнения операций базы данных.
         Функция возвращает Pandas DataFrame, содержащий данные из указанной таблицы.
    """
    db = SqlLite.SQLite_operations('data_parse/Amazon.db', name_table)
    data = db.select_All('data_parse/Amazon.db', name_table)
    return pd.DataFrame(data, columns=['title', 'price', 'link', 'date'])


def main_parse_card():
    start_time_prof = time.time()
    browser = Undectable(address, port_from_settings_browser, chrome_driver_path, headless=False)
    urls = download_data('sport_men')['link'][:]

    count_profiles = 5
    start_page = 0
    end_page = len(urls)

    drivers, id_profiles = start_profiles(browser, TAG_NAME, max_count=count_profiles)
    list_batched = list(batched(urls, int((end_page - start_page) / len(drivers))))
    print(f'Время запуска {count_profiles} профилей: {time.time() - start_time_prof}')

    print(f'Parse categories: Laptops {categories.get("laptops")}')
    start_time = time.time()
    threads = []
    for num, driver in enumerate(drivers):
        # parse(driver)
        t = Thread(target=parse_card, args=[driver, list_batched[num], num])
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    end_time = time.time()
    print("Время выполнения парсинга:", end_time - start_time)

    for id_ in id_profiles:
        print('Stop profile: ', id_)
        browser.stop_profile(id_)


def main_parse_catalog():
    start_time_prof = time.time()
    browser = Undectable(address, port_from_settings_browser, chrome_driver_path, headless=False)
    count_profiles = 5
    start_page = 1
    end_page = 400

    drivers, id_profiles = start_profiles(browser, TAG_NAME, max_count=count_profiles)
    list_batched = list(batched(range(start_page, end_page + 1), int((end_page - start_page) / len(drivers))))
    print(f'Время запуска {count_profiles} профилей: {time.time() - start_time_prof}')

    print(f'Parse categories: Laptops {categories.get("laptops")}')
    start_time = time.time()
    threads = []
    for num, driver in enumerate(drivers):
        # parse(driver)
        t = Thread(target=parse_catalog, args=[driver, list_batched[num], num])
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()
    end_time = time.time()
    print("Время выполнения парсинга:", end_time - start_time)

    for id_ in id_profiles:
        print('Stop profile: ', id_)
        browser.stop_profile(id_)


if __name__ == '__main__':
    # try:
    main_parse_card()
    # main_parse_catalog()
# except:
#     sleep(30)
