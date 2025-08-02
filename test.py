import time
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import requests

                                   # данные Вашей учетной записи
user_name = "You-login"            # Введите свой логин
user_pass = "You-pass"             # введите свой пароль
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
}

class SenergyPars:
    def __init__(self, url, user_name, user_pass, key):
        self.url = url
        self.user_name = user_name
        self.user_pass = user_pass

    def __set_up(self):
        print(">>> Стартуем Веб-Браузер...")
        print(">>> Открываем Веб-Браузер...")
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(5)

    def __get_url(self):
        print(f">>> Переходим на страницу: {self.url}")
        self.driver.get(self.url)

    def __login(self):
        print(">>> Находим поле ввода логина -> Очищаем -> Вводим")
        self.find_input = self.driver.find_element(By.ID, 'popupUsername')
        self.find_input.clear()
        self.find_input.send_keys(self.user_name)
        time.sleep(2)
        print(">>> Находим поле ввода пароля -> Очищаем -> Вводим")
        self.find_input = self.driver.find_element(By.ID, 'popupPassword')
        self.find_input.clear()
        self.find_input.send_keys(self.user_pass)
        print(">>> Ждем 2 секунды -> Жмякаем клавишу ENTER")
        time.sleep(2)
        self.find_input.send_keys(Keys.ENTER)
        time.sleep(10)

    def __open_new_page(self):
        with open('link_first_page.json', 'r', encoding='utf-8') as file:
            config = json.load(file)
        print(">>> Открываем JSON файл и извлекаем ссылки ...")
        for key, value in config.items():
            self.driver.execute_script(f"window.open('{value}', '_blank');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            print(f'>>> Открываем ссылку в новой вкладке ->{key}<- ...')

            # вызываем объект поиска на новой странице
            self.__search_new_page_link()

            time.sleep(5)
            self.driver.close()
            print(f'>>> Закрываем вкладку -> {key} <- ...')
            self.driver.switch_to.window(self.driver.window_handles[0])

    def __search_link(self):
        data = {}
        print(">>> Искаем все ссылки ... ")
        titles = self.driver.find_elements(By.TAG_NAME, 'tr')[2:]
        for title in titles:
            try:
                link_element = title.find_element(By.TAG_NAME, 'a')
                descript = link_element.text
                link = link_element.get_attribute('href')


                data[descript] = link
                print(f">>> Сохраняем >>{descript}<< и URL в Dict ...")
            except:
                 continue
        with open('link_first_page.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        print(f'>>> Запись ___link_first_page.json___ прошла успешно !..')

    ############################################################################################################
    # в этом моменте нужно каждыый раз ввести директорию для сохранения файлов                                 #
    # и JSON файл из которого считываем ссылки на блоки уроков                                                 #
    ############################################################################################################
    #                               Куда сохранять
    def __search_pdf(self, save_dir="part3"):
        os.makedirs(save_dir, exist_ok=True)
        #          откуда читать
        with open('Тема 1_ Введение.json', 'r', encoding='utf-8') as file:
            config = json.load(file)

        for key, value in config.items():
            try:
                print(">>> Открываем ссылку в новой вкладке ...")
                self.driver.execute_script(f"window.open('{value}', '_blank');")
                self.driver.switch_to.window(self.driver.window_handles[-1])
                print(f'\n>>> Открыта ссылка: {key} ({value})...')

                # Ожидание полной загрузки страницы
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'body'))
                )
                # Прокрутка для подгрузки динамического контента
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                #time.sleep(3)

                # Поиск всех iframe на странице
                iframes = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, 'iframe')))

                pdf_links = []

                for iframe in iframes:
                    try:
                        # Получаем src iframe для отладки
                        iframe_src = iframe.get_attribute('src')
                        print(f">>> Проверяем iframe: {iframe_src}...")

                        # Переключаемся в iframe
                        self.driver.switch_to.frame(iframe)

                        # Ищем PDF-ссылки внутри iframe
                        try:
                            links = WebDriverWait(self.driver, 5).until(
                                EC.presence_of_all_elements_located(
                                    (By.XPATH, '//a[contains(@href, ".pdf") or contains(@href, ".PDF")]')))
                            pdf_links.extend([(link.get_attribute('href'), link.text) for link in links])
                        except:
                            pass

                        # Возвращаемся к основному контенту
                        self.driver.switch_to.default_content()
                    except Exception as e:
                        print(f">>> Ошибка при обработке iframe: {str(e)}...")
                        self.driver.switch_to.default_content()
                        continue

                # Поиск в основном документе
                try:
                    main_links = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_all_elements_located(
                            (By.XPATH, '//a[contains(@href, ".pdf") or contains(@href, ".PDF")]')))
                    pdf_links.extend([(link.get_attribute('href'), link.text) for link in main_links])
                except Exception as ex:
                    print(f"Ошибка [{ex}]")

                if not pdf_links:
                    print(">>> PDF-ссылки не найдены...")
                    continue

                print(f">>> Найдено {len(pdf_links)} PDF-файлов...")

                # Скачивание файлов
                for i, (pdf_url, link_text) in enumerate(pdf_links, 1):
                    try:
                        if not pdf_url:
                            continue

                        # Обработка относительных ссылок
                        if not pdf_url.startswith(('http://', 'https://')):
                            current_url = self.driver.current_url
                            pdf_url = urljoin(current_url, pdf_url)

                        # Генерация имени файла
                        filename = os.path.basename(pdf_url.split('?')[0])
                        if not filename.lower().endswith('.pdf'):
                            filename = f"{link_text.strip() or 'document'}_{i}.pdf".replace('/', '_')

                        save_path = os.path.join(save_dir, filename)

                        print(f">>> [{i}/{len(pdf_links)}] Скачиваю: {filename}...")
                        print(f"     URL: {pdf_url}...")

                        # Скачивание с помощью requests
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                        }

                        session = requests.Session()
                        # Перенос cookies из Selenium в requests
                        for cookie in self.driver.get_cookies():
                            session.cookies.set(cookie['name'], cookie['value'])

                        response = session.get(pdf_url, headers=headers, stream=True, timeout=60)
                        response.raise_for_status()

                        with open(save_path, 'wb') as f:
                            for chunk in response.iter_content(1024):
                                f.write(chunk)

                        print(f">>> Успешно сохранен: {save_path}...")
                        print(f">>> Размер: {os.path.getsize(save_path) / 1024:.2f} KB...")

                    except Exception as e:
                        print(f">>> Ошибка при скачивании: {str(e)}...")

            except Exception as e:
                print(f">>> Ошибка при обработке страницы: {str(e)}...")
                self.driver.save_screenshot(os.path.join(save_dir, f'error_{key}.png'))
            finally:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])

    def __search_new_page_link(self):
        try:
            # Получаем заголовки страниц
            titles = WebDriverWait(self.driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-type="title"]'))
            )

            for title in titles[:1]:  # Обрабатываем только первый элемент
                try:
                    # Создаем безопасное имя файла из текста заголовка
                    page_title = title.text.strip() or "untitled"
                    safe_filename = "".join([c if c.isalnum() or c in (' ', '_') else '_' for c in page_title])[
                                    :50] + ".json"

                    print(f">>> Обрабатываем: {page_title}...")
                    title.click()
                    time.sleep(2)  # Даем время для загрузки контента

                    # Собираем все ссылки с data-type="content"
                    content_links = {}
                    try:
                        links = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[data-type="content"]'))
                        )
                        for i, link in enumerate(links, 1):
                            href = link.get_attribute('href')
                            if href:
                                content_links[f"content_{i}"] = href
                    except Exception as e:
                        print(f">>> Ошибка при поиске контент-ссылок: {e}...")

                    # Добавляем итоговую аттестацию
                    try:
                        attestation = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[data-type="event"]'))
                        )
                        content_links["final_attestation"] = attestation.get_attribute('href')
                        print(f">>> Итоговая аттестация: {content_links['final_attestation']}")
                    except Exception as e:
                        print(f">>> Не найдена итоговая аттестация: {e}...")

                    # Сохраняем данные в JSON
                    with open(safe_filename, 'w', encoding='utf-8') as f:
                        json.dump(content_links, f, indent=4, ensure_ascii=False)

                    print(f">>> Данные сохранены в: {safe_filename}...")

                except Exception as e:
                    print(f">>> Ошибка при обработке страницы: {e}...")
                    continue

        except Exception as e:
            print(f">>> Критическая ошибка: {e}...")
            self.driver.save_screenshot('search_error.png')

    def __stop(self):
        self.driver.close()
        self.driver.quit()

    def parser(self):
        self.__set_up()
        self.__get_url()
        self.__login()
        #self.__search_link()
        #self.__open_new_page()
        self.__search_pdf()
        self.__stop()


if __name__ == "__main__":
    SenergyPars(url='https://lms.synergy.ru/', user_name=user_name, user_pass=user_pass, key=None).parser()
