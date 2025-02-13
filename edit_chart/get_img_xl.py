from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from config.auto_search_dir import  path_to_img


def open_site(month):
    # Настройка опций для Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Запуск в headless режиме
    # Инициализация драйвера с опциями
    driver = webdriver.Chrome(options=chrome_options)

    # Устанавливаем размер окна (ширина, высота)
    driver.set_window_size(1600, 1000)
    # Открытие сайта
    driver.get(fr'C:\Users\kiraf\PycharmProjects\graficpvz\browser\{month}.html')

    # Сделать скриншот и сохранить его в файл
    driver.save_screenshot(path_to_img)

    # Закрытие драйвера
    driver.quit()
