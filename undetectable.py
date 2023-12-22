import configparser
import json
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import requests

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

from SqlLite import SQLite_operations

"""
for key, value in list_response.items():  # Loop through the list of profiles and run them one by one
    # if value['folder'] == 'test': # Here you can add a check to run only the profiles you need (in this example, we run the profiles that are in the 'test' folder)
    profile_id = key
    if value['status'] == 'Available':  # If the profile is not running, then run the profile and take the debug_port
        start_profile_response = \
        requests.get(f'http://{address}:{port_from_settings_browser}/profile/start/{profile_id}', timeout=5).json()[
            'data']
        debug_port = start_profile_response['debug_port']
    if value[
        'status'] == 'Started':  # If the profile is running, then we simply take the debug_port from the available data
        debug_port = value['debug_port']
    if value['status'] == 'Locked':  # If the profile is Locked, then skip
        continue
    if debug_port:  # We check if the browser has a connection port (WebEngine profiles doesnt have ports, so we close them immediately)
        chrome_options.debugger_address = f'{address}:{debug_port}'
        driver = webdriver.Chrome(service=ser, options=chrome_options)
        driver.get("https://whoer.net/")  # Open whoer.net in active tab
        driver.switch_to.new_window('tab')  # Create a new tab and switch to it
        driver.get(url='https://browserleaks.com/js')  # Open browserleaks.com/js in active tab
        # You can add any other actions here
    sleep(60)  # Wait 5 sec
    requests.get(f'http://{address}:{port_from_settings_browser}/profile/stop/{profile_id}')  # Stop profile
"""

config = configparser.ConfigParser()  # создаём объекта парсера
config.read("settings.ini", encoding='utf-8')  # читаем конфиг

ADDRESS = str(config['Undetectable']['ADDRESS'])
PORT_FROM_SETTINGS_BROWSER = str(config['Undetectable']['PORT_FROM_SETTINGS_BROWSER'])
CHROME_DRIVER_PATH = str(config['Undetectable']['CHROME_DRIVER_PATH'])
NAME_PROFILE = str(config['Undetectable']['NAME_PROFILE'])
TAG_NAME = str(config['Undetectable']['TAG_SEARCH'])

TABLE_COUNTRIES = config['SMS']['TABLE_COUNTRIES']

BLACKLIST_IP = str(config['Bot']['BLACK_IP_ADDRESS'])
GMAIL_LOGIN_PASSWORD = str(config['Bot']['GMAIL_LOGIN_PASSWORD'])
CREDIT_CARDS = str(config['Bot']['CARD_PATH'])
PRODUCTS_BUY = str(config['Bot']['PRODUCTS_PATH'])


@dataclass
class Orders:
    """
    Класс Orders предназначен для хранения данных о выполненных заказах.

    Конструктор класса не имеет параметров.

    Доступны следующие поля:

    date_registered: хранит дату регистрации.
    name_profile: хранит имя профиля.
    type_os: хранит тип операционной системы.
    login: хранит логин.
    password: хранит пароль.
    name: хранит имя.
    surname: хранит фамилию.
    country: хранит страну.
    phone: хранит номер телефона.
    zip_code: хранит почтовый индекс.
    ip_start: хранит начальный IP-адрес.
    ip_end: хранит конечный IP-адрес.
    link_product: хранит ссылку на продукты, которые были куплены.
    """
    date_registered: str
    name_profile: str
    type_os: str
    login: str
    password: str
    name: str
    surname: str
    country: str
    phone: str
    zip_code: str
    ip_start: str
    ip_end: str
    link_product: str


class Clicks:
    def __init__(self, driver, button):
        self.driver = driver
        self.button = button

    def action_chains(self):
        ActionChains(self.driver).click(self.button).perform()

    def javascript_dispatch(self):
        self.driver.execute_script("arguments[0].dispatchEvent(new Event('click'));", self.button)

    def javascript_click(self):
        self.driver.execute_script("arguments[0].click();", self.button)

    def javascript_listener(self):
        self.driver.execute_script('addEventListener("click")', self.button)

    def keys_return(self):
        """
        Метод send_keys(): Если кнопка является элементом <input> с атрибутом type="submit" или type="button",
        вы можете использовать метод send_keys(Keys.RETURN) для нажатия на кнопку.
        :return:
        """
        self.button.send_keys(Keys.RETURN)

    def submit(self):
        """
        Скорее всего работает только Если кнопка является элементом <input>
        :return:
        """
        self.button.submit()


