import argparse
import csv
import math
import os
import platform
import re
import statistics
import time
from datetime import date, datetime, timedelta

import lhafile
import lightgbm
import numpy
import pandas
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from constants import (
    CSV_COLUMN_LIST,
    GRADE_LIST,
    RACER_CLASS_LIST,
    REQUEST_HEADERS,
    SEED_COUNT,
    TRIFECTA_LIST,
    USER_AGENT,
    WEATHER_LIST,
    WIND_DIRECTION_ANGLES,
)
from database import Session
from models import PeriodStat, Race, Racer, Ticket, VenueStat


def download(url: str, target_date: int):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.page_load_strategy = "eager"
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(f"--user-agent={USER_AGENT}")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    if platform.system() == "Linux":
        chrome_options.add_argument("--no-sandbox")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.add_experimental_option(
        "prefs",
        {
            "profile.managed_default_content_settings.images": 2,
            "credentials_enable_service": False,
            "download.default_directory": os.path.join(os.getcwd(), "temp"),
            "download_bubble.partial_view_enabled": False,
        },
    )
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver=driver, timeout=5)
    driver.get(url)
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "menu")))
    select_box = wait.until(EC.presence_of_element_located((By.NAME, "MONTH")))
    select = Select(select_box)

    for ym_index, option in enumerate(select.options):
        ym_match = re.search(r"(\d{4})年\s*(\d{1,2})月", option.text.strip())
        if ym_match is None:
            continue
        if int(ym_match.group(1)) * 100 + int(ym_match.group(2)) == target_date // 100:
            select.select_by_index(ym_index)
            driver.switch_to.default_content()
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "JYOU")))
            for radio in wait.until(EC.presence_of_all_elements_located((By.NAME, "MDAY"))):
                if radio.get_attribute("value") == str(target_date % 100).zfill(2):
                    radio.click()
                    download_button = wait.until(
                        EC.element_to_be_clickable((By.XPATH, '//input[@onclick="download(this)"]'))
                    )
                    download_button.click()
                    break
            break
    time.sleep(5)
    driver.quit()


def decompress(file_name: str):
    directory_path = os.path.join(os.getcwd(), "temp")
    file_path = os.path.join(directory_path, file_name)
    file = lhafile.LhaFile(file_path)
    for info in file.infolist():
        with open(os.path.join(directory_path, info.filename), "wb") as newfile:
            newfile.write(file.read(info.filename))
    del file
    os.remove(file_path)


