import os
import re
from datetime import date

from tqdm import tqdm

from constants import SESSION
from models import Race


def main():
    # race
    race_list = []
    race_directory_path = os.path.join(os.getcwd(), "official_data", "race")
    for file in tqdm(os.listdir(race_directory_path)):
        if file.startswith("B") and (file.endswith(".txt") or file.endswith(".TXT")):
            with open(os.path.join(race_directory_path, file), "r", encoding="CP932") as f:
                venue = None
                day_number = None
                date_ = f'20{file.split(".")[0][1:]}'
                if 5 <= int(date_[4:6]) <= 10:
                    period_start = date(int(date_[:4]), 5, 1)
                    period_end = date(int(date_[:4]), 10, 31)
                else:
                    period_start = date(int(date_[:4]) - 1, 11, 1)
                    period_end = date(int(date_[:4]), 4, 30)
                period_progress_rate = round(
                    (
                        (date(int(date_[:4]), int(date_[4:6]), int(date_[6:8])) - period_start).days
                        / (period_end - period_start).days
                    )
                    * 100,
                    2,
                )
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
                        race_id = int(f"{date_}{venue}{str(race_number).zfill(2)}")
                        race = SESSION.query(Race).filter(Race.id == race_id).one_or_none()
                        if race is not None:
                            race.date = int(date_)
                            race.period_progress_rate = period_progress_rate
                            race.venue = int(venue)
                            race.race_number = race_number
                            race.deadline = f"{str(hour).zfill(2)}:{str(minute).zfill(2)}"
                            race.day_number = day_number
                        else:
                            race_list.append(
                                Race(
                                    id=race_id,
                                    date=int(date_),
                                    period_progress_rate=period_progress_rate,
                                    venue=int(venue),
                                    race_number=race_number,
                                    deadline=f"{str(hour).zfill(2)}:{str(minute).zfill(2)}",
                                    day_number=day_number,
                                )
                            )
    SESSION.add_all(race_list)
    SESSION.commit()

    # result
    result_directory_path = os.path.join(os.getcwd(), "official_data", "result")
    for file in tqdm(os.listdir(result_directory_path)):
        if file.startswith("K") and (file.endswith(".txt") or file.endswith(".TXT")):
            with open(os.path.join(result_directory_path, file), "r", encoding="CP932") as f:
                date_ = int(f'20{file.split(".")[0][1:]}')
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
                        race_id = int(f"{date_}{venue}{str(race_number).zfill(2)}")
                        race = SESSION.query(Race).filter(Race.id == race_id).one_or_none()
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
                                elif re.match(r"^[1-6]{1}-[1-6]{1}$", words[3]) and re.match(
                                    r"^[1-6]{1}-[1-6]{1}$", words[5]
                                ):
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
                                if re.match(r"^[1-6]{1}-[1-6]{1}$", words[1]) and re.match(
                                    r"^[1-6]{1}-[1-6]{1}$", words[3]
                                ):
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
    SESSION.commit()


if __name__ == "__main__":
    main()