class BestRandoms:
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.url = 'https://www.bestrandoms.com/random-address'
        start_time = time.time()
        self.driver.get(self.url)
        max_wait_load = 5
        self.driver.set_script_timeout(max_wait_load)
        # Не работает
        if time.time() - start_time > max_wait_load:
            driver.execute_script("window.stop();")

    def select_state(self, select_state: str):
        """
        Select a state from the drop-down menu.

        Parameters:
            select_state (str): The name of the state to select.
        """
        states = self.driver.find_elements(By.XPATH, '//*[@name="state"]/option')
        for state in states:
            if state.text == select_state:
                state.click()

    def select_city(self, city: str):
        city_input = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(
            (By.XPATH, '//*[@name="city"]')))
        city_input.send_keys(city)

    def select_zipcode(self, zipcode: str):
        zipcode_input = self.driver.find_element(By.XPATH, '//*[@name="zip"]')
        zipcode_input.send_keys(zipcode)

    def click_generate(self):
        self.driver.find_element(By.XPATH, '//*[@type="submit"]').click()

    def _pattern(self, number_option: int, num_generator: int = 0):
        return self.driver.find_elements(By.XPATH, f'//*[@class="content"]//li/span[{number_option}]')[
            num_generator].text

    def parse_data(self):
        phone = self._pattern(1)
        address = self._pattern(2)
        city = self._pattern(3)
        state = self._pattern(4).split('(')[0]  # Удаление сокращения штата в ()
        zipcode = self._pattern(5)
        return {'phone': phone, 'address': address, 'city': city,
                'state': state, 'zipcode': zipcode}


class Undectable:

    def __init__(self, address, port_from_settings_browser, chrome_driver_path, headless):
        self.ser = Service(chrome_driver_path)
        self.chrome_options = Options()
        self.address = address
        self.port_from_settings_browser = port_from_settings_browser
        self.headless = headless
        # Send a request to the local API to get a list of profiles
        self.list_response = requests.get(f'http://{address}:{port_from_settings_browser}/list').json()['data']

    def get_proxy_by_name(self, name):
        return requests.get(
            f'http://{self.address}:{self.port_from_settings_browser}'
            f'/profile/getinfo/{self.get_id_by_name(name)}').json()['data']['proxy']

    def get_link_rotate_by_name(self, name):
        """Получить ссылку на ротацию прокси по имени"""
        proxy = self.get_proxy_by_name(name)
        return proxy[proxy.find(':http') + 1:]

    def get_proxy_by_id(self, id):
        return requests.get(
            f'http://{self.address}:{self.port_from_settings_browser}'
            f'/profile/getinfo/{id}').json()['data']['proxy']

    def get_link_rotate_by_id(self, id):
        """Получить ссылку на ротацию прокси по id"""
        proxy = self.get_proxy_by_id(id)
        return proxy[proxy.find(':http') + 1:]

    def get_id_by_name(self, name):
        """Получить профиль id по имени"""
        return [k for k, v in self.list_response.items() if v['name'] == name][0]

    def get_names_by_tag(self, tag):
        """Получить список имен профилей по тегу"""
        return [v['name'] for k, v in self.list_response.items() if tag in v['tags']]

    def get_ids_by_tag(self, tag):
        """Получить список id профилей по тегу"""
        return [k for k, v in self.list_response.items() if tag in v['tags']]

    def _start_profile(self, profile_id):
        if self.headless:
            params = 'chrome_flags=--headless=new'
        else:
            params = None
        return requests.get(f'http://{self.address}:{self.port_from_settings_browser}/profile/start/{profile_id}',
                            timeout=60, params=params)

    def startProfile_get_debug_port(self, profile_id):
        debug_port = self._start_profile(profile_id).json()['data']['debug_port']
        return debug_port

    def start_driver(self, debug_port):
        self.chrome_options.debugger_address = f'{self.address}:{debug_port}'
        driver = webdriver.Chrome(service=self.ser, options=self.chrome_options)
        return driver

    def stop_profile(self, profile_id):
        requests.get(
            f'http://{self.address}:{self.port_from_settings_browser}/profile/stop/{profile_id}')  # Stop profile

    def get_info_profile(self, profile_id):
        return requests.get(
            f'http://{self.address}:{self.port_from_settings_browser}'
            f'/profile/getinfo/{profile_id}').json()['data']


