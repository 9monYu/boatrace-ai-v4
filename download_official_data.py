import argparse
import os
import re
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait


def download(url, download_directory, start, end):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.add_experimental_option(
        "prefs",
        {
            "profile.managed_default_content_settings.images": 2,
            "credentials_enable_service": False,
            "download.default_directory": download_directory,
            "download_bubble.partial_view_enabled": False,
        },
    )
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver=driver, timeout=20)
    driver.get(url)
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "menu")))
    select_box = wait.until(EC.presence_of_element_located((By.NAME, "MONTH")))
    select = Select(select_box)
    target_ym_index_list = []
    for ym_index, option in enumerate(select.options):
        ym_match = re.search(r"(\d{4})年\s*(\d{1,2})月", option.text.strip())
        if ym_match is None:
            continue
        if start <= int(ym_match.group(1)) * 100 + int(ym_match.group(2)) <= end:
            target_ym_index_list.append(ym_index)
    for ym_index in target_ym_index_list:
        select.select_by_index(ym_index)
        driver.switch_to.default_content()
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "JYOU")))
        for radio in wait.until(EC.presence_of_all_elements_located((By.NAME, "MDAY"))):
            radio.click()
            download_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@onclick="download(this)"]')))
            download_button.click()
        driver.switch_to.default_content()
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "menu")))
        select_box = wait.until(EC.presence_of_element_located((By.NAME, "MONTH")))
        select = Select(select_box)
    time.sleep(5)
    driver.quit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("start", type=int)
    parser.add_argument("end", type=int)
    args = parser.parse_args()

    download(
        "https://www1.mbrace.or.jp/od2/B/dindex.html",
        os.path.join(os.getcwd(), "official_data", "race"),
        args.start,
        args.end,
    )

    download(
        "https://www1.mbrace.or.jp/od2/K/dindex.html",
        os.path.join(os.getcwd(), "official_data", "result"),
        args.start,
        args.end,
    )


if __name__ == "__main__":
    main()
