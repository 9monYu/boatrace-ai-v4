import argparse
import csv
import os
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from constants import SESSION
from models import Race


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("start", type=int)
    parser.add_argument("end", type=int)
    args = parser.parse_args()

    try:
        datetime.strptime(str(args.start), "%Y%m%d")
        datetime.strptime(str(args.end), "%Y%m%d")
    except ValueError:
        return

    race_list = (
        SESSION.query(Race)
        .filter(
            Race.is_cancel == 0,
            Race.date >= args.start,
            Race.date <= args.end,
        )
        .order_by(Race.id.asc())
        .all()
    )
    for race_index, race in enumerate(race_list):
        if race_index == 0 or race.date != race_list[race_index - 1].date:
            print(f"[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {race.date}")

        racer_list = [
            [],
            [],
            [],
            [],
            [],
            [],
        ]

        # race and racer
        url = f"https://www.boatrace.jp/owpc/pc/race/racelist?rno={race.race_number}&jcd={race.venue:02d}&hd={race.date}"
        try:
            response = requests.get(url)
        except Exception:
            response = requests.get(url)
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

        is_last_day = 0
        if beautifulsoup.find("li", class_="is-active2").find("span", class_="tab2_inner").find("span").get_text(strip=True) == "最終日":
            is_last_day = 1

        has_stabilizer = 0
        if beautifulsoup.find("div", class_="title16_titleLabels__add2020").find("span", class_="label2 is-type1") is not None:
            has_stabilizer = 1

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
        url = f"https://www.boatrace.jp/owpc/pc/race/beforeinfo?rno={race.race_number}&jcd={race.venue:02d}&hd={race.date}"
        try:
            response = requests.get(url)
        except Exception:
            response = requests.get(url)
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
        #  temperature
        try:
            before_info_temperature = float(soup_list[0].find("span", class_="weather1_bodyUnitLabelData").get_text(strip=True).replace("℃", ""))
        except Exception:
            pass
        # weather
        try:
            before_info_weather = soup_list[1].find("span", class_="weather1_bodyUnitLabelTitle").get_text(strip=True)
        except Exception:
            pass
        # wind speed
        try:
            before_info_wind_speed = int(soup_list[2].find("span", class_="weather1_bodyUnitLabelData").get_text(strip=True).replace("m", ""))
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
            before_info_water_temperature = float(soup_list[4].find("span", class_="weather1_bodyUnitLabelData").get_text(strip=True).replace("℃", ""))
        except Exception:
            pass
        # wave height
        try:
            before_info_wave_height = int(soup_list[5].find("span", class_="weather1_bodyUnitLabelData").get_text(strip=True).replace("cm", ""))
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
        url = f"https://www.boatrace.jp/owpc/pc/race/raceresult?rno={race.race_number}&jcd={race.venue:02d}&hd={race.date}"
        try:
            response = requests.get(url)
        except Exception:
            response = requests.get(url)
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
        #  temperature
        try:
            temperature = float(soup_list[0].find("span", class_="weather1_bodyUnitLabelData").get_text(strip=True).replace("℃", ""))
        except Exception:
            pass
        # weather
        try:
            weather = soup_list[1].find("span", class_="weather1_bodyUnitLabelTitle").get_text(strip=True)
        except Exception:
            pass
        # wind speed
        try:
            wind_speed = int(soup_list[2].find("span", class_="weather1_bodyUnitLabelData").get_text(strip=True).replace("m", ""))
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
            water_temperature = float(soup_list[4].find("span", class_="weather1_bodyUnitLabelData").get_text(strip=True).replace("℃", ""))
        except Exception:
            pass
        # wave height
        try:
            wave_height = int(soup_list[5].find("span", class_="weather1_bodyUnitLabelData").get_text(strip=True).replace("cm", ""))
        except Exception:
            pass

        # winning style
        try:
            winning_style = beautifulsoup.find("table", class_="is-h108__3rdadd").find("td", class_="is-fs16").get_text(strip=True)
        except Exception:
            pass

        # course
        # start timing
        for course, soup in enumerate(beautifulsoup.find("table", class_="is-h292__3rdadd").find("tbody").find_all("tr"), start=1):
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
                        result = int(td_list[0].get_text(strip=True))
                    except Exception:
                        pass
                    race_time = None
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
            os.path.join(os.getcwd(), "scraping_data", "race", f"race_{race.date // 100}.csv"),
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
            os.path.join(os.getcwd(), "scraping_data", "racer", f"racer_{race.date // 100}.csv"),
            mode="a",
            encoding="UTF-8",
            newline="",
        ) as f:
            writer = csv.writer(f)
            for racer in racer_list:
                writer.writerow(racer)

        # deadline odds
        url = f"https://www.boatrace.jp/owpc/pc/race/odds3t?rno={race.race_number}&jcd={race.venue:02d}&hd={race.date}"
        try:
            response = requests.get(url)
        except Exception:
            response = requests.get(url)
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
            os.path.join(os.getcwd(), "scraping_data", "deadline_odds", f"deadline_odds_{race.date // 100}.csv"),
            mode="a",
            encoding="UTF-8",
            newline="",
        ) as f:
            writer = csv.writer(f)
            writer.writerow(odds_list)


if __name__ == "__main__":
    main()