class Amazon:
    def __init__(self, driver: WebDriver):
        self.login = None
        self.password = None
        self.mobile_or_email = None
        self.driver = driver
        self.wait_sec = 15
        self.impl_wait = 5
        self.default_url = 'https://www.amazon.com/'

    def pattern_wait(self, locator, wait_sec=30):
        return WebDriverWait(self.driver, wait_sec).until(
            EC.presence_of_element_located(locator))

    def create_account(self, login, password, mobile_or_email, replay=False):
        self.login = login
        self.password = password
        self.mobile_or_email = mobile_or_email

        if not replay:
            url = self.default_url
            self.driver.get(url)
            self.driver.implicitly_wait(self.impl_wait)

            try:
                start_here = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located(
                    (By.XPATH, '//*[@class="nav-signin-tooltip-footer"]/a')))
                url_create = start_here.get_attribute('href')
            except:
                raise Exception('[?] Вы уже вошли в аккаунт')

            self.driver.get(url_create)
        time.sleep(1)
        self.driver.implicitly_wait(self.impl_wait)
        input_your_name = self.pattern_wait((By.ID, 'ap_customer_name'))
        input_your_name.clear()
        input_your_name.send_keys(login)

        input_mobile_or_email = self.pattern_wait((By.ID, 'ap_email'))
        input_mobile_or_email.clear()
        input_mobile_or_email.send_keys(mobile_or_email)

        input_password = self.pattern_wait((By.ID, 'ap_password'))
        input_password.clear()
        input_password.send_keys(password)

        re_enter_password = self.pattern_wait((By.ID, 'ap_password_check'))
        re_enter_password.clear()
        re_enter_password.send_keys(password)

        time.sleep(1)
        submit_button = self.driver.find_element(By.XPATH, '//*[contains(@id, "continue")]//input')
        submit_button.submit()

        if self._check_already_email():
            raise Exception('[-] Email уже зарегистрирован')

    def replace_amazon_captcha(self):
        # Замена Amazon Captcha на другую
        # Очистка куков после 3 обновления
        try:
            count_captcha = 1
            while self.check_amazon_captcha():
                self.driver.back()
                time.sleep(1)
                self.driver.implicitly_wait(self.impl_wait)
                self.create_account(self.login, self.password, self.mobile_or_email, replay=True)
                time.sleep(3)
                count_captcha += 1
                if count_captcha > 3:
                    self.driver.delete_all_cookies()
                    print('[+] Delete all cookies')
                    time.sleep(3)
                    count_captcha = 1
        except NoSuchElementException:
            print('[-] No such element')
        except TimeoutException:
            print('[-] TimeoutException')

    def check_account_ban(self):
        # После нажатия кнопки покупки
        """We noticed unusual payment activity on your account and need to verify
        ownership of the payment method used on your most recent order. (Why?)"""
        if self.driver.title == 'Account on hold temporarily':
            return True
        else:
            return False

    def _check_already_email(self):
        """Email уже зарегистрирован"""
        try:
            self.driver.implicitly_wait(1)
            # self.pattern_wait((By.XPATH, '//*[contains(text(), "already an account with this email")]'), 1)
            self.driver.find_element(By.XPATH, '//*[contains(text(), "already an account with this email")]')
        except NoSuchElementException:
            return False
        else:
            return True

    def check_internal_error(self):
        try:
            self.driver.implicitly_wait(self.impl_wait)
            self.pattern_wait((By.XPATH, '//*[contains(text(), "Internal Error. Please try again later")]'), 1)
        except TimeoutException:
            return False
        else:
            return True

    def check_countre_isnot_supported(self):
        try:
            self.driver.implicitly_wait(self.impl_wait)
            self.driver.find_element(
                By.XPATH, '//*[contains(text(), " Try using a mobile number with another country code")]')
            return True
        except NoSuchElementException:
            return False

    def check_verify_email(self):
        try:
            self.driver.implicitly_wait(self.impl_wait)

            self.driver.find_element(By.ID, 'cvf-input-code')
            return True
        except:
            return False

    def check_amazon_captcha(self):
        self.driver.implicitly_wait(self.impl_wait)

        iframe1 = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(
            (By.TAG_NAME, 'iframe')))
        self.driver.switch_to.frame(iframe1)
        self.driver.find_element(By.XPATH, '//*[@class="amzn-captcha-modal"]')
        print("[-] Detected Amazon captcha")
        return True

    def check_entered_exists_account(self):
        """Номер телефона уже зарегистрирован"""
        try:
            self.driver.implicitly_wait(self.impl_wait)

            alert = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(
                (By.XPATH, '//*[contains(text(), "entered already exists with another account.")]')))
            return True
        except TimeoutException:
            return False

    def check_add_mobile_number(self):
        try:
            self.driver.implicitly_wait(self.impl_wait)
            self.driver.find_element(By.XPATH, '//h1[text()="Add mobile number"]')
            return True
        except Exception:
            return False

    def _check_all_prime(self):
        self.driver.implicitly_wait(self.impl_wait)
        if self.driver.title == 'Amazon.com Checkout':
            no_thanks_button = self.driver.find_element(By.ID, 'prime-interstitial-nothanks-button')
            no_thanks_button.click()
        self.driver.implicitly_wait(self.impl_wait)

    def input_verify_code(self, code):
        input_code = self.driver.find_element(By.XPATH, '//input[@type="text"]')
        input_code.send_keys(code.strip())
        self.driver.implicitly_wait(self.impl_wait)
        self.driver.find_element(By.ID, 'cvf-submit-otp-button').click()

    def input_sms_verify_code(self, code: str):
        input_code = self.driver.find_element(By.XPATH, '//*[@name="code"]')
        input_code.clear()
        input_code.send_keys(code.strip())
        self.driver.find_element(By.XPATH, '//*[@name="cvf_action"]').click()
        self.driver.implicitly_wait(self.impl_wait)

    @staticmethod
    def set_default_address(driver, address_text, city_text, state_text, zip_code_text):
        wait_sec = 5
        url = 'https://www.amazon.com/a/addresses'
        driver.get(url)
        driver.implicitly_wait(wait_sec)

        time.sleep(3)
        add_address_button = WebDriverWait(driver, wait_sec).until(
            EC.visibility_of_element_located((By.ID, 'ya-myab-address-add-link')))
        link_add_address = add_address_button.get_attribute('href')
        driver.get(link_add_address)
        driver.implicitly_wait(wait_sec)

        address_input = driver.find_element(By.ID, 'address-ui-widgets-enterAddressLine1')
        address_input.send_keys(address_text)

        city_input = driver.find_element(By.ID, 'address-ui-widgets-enterAddressCity')
        city_input.send_keys(city_text)

        state_button = WebDriverWait(driver, 1).until(EC.presence_of_element_located(
            (By.ID, 'address-ui-widgets-enterAddressStateOrRegion')))
        state_button.click()
        time.sleep(1)

        states = driver.find_elements \
            (By.XPATH,
             '//*[contains(@aria-labelledby,"address-ui-widgets-enterAddressStateOrRegion-dropdown-nativeId")]')
        for state in states:
            if state.text == state_text:
                state.click()

        zip_code_input = driver.find_element(By.ID, 'address-ui-widgets-enterAddressPostalCode')
        zip_code_input.clear()
        zip_code_input.send_keys(zip_code_text)

        make_default_address = driver.find_element(By.ID, 'address-ui-widgets-use-as-my-default')
        make_default_address.click()
        time.sleep(1)

        final_button = driver.find_element \
            (By.XPATH, '//span[@id="address-ui-widgets-form-submit-button"]//input[@class="a-button-input"]')
        final_button.click()
        driver.implicitly_wait(wait_sec)

        default_address = driver.find_element(By.XPATH, '//span[@id="address-ui-widgets-CityStatePostalCode"]')
        return default_address.text

    @staticmethod
    def set_your_payments(driver, card_number: str = '1232312', name_card='adsda', verify_code='123',
                          month_card: str = '04', year_card: str = 2023):
        url = 'https://www.amazon.com/cpe/yourpayments/wallet'
        wait_sec = 5

        driver.get(url)
        driver.implicitly_wait(wait_sec)

        add_button = WebDriverWait(driver, 3).until(EC.presence_of_element_located(
            (By.XPATH, '//a[@aria-label="add payment method link"]')))
        add_button.click()
        time.sleep(1)
        driver.implicitly_wait(wait_sec)
        # add_button = driver.find_element(By.XPATH, '//*[@class ="a-button-input"]')
        # add_button = driver.find_element \
        #     (By.XPATH, '//*[@class="a-section apx-wallet-selectable-payment-method-tab"]')
        # add_button = driver.find_element\
        #     (By.XPATH, '//*[@class="a-button a-spacing-top-large a-button-primary"]')
        add_credit_button = driver.find_element \
            (By.XPATH, '//*[@id="apx-add-credit-card-action-test-id"]//*[@class="a-button-input"]')
        add_credit_button.click()
        driver.implicitly_wait(wait_sec)

        iframe = driver.find_element \
            (By.XPATH, '//*[contains(@class, "apx-secure-iframe pmts-portal-component pmts-portal-components")]')
        driver.switch_to.frame(iframe)

        card_number_input = WebDriverWait(driver, 5).until(EC.presence_of_element_located(
            (By.XPATH,
             '//*[@class="a-row pmts-add-credit-card-container"]//input[@name="addCreditCardNumber" and @type="tel"]')))
        card_number_input.send_keys(card_number)

        name_input = driver.find_element(By.XPATH, '//*[@name="ppw-accountHolderName"]')
        name_input.send_keys(name_card)

        verify_number = driver.find_element(By.XPATH, '//*[@name="addCreditCardVerificationNumber"]')
        verify_number.send_keys(verify_code)

        expiration_date = driver.find_elements \
            (By.XPATH, '//*[@id="add-credit-card-expiry-date-input-id"]//*[@class="a-button-text a-declarative"]')
        month_button = expiration_date[0]
        time.sleep(1)
        month_button.click()
        driver.implicitly_wait(wait_sec)

        months = WebDriverWait(driver, wait_sec).until(EC.presence_of_all_elements_located(
            (By.XPATH, '//*[@class="a-popover a-dropdown a-dropdown-common a-declarative"][1]//li[@tabindex]')))
        months[int(month_card) - 1].click()
        driver.implicitly_wait(wait_sec)

        year_button = expiration_date[1]
        year_button.click()
        years = driver.find_elements \
            (By.XPATH, '//*[@class="a-popover a-dropdown a-dropdown-common a-declarative"][2]//li[@tabindex]')
        for year in years:
            if year.text == year_card:
                year.click()
        driver.implicitly_wait(wait_sec)

        final_button = driver.find_element(By.XPATH, '//*[@name="ppw-widgetEvent:AddCreditCardEvent"]')
        final_button.click()
        driver.implicitly_wait(wait_sec)

    def add_mobile_number(self, mobile_number: str, name_country):
        self.driver.implicitly_wait(self.impl_wait)

        while True:
            #  Если не найден код страны, то кликнем повторно
            try:
                WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(
                    (By.XPATH, '//*[@class="a-button-text a-declarative"]'))) \
                    .click()
                countries = WebDriverWait(self.driver, 5).until(EC.presence_of_all_elements_located(
                    (By.XPATH, '//*[@class="a-dropdown-item cvf-country-code-option"]')))
            except TimeoutException:
                continue
            else:
                break

        code_country = None
        for country in countries:
            if country.text.__contains__(name_country):
                code_country = re.search(r'\+\d+', country.text).group(0)
                code_country = code_country.replace('+', '')
                country.click()

        if not code_country:
            raise Exception('[-] Code Country not found')

        mobile_number = mobile_number.removeprefix(code_country)

        input_number = self.driver.find_element(By.XPATH, '//*[@name="cvf_phone_num"]')
        input_number.send_keys(mobile_number)

        self.driver.find_element(By.XPATH, '//*[@name="cvf_action"]').click()
        self.driver.implicitly_wait(self.impl_wait)

    def sign_in(self, username, password):
        self.driver.get(self.default_url)
        self.driver.implicitly_wait(self.impl_wait)

        url_sign_in = self.driver.find_element(By.XPATH, '//*[@id="nav-signin-tooltip"]/a').get_attribute('href')
        self.driver.get(url_sign_in)
        self.driver.implicitly_wait(self.impl_wait)
        email_input = self.driver.find_element(By.XPATH, '//input[@type="email"]')
        email_input.clear()
        email_input.send_keys(username)
        continue_button = self.driver.find_element(By.XPATH, '//*[@class="a-button-inner"]/input')
        continue_button.click()
        self.driver.implicitly_wait(self.impl_wait)

        password_input = self.driver.find_element(By.XPATH, '//input[@id="ap_password"]')
        password_input.clear()
        password_input.send_keys(password)
        sign_in_button = self.driver.find_element(By.XPATH, '//input[@id="signInSubmit"]')
        sign_in_button.click()
        self.driver.implicitly_wait(self.impl_wait)