def import_official_data(target_date: int):
    year = target_date // 10000
    month = (target_date // 100) % 100
    day = target_date % 100
    # race
    with open(os.path.join(os.getcwd(), "temp", f"B{target_date % 1000000}.TXT"), "r", encoding="CP932") as f:
        venue = None
        day_number = None
        if 5 <= month <= 10:
            start = date(year, 5, 1)
            end = date(year, 10, 31)
        else:
            start = date(year - 1, 11, 1)
            end = date(year, 4, 30)
        period_progress_rate = round(((date(year, month, day) - start).days / (end - start).days) * 100, 2)
        for line in f:
            bgn_match = re.match(r"^([0-9]{2})(BBGN)", line)
            if bgn_match is not None:
                venue = bgn_match.group(1)
            end_match = re.match(r"^([0-9]{2})(BEND)", line)
            if end_match is not None:
                venue = None
            day_match = re.match(r"^   第　([１-７])日.*$", line)
            if day_match is not None:
                day_number = int(day_match.group(1))
            race_match = re.match(r"^　?([０-９]{1,2})Ｒ.*([０-９]{2})：([０-９]{2}) $", line)
            if race_match is not None:
                race_number = int(race_match.group(1))
                hour = int(race_match.group(2))
                minute = int(race_match.group(3))
                race_id = int(f"{target_date}{venue}{str(race_number).zfill(2)}")
                race = Session.get(Race, race_id)
                if race is not None:
                    race.date = target_date
                    race.period_progress_rate = period_progress_rate
                    race.venue = int(venue)
                    race.race_number = race_number
                    race.deadline = f"{str(hour).zfill(2)}:{str(minute).zfill(2)}"
                    race.day_number = day_number
                else:
                    Session.add(
                        Race(
                            id=race_id,
                            date=target_date,
                            period_progress_rate=period_progress_rate,
                            venue=int(venue),
                            race_number=race_number,
                            deadline=f"{str(hour).zfill(2)}:{str(minute).zfill(2)}",
                            day_number=day_number,
                        )
                    )
    Session.commit()

    # result
    with open(os.path.join(os.getcwd(), "temp", f"K{target_date % 1000000}.TXT"), "r", encoding="CP932") as f:
        venue = None
        for line in f:
            bgn_match = re.match(r"^([0-9]{2})(KBGN)", line)
            if bgn_match is not None:
                venue = bgn_match.group(1)
            end_match = re.match(r"^([0-9]{2})(KEND)", line)
            if end_match is not None:
                venue = None
            result_match = re.match(r"^(\s{10,11})([0-9]{1,2})(R)", line)
            if result_match is not None:
                race_number = result_match.group(2)
                race_id = int(f"{target_date}{venue}{str(race_number).zfill(2)}")
                race = Session.get(Race, race_id)
                if race is not None:
                    words = [word for word in line.split(" ") if word]
                    words = [x.strip() for x in words if x.strip()]
                    # 中止
                    if words[1] == "中　止":
                        race.is_cancel = 1
                    elif len(words) == 9:
                        # 3連単● 3連複● 2連単● 2連複●
                        if (
                            re.match(r"^[1-6]{1}-[1-6]{1}-[1-6]{1}$", words[1])
                            and re.match(r"^[1-6]{1}-[1-6]{1}-[1-6]{1}$", words[3])
                            and re.match(r"^[1-6]{1}-[1-6]{1}$", words[5])
                            and re.match(r"^[1-6]{1}-[1-6]{1}$", words[7])
                        ):
                            race.first = int(words[1].split("-")[0])
                            race.second = int(words[1].split("-")[1])
                            race.third = int(words[1].split("-")[2])
                            race.odds_trifecta = round(int(words[2]) / 100, 1)
                            race.odds_trio = round(int(words[4]) / 100, 1)
                            race.odds_exacta = round(int(words[6]) / 100, 1)
                            race.odds_quinella = round(int(words[8]) / 100, 1)
                    elif len(words) == 8:
                        # 3連単● 3連複● 2連単● 2連複×
                        if (
                            re.match(r"^[1-6]{1}-[1-6]{1}-[1-6]{1}$", words[1])
                            and re.match(r"^[1-6]{1}-[1-6]{1}-[1-6]{1}$", words[3])
                            and re.match(r"^[1-6]{1}-[1-6]{1}$", words[5])
                        ):
                            race.first = int(words[1].split("-")[0])
                            race.second = int(words[1].split("-")[1])
                            race.third = int(words[1].split("-")[2])
                            race.odds_trifecta = round(int(words[2]) / 100, 1)
                            race.odds_trio = round(int(words[4]) / 100, 1)
                            race.odds_exacta = round(int(words[6]) / 100, 1)
                        # 3連単● 3連複● 2連単× 2連複●
                        elif (
                            re.match(r"^[1-6]{1}-[1-6]{1}-[1-6]{1}$", words[1])
                            and re.match(r"^[1-6]{1}-[1-6]{1}-[1-6]{1}$", words[3])
                            and re.match(r"^[1-6]{1}-[1-6]{1}$", words[6])
                        ):
                            race.first = int(words[1].split("-")[0])
                            race.second = int(words[1].split("-")[1])
                            race.third = int(words[1].split("-")[2])
                            race.odds_trifecta = round(int(words[2]) / 100, 1)
                            race.odds_trio = round(int(words[4]) / 100, 1)
                            race.odds_quinella = round(int(words[7]) / 100, 1)
                        # 3連単● 3連複× 2連単● 2連複●
                        elif (
                            re.match(r"^[1-6]{1}-[1-6]{1}-[1-6]{1}$", words[1])
                            and re.match(r"^[1-6]{1}-[1-6]{1}$", words[4])
                            and re.match(r"^[1-6]{1}-[1-6]{1}$", words[6])
                        ):
                            race.first = int(words[1].split("-")[0])
                            race.second = int(words[1].split("-")[1])
                            race.third = int(words[1].split("-")[2])
                            race.odds_trifecta = round(int(words[2]) / 100, 1)
                            race.odds_exacta = round(int(words[5]) / 100, 1)
                            race.odds_quinella = round(int(words[7]) / 100, 1)
                        else:
                            pass
                    elif len(words) == 7:
                        # 3連単● 3連複● 2連単● 2連複- ※?
                        if (
                            re.match(r"^[1-6]{1}-[1-6]{1}-[1-6]{1}$", words[1])
                            and re.match(r"^[1-6]{1}-[1-6]{1}-[1-6]{1}$", words[3])
                            and re.match(r"^[1-6]{1}-[1-6]{1}$", words[5])
                        ):
                            race.first = int(words[1].split("-")[0])
                            race.second = int(words[1].split("-")[1])
                            race.third = int(words[1].split("-")[2])
                            race.odds_trifecta = round(int(words[2]) / 100, 1)
                            race.odds_trio = round(int(words[4]) / 100, 1)
                            race.odds_exacta = round(int(words[6]) / 100, 1)
                        # 3連単● 3連複× 2連単● 2連複×
                        elif re.match(r"^[1-6]{1}-[1-6]{1}-[1-6]{1}$", words[1]) and re.match(
                            r"^[1-6]{1}-[1-6]{1}$", words[4]
                        ):
                            race.first = int(words[1].split("-")[0])
                            race.second = int(words[1].split("-")[1])
                            race.third = int(words[1].split("-")[2])
                            race.odds_trifecta = round(int(words[2]) / 100, 1)
                            race.odds_exacta = round(int(words[5]) / 100, 1)
                        # 3連単× 3連複× 2連単● 2連複●
                        elif re.match(r"^[1-6]{1}-[1-6]{1}$", words[3]) and re.match(r"^[1-6]{1}-[1-6]{1}$", words[5]):
                            race.first = int(words[3].split("-")[0])
                            race.second = int(words[3].split("-")[1])
                            race.odds_exacta = round(int(words[4]) / 100, 1)
                            race.odds_quinella = round(int(words[6]) / 100, 1)
                        else:
                            pass
                    elif len(words) == 6:
                        # 3連単× 3連複× 2連単● 2連複×
                        if re.match(r"^[1-6]{1}-[1-6]{1}$", words[3]):
                            race.first = int(words[3].split("-")[0])
                            race.second = int(words[3].split("-")[1])
                            race.odds_exacta = round(int(words[4]) / 100, 1)
                    elif len(words) == 5:
                        # 3連単- 3連複- 2連単● 2連複●
                        if re.match(r"^[1-6]{1}-[1-6]{1}$", words[1]) and re.match(r"^[1-6]{1}-[1-6]{1}$", words[3]):
                            race.first = int(words[1].split("-")[0])
                            race.second = int(words[1].split("-")[1])
                            race.odds_exacta = round(int(words[2]) / 100, 1)
                            race.odds_quinella = round(int(words[4]) / 100, 1)
                    elif len(words) == 4:
                        # 3連単- 3連複- 2連単● 2連複×
                        if re.match(r"^[1-6]{1}-[1-6]{1}$", words[1]):
                            race.first = int(words[1].split("-")[0])
                            race.second = int(words[1].split("-")[1])
                            race.odds_exacta = round(int(words[2]) / 100, 1)
                    else:
                        pass
                    if race.is_cancel is None:
                        race.is_cancel = 0
    Session.commit()


def scrape(target_date: int):
    race_list = Session.scalars(
        select(Race)
        .where(
            Race.is_cancel == 0,
            Race.date == target_date,
        )
        .order_by(Race.id.asc())
    ).all()
    for race in race_list:
        racer_list = [
            [],
            [],
            [],
            [],
            [],
            [],
        ]

        # race and racer
        for retry in range(3):
            try:
                response = requests.get(
                    f"https://www.boatrace.jp/owpc/pc/race/racelist?rno={race.race_number}&jcd={race.venue:02d}&hd={race.date}",
                    headers=REQUEST_HEADERS,
                    timeout=10,
                )
                response.raise_for_status()
                break
            except requests.RequestException:
                if retry == 2:
                    raise
                time.sleep(5)

        beautifulsoup = BeautifulSoup(response.text, "html.parser")

        grade = None
        try:
            classes = beautifulsoup.find("div", class_="heading2_title").get("class")
            if "is-SGa" in classes:
                grade = "SG"
            elif "is-G1a" in classes:
                grade = "PG1"
            elif "is-G1b" in classes:
                grade = "G1"
            elif "is-G2b" in classes:
                grade = "G2"
            elif "is-G3b" in classes:
                grade = "G3"
            elif "is-ippan" in classes:
                grade = "一般"
            else:
                pass
        except Exception:
            pass

        is_last_day = None
        try:
            if (
                beautifulsoup.find("li", class_="is-active2")
                .find("span", class_="tab2_inner")
                .find("span")
                .get_text(strip=True)
                == "最終日"
            ):
                is_last_day = 1
            else:
                is_last_day = 0
        except Exception:
            pass

        has_stabilizer = None
        try:
            if (
                beautifulsoup.find("div", class_="title16_titleLabels__add2020").find("span", class_="label2 is-type1")
                is not None
            ):
                has_stabilizer = 1
            else:
                has_stabilizer = 0
        except Exception:
            pass

        soup_list = beautifulsoup.find_all("tbody", class_="is-fs12")
        for soup in soup_list:
            soup_td_list = soup.find("tr").find_all("td")
            soup_div_list = soup_td_list[2].find_all("div")
            # boat number
            boat_number = int(soup_td_list[0].get_text(strip=True))
            racer_index = boat_number - 1
            racer_list[racer_index].append(race.id)
            racer_list[racer_index].append(boat_number)
            # racer number, racer class
            div0_text = soup_div_list[0].get_text(strip=True)
            racer_list[racer_index].append(int(div0_text.split("/")[0]))
            racer_list[racer_index].append(div0_text.split("/")[1])
            # branch, hometown, age, weight
            div2_text = soup_div_list[2].get_text().replace("\n", "/").replace(" ", "")
            racer_list[racer_index].append(div2_text.split("/")[0])
            if div2_text.split("/")[1] != "－":
                racer_list[racer_index].append(div2_text.split("/")[1])
            else:
                racer_list[racer_index].append(None)
            racer_list[racer_index].append(int(div2_text.split("/")[2].replace("歳", "")))
            if div2_text.split("/")[3].replace("kg", "") != "-":
                racer_list[racer_index].append(float(div2_text.split("/")[3].replace("kg", "")))
            else:
                racer_list[racer_index].append(None)
            # f, l, st
            td3_text = soup_td_list[3].get_text().replace(" ", "")
            racer_list[racer_index].append(int(td3_text.split("\n")[0].replace("F", "")))
            racer_list[racer_index].append(int(td3_text.split("\n")[1].replace("L", "")))
            if td3_text.split("\n")[2] != "-":
                racer_list[racer_index].append(float(td3_text.split("\n")[2]))
            else:
                racer_list[racer_index].append(None)
            # all venue
            td4_text = soup_td_list[4].get_text().replace(" ", "")
            if td4_text.split("\n")[0] != "-":
                racer_list[racer_index].append(float(td4_text.split("\n")[0]))
            else:
                racer_list[racer_index].append(None)
            if td4_text.split("\n")[1] != "-":
                racer_list[racer_index].append(float(td4_text.split("\n")[1]))
            else:
                racer_list[racer_index].append(None)
            if td4_text.split("\n")[2] != "-":
                racer_list[racer_index].append(float(td4_text.split("\n")[2]))
            else:
                racer_list[racer_index].append(None)
            # this venue
            td5_text = soup_td_list[5].get_text().replace(" ", "")
            if td5_text.split("\n")[0] != "-":
                racer_list[racer_index].append(float(td5_text.split("\n")[0]))
            else:
                racer_list[racer_index].append(None)
            if td5_text.split("\n")[1] != "-":
                racer_list[racer_index].append(float(td5_text.split("\n")[1]))
            else:
                racer_list[racer_index].append(None)
            if td5_text.split("\n")[2] != "-":
                racer_list[racer_index].append(float(td5_text.split("\n")[2]))
            else:
                racer_list[racer_index].append(None)
            # motor
            td6_text = soup_td_list[6].get_text().replace(" ", "")
            if td6_text.split("\n")[1] != "-":
                racer_list[racer_index].append(float(td6_text.split("\n")[1]))
            else:
                racer_list[racer_index].append(None)
            if td6_text.split("\n")[2] != "-":
                racer_list[racer_index].append(float(td6_text.split("\n")[2]))
            else:
                racer_list[racer_index].append(None)
            # boat
            td7_text = soup_td_list[7].get_text().replace(" ", "")
            if td7_text.split("\n")[1] != "-":
                racer_list[racer_index].append(float(td7_text.split("\n")[1]))
            else:
                racer_list[racer_index].append(None)
            if td7_text.split("\n")[2] != "-":
                racer_list[racer_index].append(float(td7_text.split("\n")[2]))
            else:
                racer_list[racer_index].append(None)

        # before info
        for retry in range(3):
            try:
                response = requests.get(
                    f"https://www.boatrace.jp/owpc/pc/race/beforeinfo?rno={race.race_number}&jcd={race.venue:02d}&hd={race.date}",
                    headers=REQUEST_HEADERS,
                    timeout=10,
                )
                response.raise_for_status()
                break
            except requests.RequestException:
                if retry == 2:
                    raise
                time.sleep(5)

        beautifulsoup = BeautifulSoup(response.text, "html.parser")

        before_info_temperature = None
        before_info_weather = None
        before_info_wind_speed = None
        before_info_wind_direction = None
        before_info_water_temperature = None
        before_info_wave_height = None

        # course, start timing, weight, adjusted weight, display time, tilt
        boat1_before_info_list = [None, None, None, None, None, None]
        boat2_before_info_list = [None, None, None, None, None, None]
        boat3_before_info_list = [None, None, None, None, None, None]
        boat4_before_info_list = [None, None, None, None, None, None]
        boat5_before_info_list = [None, None, None, None, None, None]
        boat6_before_info_list = [None, None, None, None, None, None]

        soup_list = beautifulsoup.find_all("div", class_="weather1_bodyUnit")
        # temperature
        try:
            before_info_temperature = float(
                soup_list[0].find("span", class_="weather1_bodyUnitLabelData").get_text(strip=True).replace("℃", "")
            )
        except Exception:
            pass
        # weather
        try:
            before_info_weather = soup_list[1].find("span", class_="weather1_bodyUnitLabelTitle").get_text(strip=True)
        except Exception:
            pass
        # wind speed
        try:
            before_info_wind_speed = int(
                soup_list[2].find("span", class_="weather1_bodyUnitLabelData").get_text(strip=True).replace("m", "")
            )
        except Exception:
            pass
        # wind direction
        try:
            for class_ in soup_list[3].find("p", class_="weather1_bodyUnitImage").get("class"):
                if class_.startswith("is-wind"):
                    before_info_wind_direction = int(class_.replace("is-wind", ""))
                    break
        except Exception:
            pass
        # water temperature
        try:
            before_info_water_temperature = float(
                soup_list[4].find("span", class_="weather1_bodyUnitLabelData").get_text(strip=True).replace("℃", "")
            )
        except Exception:
            pass
        # wave height
        try:
            before_info_wave_height = int(
                soup_list[5].find("span", class_="weather1_bodyUnitLabelData").get_text(strip=True).replace("cm", "")
            )
        except Exception:
            pass

        # course
        # start timing
        for course, soup in enumerate(beautifulsoup.find("tbody", class_="is-p10-0").find_all("tr"), start=1):
            boat_number_span = soup.find("span", class_="table1_boatImage1Number")
            if boat_number_span is not None:
                try:
                    boat_number = int(boat_number_span.get_text(strip=True))
                    start_timing = soup.find("span", class_="table1_boatImage1Time").get_text(strip=True)
                    match boat_number:
                        case 1:
                            boat1_before_info_list[0] = course
                            if start_timing.startswith("F"):
                                boat1_before_info_list[1] = float(start_timing.replace("F", "-0"))
                            elif start_timing.startswith("L"):
                                boat1_before_info_list[1] = float(start_timing.replace("L", "1"))
                            else:
                                boat1_before_info_list[1] = float(start_timing)
                        case 2:
                            boat2_before_info_list[0] = course
                            if start_timing.startswith("F"):
                                boat2_before_info_list[1] = float(start_timing.replace("F", "-0"))
                            elif start_timing.startswith("L"):
                                boat2_before_info_list[1] = float(start_timing.replace("L", "1"))
                            else:
                                boat2_before_info_list[1] = float(start_timing)
                        case 3:
                            boat3_before_info_list[0] = course
                            if start_timing.startswith("F"):
                                boat3_before_info_list[1] = float(start_timing.replace("F", "-0"))
                            elif start_timing.startswith("L"):
                                boat3_before_info_list[1] = float(start_timing.replace("L", "1"))
                            else:
                                boat3_before_info_list[1] = float(start_timing)
                        case 4:
                            boat4_before_info_list[0] = course
                            if start_timing.startswith("F"):
                                boat4_before_info_list[1] = float(start_timing.replace("F", "-0"))
                            elif start_timing.startswith("L"):
                                boat4_before_info_list[1] = float(start_timing.replace("L", "1"))
                            else:
                                boat4_before_info_list[1] = float(start_timing)
                        case 5:
                            boat5_before_info_list[0] = course
                            if start_timing.startswith("F"):
                                boat5_before_info_list[1] = float(start_timing.replace("F", "-0"))
                            elif start_timing.startswith("L"):
                                boat5_before_info_list[1] = float(start_timing.replace("L", "1"))
                            else:
                                boat5_before_info_list[1] = float(start_timing)
                        case 6:
                            boat6_before_info_list[0] = course
                            if start_timing.startswith("F"):
                                boat6_before_info_list[1] = float(start_timing.replace("F", "-0"))
                            elif start_timing.startswith("L"):
                                boat6_before_info_list[1] = float(start_timing.replace("L", "1"))
                            else:
                                boat6_before_info_list[1] = float(start_timing)
                        case _:
                            pass
                except ValueError:
                    pass

        for boat_number, soup in enumerate(beautifulsoup.find_all("tbody", class_="is-fs12"), start=1):
            for index, tr in enumerate(soup.find_all("tr")):
                if index == 0:
                    td_list = tr.find_all("td")
                    # weight
                    try:
                        match boat_number:
                            case 1:
                                boat1_before_info_list[2] = float(td_list[3].get_text(strip=True).replace("kg", ""))
                            case 2:
                                boat2_before_info_list[2] = float(td_list[3].get_text(strip=True).replace("kg", ""))
                            case 3:
                                boat3_before_info_list[2] = float(td_list[3].get_text(strip=True).replace("kg", ""))
                            case 4:
                                boat4_before_info_list[2] = float(td_list[3].get_text(strip=True).replace("kg", ""))
                            case 5:
                                boat5_before_info_list[2] = float(td_list[3].get_text(strip=True).replace("kg", ""))
                            case 6:
                                boat6_before_info_list[2] = float(td_list[3].get_text(strip=True).replace("kg", ""))
                            case _:
                                pass
                    except ValueError:
                        pass
                    # display time
                    try:
                        match boat_number:
                            case 1:
                                boat1_before_info_list[4] = float(td_list[4].get_text(strip=True))
                            case 2:
                                boat2_before_info_list[4] = float(td_list[4].get_text(strip=True))
                            case 3:
                                boat3_before_info_list[4] = float(td_list[4].get_text(strip=True))
                            case 4:
                                boat4_before_info_list[4] = float(td_list[4].get_text(strip=True))
                            case 5:
                                boat5_before_info_list[4] = float(td_list[4].get_text(strip=True))
                            case 6:
                                boat6_before_info_list[4] = float(td_list[4].get_text(strip=True))
                            case _:
                                pass
                    except ValueError:
                        pass
                    # tilt
                    try:
                        match boat_number:
                            case 1:
                                boat1_before_info_list[5] = float(td_list[5].get_text(strip=True))
                            case 2:
                                boat2_before_info_list[5] = float(td_list[5].get_text(strip=True))
                            case 3:
                                boat3_before_info_list[5] = float(td_list[5].get_text(strip=True))
                            case 4:
                                boat4_before_info_list[5] = float(td_list[5].get_text(strip=True))
                            case 5:
                                boat5_before_info_list[5] = float(td_list[5].get_text(strip=True))
                            case 6:
                                boat6_before_info_list[5] = float(td_list[5].get_text(strip=True))
                            case _:
                                pass
                    except ValueError:
                        pass
                elif index == 2:
                    # adjusted weight
                    try:
                        match boat_number:
                            case 1:
                                boat1_before_info_list[3] = float(tr.find("td").get_text(strip=True))
                            case 2:
                                boat2_before_info_list[3] = float(tr.find("td").get_text(strip=True))
                            case 3:
                                boat3_before_info_list[3] = float(tr.find("td").get_text(strip=True))
                            case 4:
                                boat4_before_info_list[3] = float(tr.find("td").get_text(strip=True))
                            case 5:
                                boat5_before_info_list[3] = float(tr.find("td").get_text(strip=True))
                            case 6:
                                boat6_before_info_list[3] = float(tr.find("td").get_text(strip=True))
                            case _:
                                pass
                    except ValueError:
                        pass
                else:
                    pass
            if boat_number == 6:
                break

        racer_list[0].extend(boat1_before_info_list)
        racer_list[1].extend(boat2_before_info_list)
        racer_list[2].extend(boat3_before_info_list)
        racer_list[3].extend(boat4_before_info_list)
        racer_list[4].extend(boat5_before_info_list)
        racer_list[5].extend(boat6_before_info_list)

        # result
        for retry in range(3):
            try:
                response = requests.get(
                    f"https://www.boatrace.jp/owpc/pc/race/raceresult?rno={race.race_number}&jcd={race.venue:02d}&hd={race.date}",
                    headers=REQUEST_HEADERS,
                    timeout=10,
                )
                response.raise_for_status()
                break
            except requests.RequestException:
                if retry == 2:
                    raise
                time.sleep(5)

        beautifulsoup = BeautifulSoup(response.text, "html.parser")

        temperature = None
        weather = None
        wind_speed = None
        wind_direction = None
        water_temperature = None
        wave_height = None

        winning_style = None

        # course, start timing, result, race time
        boat1_result_list = [None, None, None, None]
        boat2_result_list = [None, None, None, None]
        boat3_result_list = [None, None, None, None]
        boat4_result_list = [None, None, None, None]
        boat5_result_list = [None, None, None, None]
        boat6_result_list = [None, None, None, None]

        soup_list = beautifulsoup.find_all("div", class_="weather1_bodyUnit")
        # temperature
        try:
            temperature = float(
                soup_list[0].find("span", class_="weather1_bodyUnitLabelData").get_text(strip=True).replace("℃", "")
            )
        except Exception:
            pass
        # weather
        try:
            weather = soup_list[1].find("span", class_="weather1_bodyUnitLabelTitle").get_text(strip=True)
        except Exception:
            pass
        # wind speed
        try:
            wind_speed = int(
                soup_list[2].find("span", class_="weather1_bodyUnitLabelData").get_text(strip=True).replace("m", "")
            )
        except Exception:
            pass
        # wind direction
        try:
            for class_ in soup_list[3].find("p", class_="weather1_bodyUnitImage").get("class"):
                if class_.startswith("is-wind"):
                    wind_direction = int(class_.replace("is-wind", ""))
                    break
        except Exception:
            pass
        # water temperature
        try:
            water_temperature = float(
                soup_list[4].find("span", class_="weather1_bodyUnitLabelData").get_text(strip=True).replace("℃", "")
            )
        except Exception:
            pass
        # wave height
        try:
            wave_height = int(
                soup_list[5].find("span", class_="weather1_bodyUnitLabelData").get_text(strip=True).replace("cm", "")
            )
        except Exception:
            pass

        # winning style
        try:
            winning_style = (
                beautifulsoup.find("table", class_="is-h108__3rdadd").find("td", class_="is-fs16").get_text(strip=True)
            )
        except Exception:
            pass

        # course
        # start timing
        for course, soup in enumerate(
            beautifulsoup.find("table", class_="is-h292__3rdadd").find("tbody").find_all("tr"), start=1
        ):
            boat_number_span = soup.find("span", class_="table1_boatImage1Number")
            if boat_number_span is not None:
                try:
                    boat_number = int(boat_number_span.get_text(strip=True))
                    start_timing = soup.find("span", class_="table1_boatImage1Time").get_text(strip=True).split(" ")[0]
                    match boat_number:
                        case 1:
                            boat1_result_list[0] = course
                            if start_timing.startswith("F"):
                                boat1_result_list[1] = float(start_timing.replace("F", "-0"))
                            elif start_timing.startswith("L"):
                                boat1_result_list[1] = float(start_timing.replace("L", "1"))
                            else:
                                boat1_result_list[1] = float(start_timing)
                        case 2:
                            boat2_result_list[0] = course
                            if start_timing.startswith("F"):
                                boat2_result_list[1] = float(start_timing.replace("F", "-0"))
                            elif start_timing.startswith("L"):
                                boat2_result_list[1] = float(start_timing.replace("L", "1"))
                            else:
                                boat2_result_list[1] = float(start_timing)
                        case 3:
                            boat3_result_list[0] = course
                            if start_timing.startswith("F"):
                                boat3_result_list[1] = float(start_timing.replace("F", "-0"))
                            elif start_timing.startswith("L"):
                                boat3_result_list[1] = float(start_timing.replace("L", "1"))
                            else:
                                boat3_result_list[1] = float(start_timing)
                        case 4:
                            boat4_result_list[0] = course
                            if start_timing.startswith("F"):
                                boat4_result_list[1] = float(start_timing.replace("F", "-0"))
                            elif start_timing.startswith("L"):
                                boat4_result_list[1] = float(start_timing.replace("L", "1"))
                            else:
                                boat4_result_list[1] = float(start_timing)
                        case 5:
                            boat5_result_list[0] = course
                            if start_timing.startswith("F"):
                                boat5_result_list[1] = float(start_timing.replace("F", "-0"))
                            elif start_timing.startswith("L"):
                                boat5_result_list[1] = float(start_timing.replace("L", "1"))
                            else:
                                boat5_result_list[1] = float(start_timing)
                        case 6:
                            boat6_result_list[0] = course
                            if start_timing.startswith("F"):
                                boat6_result_list[1] = float(start_timing.replace("F", "-0"))
                            elif start_timing.startswith("L"):
                                boat6_result_list[1] = float(start_timing.replace("L", "1"))
                            else:
                                boat6_result_list[1] = float(start_timing)
                        case _:
                            pass
                except Exception:
                    pass

        # result
        # race time
        for table in beautifulsoup.select("table.is-w495"):
            headers = [th.get_text(strip=True) for th in table.select("thead th")]
            if headers == ["着", "枠", "ボートレーサー", "レースタイム"]:
                for tbody in table.find_all("tbody"):
                    td_list = tbody.find("tr").find_all("td")
                    result = None
                    try:
                        if td_list[0].get_text(strip=True) in ["１", "２", "３", "４", "５", "６"]:
                            result = int(td_list[0].get_text(strip=True))
                    except Exception:
                        pass
                    race_time = None
                    if result is not None and result < 5:
                        try:
                            minutes = int(td_list[3].get_text(strip=True).split("'")[0])
                            seconds = int(td_list[3].get_text(strip=True).split("'")[1].split('"')[0])
                            decimal = int(td_list[3].get_text(strip=True).split("'")[1].split('"')[1])
                            race_time = minutes * 60 + seconds + decimal * 0.1
                        except Exception:
                            pass
                    match int(td_list[1].get_text(strip=True)):
                        case 1:
                            boat1_result_list[2] = result
                            boat1_result_list[3] = race_time
                        case 2:
                            boat2_result_list[2] = result
                            boat2_result_list[3] = race_time
                        case 3:
                            boat3_result_list[2] = result
                            boat3_result_list[3] = race_time
                        case 4:
                            boat4_result_list[2] = result
                            boat4_result_list[3] = race_time
                        case 5:
                            boat5_result_list[2] = result
                            boat5_result_list[3] = race_time
                        case 6:
                            boat6_result_list[2] = result
                            boat6_result_list[3] = race_time
                        case _:
                            pass
                break

        racer_list[0].extend(boat1_result_list)
        racer_list[1].extend(boat2_result_list)
        racer_list[2].extend(boat3_result_list)
        racer_list[3].extend(boat4_result_list)
        racer_list[4].extend(boat5_result_list)
        racer_list[5].extend(boat6_result_list)

        with open(
            os.path.join(os.getcwd(), "temp", f"race_{target_date}.csv"),
            mode="a",
            encoding="UTF-8",
            newline="",
        ) as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    race.id,
                    grade,
                    is_last_day,
                    has_stabilizer,
                    before_info_temperature,
                    before_info_weather,
                    before_info_wind_speed,
                    before_info_wind_direction,
                    before_info_water_temperature,
                    before_info_wave_height,
                    temperature,
                    weather,
                    wind_speed,
                    wind_direction,
                    water_temperature,
                    wave_height,
                    winning_style,
                ]
            )

        with open(
            os.path.join(os.getcwd(), "temp", f"racer_{target_date}.csv"),
            mode="a",
            encoding="UTF-8",
            newline="",
        ) as f:
            writer = csv.writer(f)
            for racer in racer_list:
                writer.writerow(racer)

        # deadline odds
        for retry in range(3):
            try:
                response = requests.get(
                    f"https://www.boatrace.jp/owpc/pc/race/odds3t?rno={race.race_number}&jcd={race.venue:02d}&hd={race.date}",
                    headers=REQUEST_HEADERS,
                    timeout=10,
                )
                response.raise_for_status()
                break
            except requests.RequestException:
                if retry == 2:
                    raise
                time.sleep(5)

        beautifulsoup = BeautifulSoup(response.text, "html.parser")
        soup_list = beautifulsoup.find_all("td", class_="oddsPoint")
        odds_list = []
        odds_list.append(race.id)
        for index, soup in enumerate(soup_list):
            odds = None
            try:
                odds = float(soup.get_text(strip=True))
            except ValueError:
                pass
            odds_list.append(odds)
            if index == 119:
                break
        with open(
            os.path.join(os.getcwd(), "temp", f"deadline_odds_{target_date}.csv"),
            mode="a",
            encoding="UTF-8",
            newline="",
        ) as f:
            writer = csv.writer(f)
            writer.writerow(odds_list)

        time.sleep(1)