class BuyOrder(Amazon):

    def check_free_delivery(self):
        el_delivery = self.driver.find_element(By.XPATH, '//*[@data-csa-c-mir-type="DELIVERY"]')
        if re.search('shipped', el_delivery.text):
            return False
        else:
            return True

    def check_conditions_buy(self):
        max_cost = 2

        cost = self.driver.find_element(
            By.XPATH, '//*[@id="corePrice_feature_div"]//span[@class="a-offscreen"]//following::span').text
        cost = float(cost.replace('$', '').replace('\n', '.'))
        if cost < max_cost:
            return True
        else:
            return False

    def check_billing_address(self):
        try:
            button_use_billing_address = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(
                (By.XPATH, '//*[@data-testid="Address_selectBillToThisAddress"]')))
        except TimeoutException:
            pass
        else:
            button_use_billing_address.submit()
            self.driver.implicitly_wait(self.impl_wait)

    def _check_fast_buy(self):
        """
        Эта функция используется для проверки доступности опции быстрой покупки.

        Для этого он ищет iframe с идентификатором «turbo-checkout-iframe»,
        ожидание присутствия элемента, а затем переключение на кадр.

        Затем он ожидает присутствия элемента с идентификатором «turbo-checkout-pyo-button»,
        и когда это так, он отправляет форму
        :return:
        """
        self.driver.implicitly_wait(5)
        try:
            iframe = WebDriverWait(self.driver, 1).until(EC.presence_of_element_located(
                (By.ID, 'turbo-checkout-iframe')))
        except TimeoutException:
            return False
        else:
            self.driver.switch_to.frame(iframe)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(
                (By.ID, 'turbo-checkout-pyo-button'))).submit()
            return True

    def buy(self, url):
        # Открывает заданный URL в браузере и ждёт, пока страница не загрузится
        self.driver.get(url)
        self.driver.implicitly_wait(self.impl_wait)

        # Проверяет, соответствует ли текущая страница условиям покупки
        if not self.check_conditions_buy() or not self.check_free_delivery():
            raise Exception('[-] Не соответствует условиям выкупа')

        # Находит кнопку "Купить сейчас" и кликает её
        buy_now_button = self.driver.find_element(By.ID, 'buy-now-button')
        buy_now_button.click()
        self.driver.implicitly_wait(self.impl_wait)

        # Проверяет, доступна ли опция "Быстрый выкуп" и возвращает True, если доступна
        if self._check_fast_buy():
            return True

        # Проверяет, доступна ли опция "Все для Премиума" и выбирает её, если доступна
        self._check_all_prime()

        # Находит кнопку "Продолжить к оплате" и кликает её
        payment_continue_button = self.driver.find_element \
            (By.XPATH, '//input[@name="ppw-widgetEvent:SetPaymentPlanSelectContinueEvent"]')
        payment_continue_button.click()
        self.driver.implicitly_wait(self.impl_wait)
        time.sleep(6)

        # Выбирает адрес доставки, если это необходимо
        self.check_billing_address()

        # Закрывает любые сообщения о промоакциях и кликает кнопку "Нет, спасибо"
        close_button = self.driver.find_element \
            (By.XPATH, '//*[@id="prime-continue-blocker-msg"]//following::div//*[@class="a-link-normal"]')
        if close_button.text == "Close":
            close_button.click()
            time.sleep(1)
        else:
            try:
                not_right_now_button = WebDriverWait(self.driver, self.wait_sec).until \
                        (EC.presence_of_element_located(
                        (By.XPATH, '//*[@class="a-button a-button-base prime-no-button"]//button')))
                not_right_now_button.click()
                time.sleep(1)
            except TimeoutException:
                pass
        self.driver.implicitly_wait(self.impl_wait)

        # Находит кнопку "Оплатить" и кликает её
        pay_button = self.driver.find_element \
            (By.XPATH, '//input[@aria-labelledby="bottomSubmitOrderButtonId-announce"]')
        pay_button.click()

        self.driver.implicitly_wait(self.impl_wait)
        time.sleep(1)
        # Ожидает сообщения о подтверждении заказа и выводит её
        order = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(
            (By.XPATH, '//h4[@class="a-alert-heading"]')))
        print(order.text)


def get_login_password(filepath: str) -> pd.DataFrame:
    # return pd.read_csv(filepath, sep='\t', names=['login', 'password',
    #                                               'name', 'surname'])
    return pd.read_csv(filepath, sep=',', names=['login', 'password',
                                                 'name', 'surname'])


def check_ip_status(driver, wait_sec=3):
    """{"status": "success","country": "Russia","countryCode": "RU",
         "region": "KYA",
         "regionName": "Krasnoyarsk Krai",
         "city": "Zheleznogorsk", "zip": "662970",
         "lat": 56.2516, "lon": 93.5445, "timezone": "Asia/Krasnoyarsk",
         "isp": "CITY26", "org": "Netcity LLC", "as": "AS50147 Posazhennikov Vladimir Vasilevich",
         "query": "185.175.19.83"}
    """
    # url = 'https://api.ipify.org/'
    url = 'http://ip-api.com/json/'
    try:
        driver.get(url)
    except WebDriverException:
        raise WebDriverException('[-] Не удалось получить информацию о IP')
    driver.implicitly_wait(wait_sec)
    ip_data = json.loads(driver.find_element(By.TAG_NAME, 'pre').text)
    return ip_data


def add_address_delivery(driver, wait_sec=3):
    """Используется для добавления адреса доставки в учетную запись Amazon
    с использованием IP-адреса прокси и генерации случайного адреса в том же городе."""
    amazon = Amazon(driver)
    ip_data = check_ip_status(driver, wait_sec)
    city = ip_data['city']
    print(f'City in proxy: {city}')
    driver.implicitly_wait(wait_sec)

    randoms = BestRandoms(driver)
    randoms.select_city(city)
    time.sleep(wait_sec)
    randoms.click_generate()
    time.sleep(wait_sec)
    generated_data = randoms.parse_data()
    print(generated_data)
    phone, *data = generated_data.values()
    default_address = amazon.set_default_address(driver, *data)
    print(f'Default address: {default_address}')
    zip_code = re.search("\d+-\d+", default_address).group(0)
    return zip_code