def import_scraping_data(target_date: int):
    # race
    with open(os.path.join(os.getcwd(), "temp", f"race_{target_date}.csv"), "r", encoding="UTF-8") as f:
        for row in csv.reader(f):
            race_id = int(row[0])
            race = Session.get(Race, race_id)
            if race is not None:
                race.grade = row[1] if row[1] != "" else None
                race.is_last_day = row[2] if row[2] != "" else None
                race.has_stabilizer = row[3] if row[3] != "" else None
                race.before_info_temperature = float(row[4]) if row[4] != "" else None
                race.before_info_weather = row[5] if row[5] != "" else None
                race.before_info_wind_speed = int(row[6]) if row[6] != "" else None
                race.before_info_wind_direction = int(row[7]) if row[7] != "" else None
                race.before_info_water_temperature = float(row[8]) if row[8] != "" else None
                race.before_info_wave_height = int(row[9]) if row[9] != "" else None
                race.temperature = float(row[10]) if row[10] != "" else None
                race.weather = row[11] if row[11] != "" else None
                race.wind_speed = int(row[12]) if row[12] != "" else None
                race.wind_direction = int(row[13]) if row[13] != "" else None
                race.water_temperature = float(row[14]) if row[14] != "" else None
                race.wave_height = int(row[15]) if row[15] != "" else None
                race.winning_style = row[16] if row[16] != "" else None
    Session.commit()

    # racer
    race_id_list = []
    racer_list = []
    with open(os.path.join(os.getcwd(), "temp", f"racer_{target_date}.csv"), "r", encoding="UTF-8") as f:
        for row in csv.reader(f):
            race_id = int(row[0])
            if race_id not in race_id_list:
                race_id_list.append(race_id)
            boat_number = int(row[1])
            racer = Session.scalars(
                select(Racer).where(Racer.race_id == race_id, Racer.boat_number == boat_number)
            ).one_or_none()
            if racer is not None:
                racer.racer_number = int(row[2])
                racer.racer_class = row[3]
                racer.branch = row[4] if row[4] != "" else None
                racer.hometown = row[5] if row[5] != "" else None
                racer.age = int(row[6])
                racer.weight = float(row[7]) if row[7] != "" else None
                racer.flying = int(row[8])
                racer.late = int(row[9])
                racer.average_start_timing = float(row[10]) if row[10] != "" else None
                racer.all_venue_win_rate = float(row[11]) if row[11] != "" else None
                racer.all_venue_top2_rate = float(row[12]) if row[12] != "" else None
                racer.all_venue_top3_rate = float(row[13]) if row[13] != "" else None
                racer.this_venue_win_rate = float(row[14]) if row[14] != "" else None
                racer.this_venue_top2_rate = float(row[15]) if row[15] != "" else None
                racer.this_venue_top3_rate = float(row[16]) if row[16] != "" else None
                racer.motor_top2_rate = float(row[17]) if row[17] != "" else None
                racer.motor_top3_rate = float(row[18]) if row[18] != "" else None
                racer.boat_top2_rate = float(row[19]) if row[19] != "" else None
                racer.boat_top3_rate = float(row[20]) if row[20] != "" else None
                racer.before_info_course = int(row[21]) if row[21] != "" else None
                racer.before_info_start_timing = float(row[22]) if row[22] != "" else None
                racer.before_info_start_timing_abs = abs(float(row[22])) if row[22] != "" else None
                racer.before_info_weight = float(row[23]) if row[23] != "" else None
                racer.before_info_adjusted_weight = float(row[24]) if row[24] != "" else None
                racer.before_info_display_time = float(row[25]) if row[25] != "" else None
                racer.before_info_tilt = float(row[26]) if row[26] != "" else None
                racer.course = int(row[27]) if row[27] != "" else None
                racer.start_timing = float(row[28]) if row[28] != "" else None
                racer.result = int(row[29]) if row[29] != "" else None
                racer.race_time = float(row[30]) if row[30] != "" else None
            else:
                racer_list.append(
                    Racer(
                        race_id=race_id,
                        boat_number=boat_number,
                        racer_number=int(row[2]),
                        racer_class=row[3],
                        branch=row[4] if row[4] != "" else None,
                        hometown=row[5] if row[5] != "" else None,
                        age=int(row[6]),
                        weight=float(row[7]) if row[7] != "" else None,
                        flying=int(row[8]),
                        late=int(row[9]),
                        average_start_timing=float(row[10]) if row[10] != "" else None,
                        all_venue_win_rate=float(row[11]) if row[11] != "" else None,
                        all_venue_top2_rate=float(row[12]) if row[12] != "" else None,
                        all_venue_top3_rate=float(row[13]) if row[13] != "" else None,
                        this_venue_win_rate=float(row[14]) if row[14] != "" else None,
                        this_venue_top2_rate=float(row[15]) if row[15] != "" else None,
                        this_venue_top3_rate=float(row[16]) if row[16] != "" else None,
                        motor_top2_rate=float(row[17]) if row[17] != "" else None,
                        motor_top3_rate=float(row[18]) if row[18] != "" else None,
                        boat_top2_rate=float(row[19]) if row[19] != "" else None,
                        boat_top3_rate=float(row[20]) if row[20] != "" else None,
                        before_info_course=int(row[21]) if row[21] != "" else None,
                        before_info_start_timing=float(row[22]) if row[22] != "" else None,
                        before_info_start_timing_abs=abs(float(row[22])) if row[22] != "" else None,
                        before_info_weight=float(row[23]) if row[23] != "" else None,
                        before_info_adjusted_weight=float(row[24]) if row[24] != "" else None,
                        before_info_display_time=float(row[25]) if row[25] != "" else None,
                        before_info_tilt=float(row[26]) if row[26] != "" else None,
                        course=int(row[27]) if row[27] != "" else None,
                        start_timing=float(row[28]) if row[28] != "" else None,
                        result=int(row[29]) if row[29] != "" else None,
                        race_time=float(row[30]) if row[30] != "" else None,
                    )
                )
    Session.add_all(racer_list)
    Session.commit()

    for race_id in race_id_list:
        racer_list = Session.scalars(select(Racer).where(Racer.race_id == race_id)).all()

        # average_start_timing
        average_start_timing_list = [
            racer.average_start_timing for racer in racer_list if racer.average_start_timing is not None
        ]
        average_start_timing_mean = numpy.mean(average_start_timing_list) if average_start_timing_list else None
        average_start_timing_std = numpy.std(average_start_timing_list) if average_start_timing_list else None
        # all_venue_win_rate
        all_venue_win_rate_list = [
            racer.all_venue_win_rate for racer in racer_list if racer.all_venue_win_rate is not None
        ]
        all_venue_win_rate_mean = numpy.mean(all_venue_win_rate_list) if all_venue_win_rate_list else None
        all_venue_win_rate_std = numpy.std(all_venue_win_rate_list) if all_venue_win_rate_list else None
        # all_venue_top2_rate
        all_venue_top2_rate_list = [
            racer.all_venue_top2_rate for racer in racer_list if racer.all_venue_top2_rate is not None
        ]
        all_venue_top2_rate_mean = numpy.mean(all_venue_top2_rate_list) if all_venue_top2_rate_list else None
        all_venue_top2_rate_std = numpy.std(all_venue_top2_rate_list) if all_venue_top2_rate_list else None
        # all_venue_top3_rate
        all_venue_top3_rate_list = [
            racer.all_venue_top3_rate for racer in racer_list if racer.all_venue_top3_rate is not None
        ]
        all_venue_top3_rate_mean = numpy.mean(all_venue_top3_rate_list) if all_venue_top3_rate_list else None
        all_venue_top3_rate_std = numpy.std(all_venue_top3_rate_list) if all_venue_top3_rate_list else None
        # this_venue_win_rate
        this_venue_win_rate_list = [
            racer.this_venue_win_rate for racer in racer_list if racer.this_venue_win_rate is not None
        ]
        this_venue_win_rate_mean = numpy.mean(this_venue_win_rate_list) if this_venue_win_rate_list else None
        this_venue_win_rate_std = numpy.std(this_venue_win_rate_list) if this_venue_win_rate_list else None
        # this_venue_top2_rate
        this_venue_top2_rate_list = [
            racer.this_venue_top2_rate for racer in racer_list if racer.this_venue_top2_rate is not None
        ]
        this_venue_top2_rate_mean = numpy.mean(this_venue_top2_rate_list) if this_venue_top2_rate_list else None
        this_venue_top2_rate_std = numpy.std(this_venue_top2_rate_list) if this_venue_top2_rate_list else None
        # this_venue_top3_rate
        this_venue_top3_rate_list = [
            racer.this_venue_top3_rate for racer in racer_list if racer.this_venue_top3_rate is not None
        ]
        this_venue_top3_rate_mean = numpy.mean(this_venue_top3_rate_list) if this_venue_top3_rate_list else None
        this_venue_top3_rate_std = numpy.std(this_venue_top3_rate_list) if this_venue_top3_rate_list else None
        # motor_top2_rate
        motor_top2_rate_list = [racer.motor_top2_rate for racer in racer_list if racer.motor_top2_rate is not None]
        motor_top2_rate_mean = numpy.mean(motor_top2_rate_list) if motor_top2_rate_list else None
        motor_top2_rate_std = numpy.std(motor_top2_rate_list) if motor_top2_rate_list else None
        # motor_top3_rate
        motor_top3_rate_list = [racer.motor_top3_rate for racer in racer_list if racer.motor_top3_rate is not None]
        motor_top3_rate_mean = numpy.mean(motor_top3_rate_list) if motor_top3_rate_list else None
        motor_top3_rate_std = numpy.std(motor_top3_rate_list) if motor_top3_rate_list else None
        # boat_top2_rate
        boat_top2_rate_list = [racer.boat_top2_rate for racer in racer_list if racer.boat_top2_rate is not None]
        boat_top2_rate_mean = numpy.mean(boat_top2_rate_list) if boat_top2_rate_list else None
        boat_top2_rate_std = numpy.std(boat_top2_rate_list) if boat_top2_rate_list else None
        # boat_top3_rate
        boat_top3_rate_list = [racer.boat_top3_rate for racer in racer_list if racer.boat_top3_rate is not None]
        boat_top3_rate_mean = numpy.mean(boat_top3_rate_list) if boat_top3_rate_list else None
        boat_top3_rate_std = numpy.std(boat_top3_rate_list) if boat_top3_rate_list else None
        # before_info_start_timing_abs
        before_info_start_timing_abs_list = [
            racer.before_info_start_timing_abs for racer in racer_list if racer.before_info_start_timing_abs is not None
        ]
        before_info_start_timing_abs_mean = (
            numpy.mean(before_info_start_timing_abs_list) if before_info_start_timing_abs_list else None
        )
        before_info_start_timing_abs_std = (
            numpy.std(before_info_start_timing_abs_list) if before_info_start_timing_abs_list else None
        )
        # before_info_display_time
        before_info_display_time_list = [
            racer.before_info_display_time for racer in racer_list if racer.before_info_display_time is not None
        ]
        before_info_display_time_mean = (
            numpy.mean(before_info_display_time_list) if before_info_display_time_list else None
        )
        before_info_display_time_std = (
            numpy.std(before_info_display_time_list) if before_info_display_time_list else None
        )

        for racer in racer_list:
            # average_start_timing
            if (
                racer.average_start_timing is not None
                and average_start_timing_mean is not None
                and average_start_timing_std is not None
            ):
                racer.average_start_timing_z_score = (
                    (average_start_timing_mean - racer.average_start_timing) / average_start_timing_std
                    if average_start_timing_std > 0
                    else 0.0
                )
            # all_venue_win_rate
            if (
                racer.all_venue_win_rate is not None
                and all_venue_win_rate_mean is not None
                and all_venue_win_rate_std is not None
            ):
                racer.all_venue_win_rate_z_score = (
                    (racer.all_venue_win_rate - all_venue_win_rate_mean) / all_venue_win_rate_std
                    if all_venue_win_rate_std > 0
                    else 0.0
                )
            # all_venue_top2_rate
            if (
                racer.all_venue_top2_rate is not None
                and all_venue_top2_rate_mean is not None
                and all_venue_top2_rate_std is not None
            ):
                racer.all_venue_top2_rate_z_score = (
                    (racer.all_venue_top2_rate - all_venue_top2_rate_mean) / all_venue_top2_rate_std
                    if all_venue_top2_rate_std > 0
                    else 0.0
                )
            # all_venue_top3_rate
            if (
                racer.all_venue_top3_rate is not None
                and all_venue_top3_rate_mean is not None
                and all_venue_top3_rate_std is not None
            ):
                racer.all_venue_top3_rate_z_score = (
                    (racer.all_venue_top3_rate - all_venue_top3_rate_mean) / all_venue_top3_rate_std
                    if all_venue_top3_rate_std > 0
                    else 0.0
                )
            # this_venue_win_rate
            if (
                racer.this_venue_win_rate is not None
                and this_venue_win_rate_mean is not None
                and this_venue_win_rate_std is not None
            ):
                racer.this_venue_win_rate_z_score = (
                    (racer.this_venue_win_rate - this_venue_win_rate_mean) / this_venue_win_rate_std
                    if this_venue_win_rate_std > 0
                    else 0.0
                )
            # this_venue_top2_rate
            if (
                racer.this_venue_top2_rate is not None
                and this_venue_top2_rate_mean is not None
                and this_venue_top2_rate_std is not None
            ):
                racer.this_venue_top2_rate_z_score = (
                    (racer.this_venue_top2_rate - this_venue_top2_rate_mean) / this_venue_top2_rate_std
                    if this_venue_top2_rate_std > 0
                    else 0.0
                )
            # this_venue_top3_rate
            if (
                racer.this_venue_top3_rate is not None
                and this_venue_top3_rate_mean is not None
                and this_venue_top3_rate_std is not None
            ):
                racer.this_venue_top3_rate_z_score = (
                    (racer.this_venue_top3_rate - this_venue_top3_rate_mean) / this_venue_top3_rate_std
                    if this_venue_top3_rate_std > 0
                    else 0.0
                )
            # motor_top2_rate
            if (
                racer.motor_top2_rate is not None
                and motor_top2_rate_mean is not None
                and motor_top2_rate_std is not None
            ):
                racer.motor_top2_rate_z_score = (
                    (racer.motor_top2_rate - motor_top2_rate_mean) / motor_top2_rate_std
                    if motor_top2_rate_std > 0
                    else 0.0
                )
            # motor_top3_rate
            if (
                racer.motor_top3_rate is not None
                and motor_top3_rate_mean is not None
                and motor_top3_rate_std is not None
            ):
                racer.motor_top3_rate_z_score = (
                    (racer.motor_top3_rate - motor_top3_rate_mean) / motor_top3_rate_std
                    if motor_top3_rate_std > 0
                    else 0.0
                )
            # boat_top2_rate
            if racer.boat_top2_rate is not None and boat_top2_rate_mean is not None and boat_top2_rate_std is not None:
                racer.boat_top2_rate_z_score = (
                    (racer.boat_top2_rate - boat_top2_rate_mean) / boat_top2_rate_std if boat_top2_rate_std > 0 else 0.0
                )
            # boat_top3_rate
            if racer.boat_top3_rate is not None and boat_top3_rate_mean is not None and boat_top3_rate_std is not None:
                racer.boat_top3_rate_z_score = (
                    (racer.boat_top3_rate - boat_top3_rate_mean) / boat_top3_rate_std if boat_top3_rate_std > 0 else 0.0
                )
            # before_info_start_timing_abs
            if (
                racer.before_info_start_timing_abs is not None
                and before_info_start_timing_abs_mean is not None
                and before_info_start_timing_abs_std is not None
            ):
                racer.before_info_start_timing_abs_z_score = (
                    (before_info_start_timing_abs_mean - racer.before_info_start_timing_abs)
                    / before_info_start_timing_abs_std
                    if before_info_start_timing_abs_std > 0
                    else 0.0
                )
            # before_info_display_time
            if (
                racer.before_info_display_time is not None
                and before_info_display_time_mean is not None
                and before_info_display_time_std is not None
            ):
                racer.before_info_display_time_z_score = (
                    (before_info_display_time_mean - racer.before_info_display_time) / before_info_display_time_std
                    if before_info_display_time_std > 0
                    else 0.0
                )

    Session.commit()

    # deadline odds
    ticket_list = []
    with open(os.path.join(os.getcwd(), "temp", f"deadline_odds_{target_date}.csv"), "r", encoding="UTF-8") as f:
        for row in csv.reader(f):
            race_id = int(row.pop(0))
            race = Session.get(Race, race_id)
            deadline_odds_list = sorted([float(x) for x in row if x and x != "0.0"])
            sum_deadline_odds_inverse = sum(1.0 / deadline_odds for deadline_odds in deadline_odds_list)
            for index in range(120):
                is_win = (
                    1
                    if race.first == TRIFECTA_LIST[index][0]
                    and race.second == TRIFECTA_LIST[index][1]
                    and race.third == TRIFECTA_LIST[index][2]
                    else 0
                )
                deadline_odds = float(row[index]) if row[index] and row[index] != "0.0" else None
                deadline_odds_market_share = (
                    (1.0 / deadline_odds) / sum_deadline_odds_inverse if deadline_odds is not None else None
                )
                ticket = Session.scalars(
                    select(Ticket).where(
                        Ticket.race_id == race_id,
                        Ticket.first == TRIFECTA_LIST[index][0],
                        Ticket.second == TRIFECTA_LIST[index][1],
                        Ticket.third == TRIFECTA_LIST[index][2],
                    )
                ).one_or_none()
                if ticket is not None:
                    ticket.is_win = is_win
                    ticket.deadline_odds = deadline_odds
                    ticket.deadline_odds_market_share = deadline_odds_market_share
                else:
                    ticket_list.append(
                        Ticket(
                            race_id=race_id,
                            first=TRIFECTA_LIST[index][0],
                            second=TRIFECTA_LIST[index][1],
                            third=TRIFECTA_LIST[index][2],
                            is_win=is_win,
                            deadline_odds=deadline_odds,
                            deadline_odds_market_share=deadline_odds_market_share,
                        )
                    )
    Session.add_all(ticket_list)
    Session.commit()


def calculate_stats(target_date: int):
    race_list = Session.scalars(
        select(Race)
        .options(selectinload(Race.racers))
        .where(
            Race.is_cancel == 0,
            Race.date == target_date,
        )
        .order_by(Race.id.asc())
    ).all()
    for race in race_list:
        for racer in race.racers:
            last5_1st_count = 0
            last5_2nd_count = 0
            last5_3rd_count = 0
            last5_result_list = []
            last5_start_timing_list = []
            last10_1st_count = 0
            last10_2nd_count = 0
            last10_3rd_count = 0
            last10_result_list = []
            last10_start_timing_list = []
            last10_racer_list = Session.scalars(
                select(Racer)
                .where(
                    Racer.race_id < race.id,
                    Racer.racer_number == racer.racer_number,
                    Racer.start_timing.is_not(None),
                    Racer.result.is_not(None),
                )
                .order_by(Racer.race_id.desc())
                .limit(10)
            ).all()
            for index, last10_racer in enumerate(last10_racer_list):
                if last10_racer.result == 1:
                    if index < 5:
                        last5_1st_count += 1
                    last10_1st_count += 1
                elif last10_racer.result == 2:
                    if index < 5:
                        last5_2nd_count += 1
                    last10_2nd_count += 1
                elif last10_racer.result == 3:
                    if index < 5:
                        last5_3rd_count += 1
                    last10_3rd_count += 1
                else:
                    pass
                if index < 5:
                    last5_result_list.append(last10_racer.result)
                last10_result_list.append(last10_racer.result)
                if index < 5:
                    last5_start_timing_list.append(last10_racer.start_timing)
                last10_start_timing_list.append(last10_racer.start_timing)
            if len(last10_racer_list) >= 5:
                racer.last5_1st_rate = round((last5_1st_count / 5) * 100, 2)
                racer.last5_2nd_rate = round((last5_2nd_count / 5) * 100, 2)
                racer.last5_3rd_rate = round((last5_3rd_count / 5) * 100, 2)
                racer.last5_average_rank = numpy.mean(last5_result_list)
                racer.last5_average_start_timing = numpy.mean(last5_start_timing_list)
                racer.last5_start_timing_std = numpy.std(last5_start_timing_list)
            else:
                racer.last5_1st_rate = None
                racer.last5_2nd_rate = None
                racer.last5_3rd_rate = None
                racer.last5_average_rank = None
                racer.last5_average_start_timing = None
                racer.last5_start_timing_std = None
            if len(last10_racer_list) == 10:
                racer.last10_1st_rate = round((last10_1st_count / 10) * 100, 2)
                racer.last10_2nd_rate = round((last10_2nd_count / 10) * 100, 2)
                racer.last10_3rd_rate = round((last10_3rd_count / 10) * 100, 2)
                racer.last10_average_rank = numpy.mean(last10_result_list)
                racer.last10_average_start_timing = numpy.mean(last10_start_timing_list)
                racer.last10_start_timing_std = numpy.std(last10_start_timing_list)
            else:
                racer.last10_1st_rate = None
                racer.last10_2nd_rate = None
                racer.last10_3rd_rate = None
                racer.last10_average_rank = None
                racer.last10_average_start_timing = None
                racer.last10_start_timing_std = None
    Session.commit()