# def start_undetectable(address, port_from_settings_browser,
#                        chrome_driver_path, name_profile):
#     browser = Undectable(address, port_from_settings_browser, chrome_driver_path)
#     # proxy = browser.get_proxy(name_profile)
#     id_profiles = browser.get_ids_by_tag(tag=TAG_NAME)
#     with open(PRODUCTS_BUY, 'r') as f:
#         list_buy = f.readlines()
#     with open(BLACKLIST_IP, 'r') as f:
#         blacklist_ip = f.readlines()
#         blacklist_ip = [line.strip() for line in blacklist_ip]
#
#     # индексы для мин кол-ва из двух списков
#     index = 0
#     while index < (min(len(id_profiles), len(list_buy))):
#         debug_port = browser.startProfile_get_debug_port(id_profiles[index])
#         driver = browser.start_driver(debug_port)
#
#         """ Проверка наличия стартового IP в списке из пункта 3.
#         При его наличии в нём - ротировать прокси и закрывать профиль,
#         после чего через 30 секунд перезапуск профиль и повторять весь алгоритм.
#         """
#         try:
#             ip_data = check_ip_status(driver, wait_sec=3)
#         except WebDriverException:
#             # Смена IP если произошла ошибка
#             time.sleep(30)
#             rotate_link = browser.get_link_rotate_by_id(id_profiles[index])
#             driver.get(rotate_link)
#             browser.stop_profile(id_profiles[index])
#             time.sleep(1)
#             debug_port = browser.startProfile_get_debug_port(id_profiles[index])
#             driver = browser.start_driver(debug_port)
#
#             ip_data = check_ip_status(driver, wait_sec=3)
#
#         ip_start = ip_data['query']
#         if ip_start in blacklist_ip:
#             print(f'IP {ip_start} in blacklist')
#             rotate_link = browser.get_link_rotate_by_id(id_profiles[index])
#             driver.get(rotate_link)
#             browser.stop_profile(id_profiles[index])
#             time.sleep(30)
#             continue
#
#         # Запись ip при регистрации
#         with open(BLACKLIST_IP, 'a') as f:
#             if ip_start not in blacklist_ip:
#                 f.write(f'{ip_start}\n')
#
#         """Основные процессы"""
#         # login, password, phone, name_country = 'SergioLindsey07', 'U6gkuYTK2sCc5SB', '66968172088', 'Orlando'
#         login, password, phone, name_country = main_registration(driver)
#         default_address = add_address_delivery(driver)
#         main_add_card(driver)
#         main_buy(driver, list_buy[index])
#
#         # запись ip перед выходом профиля
#         ip_data = check_ip_status(driver, wait_sec=3)
#         ip_end = ip_data['query']
#         with open(BLACKLIST_IP, 'a') as f:
#             if ip_end not in blacklist_ip:
#                 f.write(f'{ip_end}\n')
#
#         profile_info = browser.get_info_profile(id_profiles[index])
#
#         # Запись в базу данных
#         order = Orders(date_registered=datetime.now().strftime('%d.%m.%Y'),
#                        name_profile=profile_info['name'],
#                        type_os=profile_info['os'],
#                        login=login,
#                        password=password,
#                        name='None',
#                        surname='None',
#                        country=name_country,
#                        phone=phone,
#                        zip_code=default_address,
#                        ip_start=ip_start,
#                        ip_end=ip_end,
#                        link_product=list_buy[index])
#         db = SQLite_operations('Database.db', 'Amazon')
#         db.add_data(pd.DataFrame([order]))
#
#         time.sleep(15)
#         browser.stop_profile(id_profiles[index])
#         index += 1


# def main_registration(driver: WebDriver) -> tuple:
#     """Главная функция для регистрации нового пользователя
#
#     :return
#         login: логин
#         password: <PASSWORD>
#         phone: номер телефона
#         name_country: название страны
#     """
#
#     df_countries = pd.read_csv(TABLE_COUNTRIES)
#     df_login_pass = get_login_password(GMAIL_LOGIN_PASSWORD)
#
#     # Рандомная страна
#     row_country = df_countries.sample()
#     name_country = row_country['Name'].item()
#     code_country = row_country['Code'].item()
#
#     # Тест первой страны в списке
#     # row_country = df_countries.iloc[0]
#     # name_country = row_country['Name']
#     # code_country = row_country['Code']
#
#     amazon = Amazon(driver)
#     while True:
#         # Создаём учётную запись
#         count_index = df_login_pass.__len__()
#         index_rand = random.randrange(0, count_index)
#         # index_rand = 1
#         data = df_login_pass.iloc[index_rand]
#
#         login = data['login'].split('@')[0]
#         password = data['password']
#         print(f'Login: {login}')
#         mobile_or_email = data['login']
#         print(f'Mobile or email: {mobile_or_email}')
#
#         try:
#             amazon.create_account(login, password, mobile_or_email)
#         except Exception as e:
#             # Удаляем запись если произошла ошибка входа. Повторная попытка входа с другим Email
#             if e.args[0] == '[-] Email уже зарегистрирован':
#                 if df_login_pass.__len__() > 1:
#                     df_login_pass.drop(labels=index_rand, inplace=True)
#                     print('[-] Email уже зарегистрирован. Повторная попытка входа с другим Email')
#                     continue
#                 else:
#                     raise Exception('[-] Закончились аккаунты для регистрации')
#         else:
#             break
#
#     # amazon.replace_amazon_captcha()
#
#     # Ожиднаем появления окна с верификацией
#     wait_minutes = 10
#     print(f'Wait window "Verify email address" {wait_minutes} minutes')
#     WebDriverWait(amazon.driver, 60 * wait_minutes).until(EC.presence_of_element_located(
#         (By.XPATH, '//h1[text()="Verify email address"]')))
#
#     time.sleep(3)
#
#     # Переключаемся на новое окно
#     driver.switch_to.new_window()
#     try:
#         code = signin_and_getcode(driver, mobile_or_email, password)
#     except Exception:
#         print('[-] Вы уже вошли в аккаунт Gmail')
#         # Очищаем куки
#         driver.execute_cdp_cmd('Storage.clearDataForOrigin', {
#             "origin": '*',
#             "storageTypes": 'all',
#         })
#         print('[+] Gmail cookies cleared')
#         print('[?] Повторная попытка входа')
#         # Повторяем попытку
#         code = signin_and_getcode(driver, mobile_or_email, password)
#
#     print('[+] Gmail veriffication code:', code)
#     driver.close()
#
#     # Переключаемся обратно на первое окно
#     driver.switch_to.window(driver.window_handles[0])
#     amazon.input_verify_code(code)
#     print('[+] Verification is complete successfully')
#
#     if amazon.check_add_mobile_number():
#         timeout_wait_minutes = 4  # должно быть 4
#         max_replace_country = 3
#         count_replace_country = 0
#         max_count_smscode = 3
#         count_try = 1
#         while True:
#             flag_replace = False
#             start_time = time.time()
#
#             # sms = SMS(country=code_country)
#             # phone = sms.get_phone()
#             # amazon.add_mobile_number(phone, name_country=name_country)
#             print('Country:', name_country, 'Phone:', phone)
#
#             if amazon.check_internal_error():
#                 raise Exception(f'[-] Try {count_try}/{max_replace_country} {name_country}: '
#                                 f'Internal Error. Please try again later.')
#
#             if amazon.check_countre_isnot_supported():
#                 alarm_text = amazon.driver.find_element(
#                     By.XPATH, '//*[contains(text(), " Try using a mobile number with another country code")]')
#                 raise Exception(f'[-] Try {count_try}/{max_count_smscode}: {alarm_text.text}')
#
#             while sms.get_full_sms() == 'STATUS_WAIT_CODE':
#                 time.sleep(5)
#                 print('[?] Waiting for verification code')
#
#                 if time.time() - start_time > 60 * timeout_wait_minutes:
#                     print(f'[-] Timeout waiting for verification code')
#                     start_time = time.time()
#                     flag_replace = True
#                     break
#             if flag_replace:
#                 WebDriverWait(driver, 1).until(EC.presence_of_element_located(
#                     (By.XPATH, '//*[contains(text(),"Change")]'))).click()
#                 count_try += 1
#                 continue
#
#             sms_message = sms.get_full_sms()
#             sms_code = re.search(r'\d+', sms_message)
#             sms_code = sms_code.group(0)
#             print(f'SMS verification code: {sms_code}')
#             amazon.input_sms_verify_code(sms_code)
#
#             if not amazon.check_entered_exists_account():
#                 break
#
#             if count_try == max_count_smscode:
#                 if count_replace_country == max_replace_country:
#                     raise Exception(f'[-] Try country replacement = {count_replace_country}/{max_replace_country}:'
#                                     f' Verification code is not')
#                     # break
#
#                 print(f'[?] Try {count_try}/{max_count_smscode}: Verification code is not correct')
#                 df_countries = df_countries[df_countries["Name"] != name_country]
#
#                 code_country, name_country = df_countries.sample().values[0]
#                 count_try = 1
#                 count_replace_country += 1
#
#             count_try += 1
#
#         print('[+] Registration Complete')
#     else:
#         # Email Уже зарегистрирован?????
#         if amazon.check_verify_email():
#             text = amazon.driver.find_element(By.XPATH, '//*[@class="a-alert-content"]/div[text()][3]')
#             print(f'[?] Verify email address: {text.text}')
#         phone = None
#
#     # add_address_delivery(amazon, driver)
#     # add_card_debit(amazon)
#
#     # time.sleep(60 * 30)
#     return login, password, phone, name_country


def main_buy(driver: WebDriver, product_buy: str):
    buy_order = BuyOrder(driver)
    # product_buy = list_buy[random.randrange(0, len(list_buy))]
    buy_order.buy(product_buy)
    print(f'[+] Buy order: {product_buy}')


def main_add_card(driver: WebDriver):
    amazon = Amazon(driver)

    df = pd.read_csv(CREDIT_CARDS, header=None)
    index_card = random.randrange(0, df.shape[0])
    card = df.iloc[index_card]

    amazon.set_your_payments(driver, name_card=card[0],
                             card_number=card[1],
                             verify_code=str(card[3]),
                             month_card=card[2].split('/')[0],
                             year_card='20' + card[2].split('/')[1])


if __name__ == '__main__':
    # try:
    # start_undetectable(address=ADDRESS,
    #                    port_from_settings_browser=PORT_FROM_SETTINGS_BROWSER,
    #                    chrome_driver_path=CHROME_DRIVER_PATH,
    #                    name_profile=NAME_PROFILE)
    # except Exception as e:
    #     print(e)
    #     time.sleep(60)
    pass