def predict(target_date: int):
    with open(
        os.path.join(os.getcwd(), "temp", f"predict_{target_date}.csv"), mode="w", encoding="UTF-8", newline=""
    ) as f:
        writer = csv.writer(f)
        writer.writerow(CSV_COLUMN_LIST[:-1])
        race_list = Session.scalars(
            select(Race)
            .where(
                Race.is_cancel == 0,
                Race.date == target_date,
                Race.grade.is_not(None),
                Race.venue.is_not(None),
                Race.day_number.is_not(None),
                Race.is_last_day.is_not(None),
                Race.race_number.is_not(None),
                Race.has_stabilizer.is_not(None),
                Race.before_info_temperature.is_not(None),
                Race.before_info_weather.is_not(None),
                Race.before_info_wind_speed.is_not(None),
                Race.before_info_wind_direction.is_not(None),
                Race.before_info_water_temperature.is_not(None),
                Race.before_info_wave_height.is_not(None),
            )
            .order_by(Race.id.asc())
        ).all()
        for race in race_list:
            racer_list = Session.scalars(
                select(Racer)
                .where(
                    Racer.race_id == race.id,
                    Racer.racer_class.is_not(None),
                    Racer.branch.is_not(None),
                    Racer.age.is_not(None),
                    Racer.flying.is_not(None),
                    Racer.late.is_not(None),
                    Racer.average_start_timing.is_not(None),
                    Racer.all_venue_win_rate.is_not(None),
                    Racer.all_venue_top2_rate.is_not(None),
                    Racer.this_venue_win_rate.is_not(None),
                    Racer.this_venue_top2_rate.is_not(None),
                    Racer.motor_top2_rate.is_not(None),
                    Racer.before_info_course.is_not(None),
                    Racer.before_info_start_timing_abs.is_not(None),
                    Racer.before_info_weight.is_not(None),
                    Racer.before_info_adjusted_weight.is_not(None),
                    Racer.before_info_display_time.is_not(None),
                    Racer.before_info_tilt.is_not(None),
                    Racer.last5_1st_rate.is_not(None),
                    Racer.last5_2nd_rate.is_not(None),
                    Racer.last5_3rd_rate.is_not(None),
                    Racer.last5_average_rank.is_not(None),
                    Racer.last5_average_start_timing.is_not(None),
                    Racer.last5_start_timing_std.is_not(None),
                    Racer.last10_1st_rate.is_not(None),
                    Racer.last10_2nd_rate.is_not(None),
                    Racer.last10_3rd_rate.is_not(None),
                    Racer.last10_average_rank.is_not(None),
                    Racer.last10_average_start_timing.is_not(None),
                    Racer.last10_start_timing_std.is_not(None),
                )
                .order_by(Racer.boat_number.asc())
            ).all()
            if (
                len(racer_list) == 6
                and racer_list[0].before_info_course == 1
                and racer_list[1].before_info_course == 2
                and racer_list[2].before_info_course == 3
                and racer_list[3].before_info_course == 4
                and racer_list[4].before_info_course == 5
                and racer_list[5].before_info_course == 6
                and Session.scalar(
                    select(func.count())
                    .select_from(Ticket)
                    .where(
                        Ticket.race_id == race.id,
                        Ticket.deadline_odds.is_not(None),
                        Ticket.deadline_odds_market_share.is_not(None),
                    )
                )
                == 120
            ):
                period = 1 if (race.date // 100) % 100 < 7 else 2
                boat1_period_stat = Session.scalars(
                    select(PeriodStat).where(
                        PeriodStat.racer_number == racer_list[0].racer_number,
                        PeriodStat.year == race.date // 10000,
                        PeriodStat.period == period,
                        PeriodStat.sex.is_not(None),
                        PeriodStat.course1_entry_count > 0,
                        PeriodStat.course1_average_start_timing.is_not(None),
                        PeriodStat.course1_average_start_rank.is_not(None),
                        PeriodStat.course1_1st_count.is_not(None),
                        PeriodStat.course1_2nd_count.is_not(None),
                        PeriodStat.course1_3rd_count.is_not(None),
                    )
                ).one_or_none()
                boat2_period_stat = Session.scalars(
                    select(PeriodStat).where(
                        PeriodStat.racer_number == racer_list[1].racer_number,
                        PeriodStat.year == race.date // 10000,
                        PeriodStat.period == period,
                        PeriodStat.sex.is_not(None),
                        PeriodStat.course2_entry_count > 0,
                        PeriodStat.course2_average_start_timing.is_not(None),
                        PeriodStat.course2_average_start_rank.is_not(None),
                        PeriodStat.course2_1st_count.is_not(None),
                        PeriodStat.course2_2nd_count.is_not(None),
                        PeriodStat.course2_3rd_count.is_not(None),
                    )
                ).one_or_none()
                boat3_period_stat = Session.scalars(
                    select(PeriodStat).where(
                        PeriodStat.racer_number == racer_list[2].racer_number,
                        PeriodStat.year == race.date // 10000,
                        PeriodStat.period == period,
                        PeriodStat.sex.is_not(None),
                        PeriodStat.course3_entry_count > 0,
                        PeriodStat.course3_average_start_timing.is_not(None),
                        PeriodStat.course3_average_start_rank.is_not(None),
                        PeriodStat.course3_1st_count.is_not(None),
                        PeriodStat.course3_2nd_count.is_not(None),
                        PeriodStat.course3_3rd_count.is_not(None),
                    )
                ).one_or_none()
                boat4_period_stat = Session.scalars(
                    select(PeriodStat).where(
                        PeriodStat.racer_number == racer_list[3].racer_number,
                        PeriodStat.year == race.date // 10000,
                        PeriodStat.period == period,
                        PeriodStat.sex.is_not(None),
                        PeriodStat.course4_entry_count > 0,
                        PeriodStat.course4_average_start_timing.is_not(None),
                        PeriodStat.course4_average_start_rank.is_not(None),
                        PeriodStat.course4_1st_count.is_not(None),
                        PeriodStat.course4_2nd_count.is_not(None),
                        PeriodStat.course4_3rd_count.is_not(None),
                    )
                ).one_or_none()
                boat5_period_stat = Session.scalars(
                    select(PeriodStat).where(
                        PeriodStat.racer_number == racer_list[4].racer_number,
                        PeriodStat.year == race.date // 10000,
                        PeriodStat.period == period,
                        PeriodStat.sex.is_not(None),
                        PeriodStat.course5_entry_count > 0,
                        PeriodStat.course5_average_start_timing.is_not(None),
                        PeriodStat.course5_average_start_rank.is_not(None),
                        PeriodStat.course5_1st_count.is_not(None),
                        PeriodStat.course5_2nd_count.is_not(None),
                        PeriodStat.course5_3rd_count.is_not(None),
                    )
                ).one_or_none()
                boat6_period_stat = Session.scalars(
                    select(PeriodStat).where(
                        PeriodStat.racer_number == racer_list[5].racer_number,
                        PeriodStat.year == race.date // 10000,
                        PeriodStat.period == period,
                        PeriodStat.sex.is_not(None),
                        PeriodStat.course6_entry_count > 0,
                        PeriodStat.course6_average_start_timing.is_not(None),
                        PeriodStat.course6_average_start_rank.is_not(None),
                        PeriodStat.course6_1st_count.is_not(None),
                        PeriodStat.course6_2nd_count.is_not(None),
                        PeriodStat.course6_3rd_count.is_not(None),
                    )
                ).one_or_none()
                if (
                    boat1_period_stat is not None
                    and boat2_period_stat is not None
                    and boat3_period_stat is not None
                    and boat4_period_stat is not None
                    and boat5_period_stat is not None
                    and boat6_period_stat is not None
                ):
                    # before_info_wind
                    wind_sin = 0.0
                    wind_cos = 0.0
                    if (
                        race.before_info_wind_speed > 0
                        and race.before_info_wind_direction > 0
                        and race.before_info_wind_direction < 17
                    ):
                        wind_direction_angle_deg = WIND_DIRECTION_ANGLES[race.before_info_wind_direction]
                        wind_direction_angle_rad = numpy.deg2rad(wind_direction_angle_deg)
                        wind_sin = numpy.sin(wind_direction_angle_rad) * race.before_info_wind_speed
                        wind_cos = numpy.cos(wind_direction_angle_rad) * race.before_info_wind_speed

                    # sex
                    sex_list = [
                        boat1_period_stat.sex,
                        boat2_period_stat.sex,
                        boat3_period_stat.sex,
                        boat4_period_stat.sex,
                        boat5_period_stat.sex,
                        boat6_period_stat.sex,
                    ]
                    # course_average_start_timing
                    course_average_start_timing_list = [
                        boat1_period_stat.course1_average_start_timing,
                        boat2_period_stat.course2_average_start_timing,
                        boat3_period_stat.course3_average_start_timing,
                        boat4_period_stat.course4_average_start_timing,
                        boat5_period_stat.course5_average_start_timing,
                        boat6_period_stat.course6_average_start_timing,
                    ]
                    # course_average_start_rank
                    course_average_start_rank_list = [
                        boat1_period_stat.course1_average_start_rank,
                        boat2_period_stat.course2_average_start_rank,
                        boat3_period_stat.course3_average_start_rank,
                        boat4_period_stat.course4_average_start_rank,
                        boat5_period_stat.course5_average_start_rank,
                        boat6_period_stat.course6_average_start_rank,
                    ]
                    # course_1st_rate
                    course_1st_rate_list = [
                        round((boat1_period_stat.course1_1st_count / boat1_period_stat.course1_entry_count) * 100, 2),
                        round((boat2_period_stat.course2_1st_count / boat2_period_stat.course2_entry_count) * 100, 2),
                        round((boat3_period_stat.course3_1st_count / boat3_period_stat.course3_entry_count) * 100, 2),
                        round((boat4_period_stat.course4_1st_count / boat4_period_stat.course4_entry_count) * 100, 2),
                        round((boat5_period_stat.course5_1st_count / boat5_period_stat.course5_entry_count) * 100, 2),
                        round((boat6_period_stat.course6_1st_count / boat6_period_stat.course6_entry_count) * 100, 2),
                    ]
                    # course_2nd_rate
                    course_2nd_rate_list = [
                        round((boat1_period_stat.course1_2nd_count / boat1_period_stat.course1_entry_count) * 100, 2),
                        round((boat2_period_stat.course2_2nd_count / boat2_period_stat.course2_entry_count) * 100, 2),
                        round((boat3_period_stat.course3_2nd_count / boat3_period_stat.course3_entry_count) * 100, 2),
                        round((boat4_period_stat.course4_2nd_count / boat4_period_stat.course4_entry_count) * 100, 2),
                        round((boat5_period_stat.course5_2nd_count / boat5_period_stat.course5_entry_count) * 100, 2),
                        round((boat6_period_stat.course6_2nd_count / boat6_period_stat.course6_entry_count) * 100, 2),
                    ]
                    # course_3rd_rate
                    course_3rd_rate_list = [
                        round((boat1_period_stat.course1_3rd_count / boat1_period_stat.course1_entry_count) * 100, 2),
                        round((boat2_period_stat.course2_3rd_count / boat2_period_stat.course2_entry_count) * 100, 2),
                        round((boat3_period_stat.course3_3rd_count / boat3_period_stat.course3_entry_count) * 100, 2),
                        round((boat4_period_stat.course4_3rd_count / boat4_period_stat.course4_entry_count) * 100, 2),
                        round((boat5_period_stat.course5_3rd_count / boat5_period_stat.course5_entry_count) * 100, 2),
                        round((boat6_period_stat.course6_3rd_count / boat6_period_stat.course6_entry_count) * 100, 2),
                    ]

                    row = []
                    row.append(race.id)
                    row.append(GRADE_LIST.index(race.grade))
                    row.append((race.date // 100) % 100)
                    row.append(datetime.strptime(str(race.date), "%Y%m%d").date().weekday())
                    row.append(race.period_progress_rate)
                    row.append(race.venue)
                    venue_stat = Session.scalars(
                        select(VenueStat).where(
                            VenueStat.venue == race.venue, VenueStat.year == (race.date // 10000) - 1
                        )
                    ).one()
                    row.append(venue_stat.normal_entry_course1_1st_rate)
                    row.append(venue_stat.normal_entry_course1_2nd_rate)
                    row.append(venue_stat.normal_entry_course1_3rd_rate)
                    row.append(venue_stat.normal_entry_course2_1st_rate)
                    row.append(venue_stat.normal_entry_course2_2nd_rate)
                    row.append(venue_stat.normal_entry_course2_3rd_rate)
                    row.append(venue_stat.normal_entry_course3_1st_rate)
                    row.append(venue_stat.normal_entry_course3_2nd_rate)
                    row.append(venue_stat.normal_entry_course3_3rd_rate)
                    row.append(venue_stat.normal_entry_course4_1st_rate)
                    row.append(venue_stat.normal_entry_course4_2nd_rate)
                    row.append(venue_stat.normal_entry_course4_3rd_rate)
                    row.append(venue_stat.normal_entry_course5_1st_rate)
                    row.append(venue_stat.normal_entry_course5_2nd_rate)
                    row.append(venue_stat.normal_entry_course5_3rd_rate)
                    row.append(venue_stat.normal_entry_course6_1st_rate)
                    row.append(venue_stat.normal_entry_course6_2nd_rate)
                    row.append(venue_stat.normal_entry_course6_3rd_rate)
                    row.append(race.day_number)
                    row.append(race.is_last_day)
                    row.append(race.race_number)
                    row.append(race.has_stabilizer)
                    row.append(race.before_info_temperature)
                    row.append(WEATHER_LIST.index(race.before_info_weather))
                    row.append(round(wind_sin, 4))
                    row.append(round(wind_cos, 4))
                    row.append(race.before_info_water_temperature)
                    row.append(race.before_info_wave_height)
                    row.append(race.has_stabilizer * round(wind_sin, 4))
                    row.append(race.has_stabilizer * round(wind_cos, 4))
                    row.append(race.has_stabilizer * race.before_info_wave_height)
                    row.append(sex_list.count(2))

                    for boat_index in range(6):
                        # racer_class
                        row.append(RACER_CLASS_LIST.index(racer_list[boat_index].racer_class))
                        # sex
                        row.append(sex_list[boat_index])
                        # age
                        row.append(racer_list[boat_index].age)
                        # flying_late
                        row.append(racer_list[boat_index].flying + racer_list[boat_index].late)
                        # average_start_timing
                        row.append(racer_list[boat_index].average_start_timing)
                        row.append(racer_list[boat_index].average_start_timing_z_score)
                        # all_venue_win_rate
                        row.append(racer_list[boat_index].all_venue_win_rate)
                        row.append(racer_list[boat_index].all_venue_win_rate_z_score)
                        # all_venue_top2_rate
                        row.append(racer_list[boat_index].all_venue_top2_rate)
                        # this_venue_win_rate
                        row.append(racer_list[boat_index].this_venue_win_rate)
                        row.append(racer_list[boat_index].this_venue_win_rate_z_score)
                        # this_venue_top2_rate
                        row.append(racer_list[boat_index].this_venue_top2_rate)
                        # motor_top2_rate
                        row.append(racer_list[boat_index].motor_top2_rate)
                        row.append(racer_list[boat_index].motor_top2_rate_z_score)
                        # before_info_start_timing
                        row.append(racer_list[boat_index].before_info_start_timing)
                        row.append(racer_list[boat_index].before_info_start_timing_abs_z_score)
                        # before_info_adjusted_weight, before_info_total_weight
                        row.append(racer_list[boat_index].before_info_adjusted_weight)
                        row.append(
                            racer_list[boat_index].before_info_weight
                            + racer_list[boat_index].before_info_adjusted_weight
                        )
                        # before_info_display_time
                        row.append(racer_list[boat_index].before_info_display_time)
                        row.append(racer_list[boat_index].before_info_display_time_z_score)
                        # before_info_tilt
                        row.append(racer_list[boat_index].before_info_tilt)
                        # course_average_start_timing
                        row.append(course_average_start_timing_list[boat_index])
                        # course_average_start_rank
                        row.append(course_average_start_rank_list[boat_index])
                        # course_1st_rate
                        row.append(course_1st_rate_list[boat_index])
                        # course_2nd_rate
                        row.append(course_2nd_rate_list[boat_index])
                        # course_3rd_rate
                        row.append(course_3rd_rate_list[boat_index])
                        # last5_1st_rate
                        row.append(racer_list[boat_index].last5_1st_rate)
                        # last5_2nd_rate
                        row.append(racer_list[boat_index].last5_2nd_rate)
                        # last5_3rd_rate
                        row.append(racer_list[boat_index].last5_3rd_rate)
                        # last5_average_rank
                        row.append(racer_list[boat_index].last5_average_rank)
                        # last5_average_start_timing
                        row.append(racer_list[boat_index].last5_average_start_timing)
                        # last5_start_timing_std
                        row.append(racer_list[boat_index].last5_start_timing_std)
                        # last10_1st_rate
                        row.append(racer_list[boat_index].last10_1st_rate)
                        # last10_2nd_rate
                        row.append(racer_list[boat_index].last10_2nd_rate)
                        # last10_3rd_rate
                        row.append(racer_list[boat_index].last10_3rd_rate)
                        # last10_average_rank
                        row.append(racer_list[boat_index].last10_average_rank)
                        # last10_average_start_timing
                        row.append(racer_list[boat_index].last10_average_start_timing)
                        # last10_start_timing_std
                        row.append(racer_list[boat_index].last10_start_timing_std)

                    # average_start_timing
                    row.append(numpy.std([racer.average_start_timing for racer in racer_list]))
                    average_start_timing_z_score_list = [racer.average_start_timing_z_score for racer in racer_list]
                    row.append(average_start_timing_z_score_list[0] - average_start_timing_z_score_list[1])
                    row.append(average_start_timing_z_score_list[0] - average_start_timing_z_score_list[2])
                    row.append(average_start_timing_z_score_list[0] - average_start_timing_z_score_list[3])
                    row.append(average_start_timing_z_score_list[0] - average_start_timing_z_score_list[4])
                    row.append(average_start_timing_z_score_list[0] - average_start_timing_z_score_list[5])
                    row.append(average_start_timing_z_score_list[1] - average_start_timing_z_score_list[2])
                    row.append(average_start_timing_z_score_list[1] - average_start_timing_z_score_list[3])
                    row.append(average_start_timing_z_score_list[1] - average_start_timing_z_score_list[4])
                    row.append(average_start_timing_z_score_list[1] - average_start_timing_z_score_list[5])
                    row.append(average_start_timing_z_score_list[2] - average_start_timing_z_score_list[3])
                    row.append(average_start_timing_z_score_list[2] - average_start_timing_z_score_list[4])
                    row.append(average_start_timing_z_score_list[2] - average_start_timing_z_score_list[5])
                    row.append(average_start_timing_z_score_list[3] - average_start_timing_z_score_list[4])
                    row.append(average_start_timing_z_score_list[3] - average_start_timing_z_score_list[5])
                    row.append(average_start_timing_z_score_list[4] - average_start_timing_z_score_list[5])
                    boat23456_average_start_timing_z_score_list = [
                        racer_list[1].average_start_timing_z_score,
                        racer_list[2].average_start_timing_z_score,
                        racer_list[3].average_start_timing_z_score,
                        racer_list[4].average_start_timing_z_score,
                        racer_list[5].average_start_timing_z_score,
                    ]
                    row.append(
                        racer_list[0].average_start_timing_z_score
                        - numpy.mean(boat23456_average_start_timing_z_score_list)
                    )

                    # all_venue_win_rate
                    row.append(numpy.std([racer.all_venue_win_rate for racer in racer_list]))
                    all_venue_win_rate_z_score_list = [racer.all_venue_win_rate_z_score for racer in racer_list]
                    row.append(all_venue_win_rate_z_score_list[0] - all_venue_win_rate_z_score_list[1])
                    row.append(all_venue_win_rate_z_score_list[0] - all_venue_win_rate_z_score_list[2])
                    row.append(all_venue_win_rate_z_score_list[0] - all_venue_win_rate_z_score_list[3])
                    row.append(all_venue_win_rate_z_score_list[0] - all_venue_win_rate_z_score_list[4])
                    row.append(all_venue_win_rate_z_score_list[0] - all_venue_win_rate_z_score_list[5])
                    row.append(all_venue_win_rate_z_score_list[1] - all_venue_win_rate_z_score_list[2])
                    row.append(all_venue_win_rate_z_score_list[1] - all_venue_win_rate_z_score_list[3])
                    row.append(all_venue_win_rate_z_score_list[1] - all_venue_win_rate_z_score_list[4])
                    row.append(all_venue_win_rate_z_score_list[1] - all_venue_win_rate_z_score_list[5])
                    row.append(all_venue_win_rate_z_score_list[2] - all_venue_win_rate_z_score_list[3])
                    row.append(all_venue_win_rate_z_score_list[2] - all_venue_win_rate_z_score_list[4])
                    row.append(all_venue_win_rate_z_score_list[2] - all_venue_win_rate_z_score_list[5])
                    row.append(all_venue_win_rate_z_score_list[3] - all_venue_win_rate_z_score_list[4])
                    row.append(all_venue_win_rate_z_score_list[3] - all_venue_win_rate_z_score_list[5])
                    row.append(all_venue_win_rate_z_score_list[4] - all_venue_win_rate_z_score_list[5])
                    boat23456_all_venue_win_rate_z_score_list = [
                        racer_list[1].all_venue_win_rate_z_score,
                        racer_list[2].all_venue_win_rate_z_score,
                        racer_list[3].all_venue_win_rate_z_score,
                        racer_list[4].all_venue_win_rate_z_score,
                        racer_list[5].all_venue_win_rate_z_score,
                    ]
                    row.append(
                        racer_list[0].all_venue_win_rate_z_score - numpy.mean(boat23456_all_venue_win_rate_z_score_list)
                    )

                    # this_venue_win_rate
                    row.append(numpy.std([racer.this_venue_win_rate for racer in racer_list]))
                    this_venue_win_rate_z_score_list = [racer.this_venue_win_rate_z_score for racer in racer_list]
                    row.append(this_venue_win_rate_z_score_list[0] - this_venue_win_rate_z_score_list[1])
                    row.append(this_venue_win_rate_z_score_list[0] - this_venue_win_rate_z_score_list[2])
                    row.append(this_venue_win_rate_z_score_list[0] - this_venue_win_rate_z_score_list[3])
                    row.append(this_venue_win_rate_z_score_list[0] - this_venue_win_rate_z_score_list[4])
                    row.append(this_venue_win_rate_z_score_list[0] - this_venue_win_rate_z_score_list[5])
                    row.append(this_venue_win_rate_z_score_list[1] - this_venue_win_rate_z_score_list[2])
                    row.append(this_venue_win_rate_z_score_list[1] - this_venue_win_rate_z_score_list[3])
                    row.append(this_venue_win_rate_z_score_list[1] - this_venue_win_rate_z_score_list[4])
                    row.append(this_venue_win_rate_z_score_list[1] - this_venue_win_rate_z_score_list[5])
                    row.append(this_venue_win_rate_z_score_list[2] - this_venue_win_rate_z_score_list[3])
                    row.append(this_venue_win_rate_z_score_list[2] - this_venue_win_rate_z_score_list[4])
                    row.append(this_venue_win_rate_z_score_list[2] - this_venue_win_rate_z_score_list[5])
                    row.append(this_venue_win_rate_z_score_list[3] - this_venue_win_rate_z_score_list[4])
                    row.append(this_venue_win_rate_z_score_list[3] - this_venue_win_rate_z_score_list[5])
                    row.append(this_venue_win_rate_z_score_list[4] - this_venue_win_rate_z_score_list[5])
                    boat23456_this_venue_win_rate_z_score_list = [
                        racer_list[1].this_venue_win_rate_z_score,
                        racer_list[2].this_venue_win_rate_z_score,
                        racer_list[3].this_venue_win_rate_z_score,
                        racer_list[4].this_venue_win_rate_z_score,
                        racer_list[5].this_venue_win_rate_z_score,
                    ]
                    row.append(
                        racer_list[0].this_venue_win_rate_z_score
                        - numpy.mean(boat23456_this_venue_win_rate_z_score_list)
                    )

                    # motor_top2_rate
                    row.append(numpy.std([racer.motor_top2_rate for racer in racer_list]))
                    motor_top2_rate_z_score_list = [racer.motor_top2_rate_z_score for racer in racer_list]
                    row.append(motor_top2_rate_z_score_list[0] - motor_top2_rate_z_score_list[1])
                    row.append(motor_top2_rate_z_score_list[0] - motor_top2_rate_z_score_list[2])
                    row.append(motor_top2_rate_z_score_list[0] - motor_top2_rate_z_score_list[3])
                    row.append(motor_top2_rate_z_score_list[0] - motor_top2_rate_z_score_list[4])
                    row.append(motor_top2_rate_z_score_list[0] - motor_top2_rate_z_score_list[5])
                    row.append(motor_top2_rate_z_score_list[1] - motor_top2_rate_z_score_list[2])
                    row.append(motor_top2_rate_z_score_list[1] - motor_top2_rate_z_score_list[3])
                    row.append(motor_top2_rate_z_score_list[1] - motor_top2_rate_z_score_list[4])
                    row.append(motor_top2_rate_z_score_list[1] - motor_top2_rate_z_score_list[5])
                    row.append(motor_top2_rate_z_score_list[2] - motor_top2_rate_z_score_list[3])
                    row.append(motor_top2_rate_z_score_list[2] - motor_top2_rate_z_score_list[4])
                    row.append(motor_top2_rate_z_score_list[2] - motor_top2_rate_z_score_list[5])
                    row.append(motor_top2_rate_z_score_list[3] - motor_top2_rate_z_score_list[4])
                    row.append(motor_top2_rate_z_score_list[3] - motor_top2_rate_z_score_list[5])
                    row.append(motor_top2_rate_z_score_list[4] - motor_top2_rate_z_score_list[5])
                    boat23456_motor_top2_rate_z_score_list = [
                        racer_list[1].motor_top2_rate_z_score,
                        racer_list[2].motor_top2_rate_z_score,
                        racer_list[3].motor_top2_rate_z_score,
                        racer_list[4].motor_top2_rate_z_score,
                        racer_list[5].motor_top2_rate_z_score,
                    ]
                    row.append(
                        racer_list[0].motor_top2_rate_z_score - numpy.mean(boat23456_motor_top2_rate_z_score_list)
                    )

                    # before_info_start_timing
                    row.append(numpy.std([racer.before_info_start_timing_abs for racer in racer_list]))
                    before_info_start_timing_abs_z_score_list = [
                        racer.before_info_start_timing_abs_z_score for racer in racer_list
                    ]
                    row.append(
                        before_info_start_timing_abs_z_score_list[0] - before_info_start_timing_abs_z_score_list[1]
                    )
                    row.append(
                        before_info_start_timing_abs_z_score_list[0] - before_info_start_timing_abs_z_score_list[2]
                    )
                    row.append(
                        before_info_start_timing_abs_z_score_list[0] - before_info_start_timing_abs_z_score_list[3]
                    )
                    row.append(
                        before_info_start_timing_abs_z_score_list[0] - before_info_start_timing_abs_z_score_list[4]
                    )
                    row.append(
                        before_info_start_timing_abs_z_score_list[0] - before_info_start_timing_abs_z_score_list[5]
                    )
                    row.append(
                        before_info_start_timing_abs_z_score_list[1] - before_info_start_timing_abs_z_score_list[2]
                    )
                    row.append(
                        before_info_start_timing_abs_z_score_list[1] - before_info_start_timing_abs_z_score_list[3]
                    )
                    row.append(
                        before_info_start_timing_abs_z_score_list[1] - before_info_start_timing_abs_z_score_list[4]
                    )
                    row.append(
                        before_info_start_timing_abs_z_score_list[1] - before_info_start_timing_abs_z_score_list[5]
                    )
                    row.append(
                        before_info_start_timing_abs_z_score_list[2] - before_info_start_timing_abs_z_score_list[3]
                    )
                    row.append(
                        before_info_start_timing_abs_z_score_list[2] - before_info_start_timing_abs_z_score_list[4]
                    )
                    row.append(
                        before_info_start_timing_abs_z_score_list[2] - before_info_start_timing_abs_z_score_list[5]
                    )
                    row.append(
                        before_info_start_timing_abs_z_score_list[3] - before_info_start_timing_abs_z_score_list[4]
                    )
                    row.append(
                        before_info_start_timing_abs_z_score_list[3] - before_info_start_timing_abs_z_score_list[5]
                    )
                    row.append(
                        before_info_start_timing_abs_z_score_list[4] - before_info_start_timing_abs_z_score_list[5]
                    )
                    boat23456_before_info_start_timing_abs_z_score_list = [
                        racer_list[1].before_info_start_timing_abs_z_score,
                        racer_list[2].before_info_start_timing_abs_z_score,
                        racer_list[3].before_info_start_timing_abs_z_score,
                        racer_list[4].before_info_start_timing_abs_z_score,
                        racer_list[5].before_info_start_timing_abs_z_score,
                    ]
                    row.append(
                        racer_list[0].before_info_start_timing_abs_z_score
                        - numpy.mean(boat23456_before_info_start_timing_abs_z_score_list)
                    )

                    # before_info_display_time
                    row.append(numpy.std([racer.before_info_display_time for racer in racer_list]))
                    before_info_display_time_z_score_list = [
                        racer.before_info_display_time_z_score for racer in racer_list
                    ]
                    row.append(before_info_display_time_z_score_list[0] - before_info_display_time_z_score_list[1])
                    row.append(before_info_display_time_z_score_list[0] - before_info_display_time_z_score_list[2])
                    row.append(before_info_display_time_z_score_list[0] - before_info_display_time_z_score_list[3])
                    row.append(before_info_display_time_z_score_list[0] - before_info_display_time_z_score_list[4])
                    row.append(before_info_display_time_z_score_list[0] - before_info_display_time_z_score_list[5])
                    row.append(before_info_display_time_z_score_list[1] - before_info_display_time_z_score_list[2])
                    row.append(before_info_display_time_z_score_list[1] - before_info_display_time_z_score_list[3])
                    row.append(before_info_display_time_z_score_list[1] - before_info_display_time_z_score_list[4])
                    row.append(before_info_display_time_z_score_list[1] - before_info_display_time_z_score_list[5])
                    row.append(before_info_display_time_z_score_list[2] - before_info_display_time_z_score_list[3])
                    row.append(before_info_display_time_z_score_list[2] - before_info_display_time_z_score_list[4])
                    row.append(before_info_display_time_z_score_list[2] - before_info_display_time_z_score_list[5])
                    row.append(before_info_display_time_z_score_list[3] - before_info_display_time_z_score_list[4])
                    row.append(before_info_display_time_z_score_list[3] - before_info_display_time_z_score_list[5])
                    row.append(before_info_display_time_z_score_list[4] - before_info_display_time_z_score_list[5])
                    boat23456_before_info_display_time_z_score_list = [
                        racer_list[1].before_info_display_time_z_score,
                        racer_list[2].before_info_display_time_z_score,
                        racer_list[3].before_info_display_time_z_score,
                        racer_list[4].before_info_display_time_z_score,
                        racer_list[5].before_info_display_time_z_score,
                    ]
                    row.append(
                        racer_list[0].before_info_display_time_z_score
                        - numpy.mean(boat23456_before_info_display_time_z_score_list)
                    )

                    # course_1st_rate
                    row.append(round(course_1st_rate_list[0] - course_1st_rate_list[1], 2))
                    row.append(round(course_1st_rate_list[0] - course_1st_rate_list[2], 2))
                    row.append(round(course_1st_rate_list[0] - course_1st_rate_list[3], 2))
                    row.append(round(course_1st_rate_list[0] - course_1st_rate_list[4], 2))
                    row.append(round(course_1st_rate_list[0] - course_1st_rate_list[5], 2))
                    row.append(round(course_1st_rate_list[1] - course_1st_rate_list[2], 2))
                    row.append(round(course_1st_rate_list[1] - course_1st_rate_list[3], 2))
                    row.append(round(course_1st_rate_list[1] - course_1st_rate_list[4], 2))
                    row.append(round(course_1st_rate_list[1] - course_1st_rate_list[5], 2))
                    row.append(round(course_1st_rate_list[2] - course_1st_rate_list[3], 2))
                    row.append(round(course_1st_rate_list[2] - course_1st_rate_list[4], 2))
                    row.append(round(course_1st_rate_list[2] - course_1st_rate_list[5], 2))
                    row.append(round(course_1st_rate_list[3] - course_1st_rate_list[4], 2))
                    row.append(round(course_1st_rate_list[3] - course_1st_rate_list[5], 2))
                    row.append(round(course_1st_rate_list[4] - course_1st_rate_list[5], 2))

                    # course_2nd_rate
                    row.append(round(course_2nd_rate_list[0] - course_2nd_rate_list[1], 2))
                    row.append(round(course_2nd_rate_list[0] - course_2nd_rate_list[2], 2))
                    row.append(round(course_2nd_rate_list[0] - course_2nd_rate_list[3], 2))
                    row.append(round(course_2nd_rate_list[0] - course_2nd_rate_list[4], 2))
                    row.append(round(course_2nd_rate_list[0] - course_2nd_rate_list[5], 2))
                    row.append(round(course_2nd_rate_list[1] - course_2nd_rate_list[2], 2))
                    row.append(round(course_2nd_rate_list[1] - course_2nd_rate_list[3], 2))
                    row.append(round(course_2nd_rate_list[1] - course_2nd_rate_list[4], 2))
                    row.append(round(course_2nd_rate_list[1] - course_2nd_rate_list[5], 2))
                    row.append(round(course_2nd_rate_list[2] - course_2nd_rate_list[3], 2))
                    row.append(round(course_2nd_rate_list[2] - course_2nd_rate_list[4], 2))
                    row.append(round(course_2nd_rate_list[2] - course_2nd_rate_list[5], 2))
                    row.append(round(course_2nd_rate_list[3] - course_2nd_rate_list[4], 2))
                    row.append(round(course_2nd_rate_list[3] - course_2nd_rate_list[5], 2))
                    row.append(round(course_2nd_rate_list[4] - course_2nd_rate_list[5], 2))

                    # course_3rd_rate
                    row.append(round(course_3rd_rate_list[0] - course_3rd_rate_list[1], 2))
                    row.append(round(course_3rd_rate_list[0] - course_3rd_rate_list[2], 2))
                    row.append(round(course_3rd_rate_list[0] - course_3rd_rate_list[3], 2))
                    row.append(round(course_3rd_rate_list[0] - course_3rd_rate_list[4], 2))
                    row.append(round(course_3rd_rate_list[0] - course_3rd_rate_list[5], 2))
                    row.append(round(course_3rd_rate_list[1] - course_3rd_rate_list[2], 2))
                    row.append(round(course_3rd_rate_list[1] - course_3rd_rate_list[3], 2))
                    row.append(round(course_3rd_rate_list[1] - course_3rd_rate_list[4], 2))
                    row.append(round(course_3rd_rate_list[1] - course_3rd_rate_list[5], 2))
                    row.append(round(course_3rd_rate_list[2] - course_3rd_rate_list[3], 2))
                    row.append(round(course_3rd_rate_list[2] - course_3rd_rate_list[4], 2))
                    row.append(round(course_3rd_rate_list[2] - course_3rd_rate_list[5], 2))
                    row.append(round(course_3rd_rate_list[3] - course_3rd_rate_list[4], 2))
                    row.append(round(course_3rd_rate_list[3] - course_3rd_rate_list[5], 2))
                    row.append(round(course_3rd_rate_list[4] - course_3rd_rate_list[5], 2))
                    writer.writerow(row)

    if os.path.exists(os.path.join(os.getcwd(), "temp", f"predict_{target_date}.csv")):
        predict_df = pandas.read_csv(os.path.join(os.getcwd(), "temp", f"predict_{target_date}.csv"), index_col=0)

        deltas_list = []
        for seed in range(SEED_COUNT):
            model = lightgbm.Booster(
                model_file=os.path.join(os.getcwd(), "models", f"{target_date // 10000}_{seed + 1:02d}.txt")
            )
            deltas = model.predict(predict_df, raw_score=True)
            deltas_list.append(deltas)

        for race_index, race_id in enumerate(predict_df.index):
            ticket_list = Session.scalars(
                select(Ticket).where(
                    Ticket.race_id == race_id,
                    Ticket.deadline_odds.is_not(None),
                    Ticket.deadline_odds_market_share.is_not(None),
                )
            ).all()

            ticket_by_trifecta = {(ticket.first, ticket.second, ticket.third): ticket for ticket in ticket_list}

            sum_exp_score = 0.0
            for trifecta_index, trifecta in enumerate(TRIFECTA_LIST):
                ticket = ticket_by_trifecta[trifecta]
                ticket.delta = statistics.mean(deltas[race_index][trifecta_index] for deltas in deltas_list)
                sum_exp_score += ticket.deadline_odds_market_share * math.exp(ticket.delta)
                # sum_exp_score += math.exp(math.log(ticket.deadline_odds_market_share) + ticket.delta)

            for trifecta in TRIFECTA_LIST:
                ticket = ticket_by_trifecta[trifecta]
                ticket.deadline_odds_probability = (
                    ticket.deadline_odds_market_share * math.exp(ticket.delta)
                ) / sum_exp_score
                ticket.deadline_odds_expected_value = ticket.deadline_odds_probability * ticket.deadline_odds

        Session.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("start_date", type=int)
    parser.add_argument("end_date", type=int)
    parser.add_argument("--predict", action="store_true")
    args = parser.parse_args()

    try:
        start_date = datetime.strptime(str(args.start_date), "%Y%m%d")
        end_date = datetime.strptime(str(args.end_date), "%Y%m%d")
    except ValueError:
        print("ERROR")
        return

    if start_date > end_date:
        print("ERROR")
        return

    current_date = start_date

    while current_date <= end_date:
        target_date = int(current_date.strftime("%Y%m%d"))

        download("https://www1.mbrace.or.jp/od2/B/dindex.html", target_date)
        download("https://www1.mbrace.or.jp/od2/K/dindex.html", target_date)

        if os.path.exists(os.path.join(os.getcwd(), "temp", f"B{target_date % 1000000}.lzh")):
            decompress(f"B{target_date % 1000000}.lzh")
        if os.path.exists(os.path.join(os.getcwd(), "temp", f"K{target_date % 1000000}.lzh")):
            decompress(f"K{target_date % 1000000}.lzh")

        import_official_data(target_date)

        scrape(target_date)
        import_scraping_data(target_date)

        calculate_stats(target_date)

        if args.predict:
            predict(target_date)

        current_date += timedelta(days=1)


if __name__ == "__main__":
    main()
