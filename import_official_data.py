import os
import re
from datetime import date

from tqdm import tqdm

from constants import SESSION
from models import PeriodStat, Race


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
                    start = date(int(date_[:4]), 5, 1)
                    end = date(int(date_[:4]), 10, 31)
                else:
                    start = date(int(date_[:4]) - 1, 11, 1)
                    end = date(int(date_[:4]), 4, 30)
                period_progress_rate = round(
                    ((date(int(date_[:4]), int(date_[4:6]), int(date_[6:8])) - start).days / (end - start).days) * 100,
                    2,
                )
                for line in f.readlines():
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
                for line in f.readlines():
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
                                elif re.match(r"^[1-6]{1}-[1-6]{1}-[1-6]{1}$", words[1]) and re.match(r"^[1-6]{1}-[1-6]{1}$", words[4]):
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
    SESSION.commit()

    # period stats
    period_stats_list = []
    period_stats_directory_path = os.path.join(os.getcwd(), "official_data", "period_stats")
    for file in tqdm(os.listdir(period_stats_directory_path)):
        if file.startswith("fan") and (file.endswith(".txt") or file.endswith(".TXT")):
            with open(os.path.join(period_stats_directory_path, file), "r", encoding="CP932") as f:
                for line in f.readlines():
                    if line == "\n":
                        continue
                    racer_number = line[0:4]
                    year = line[164:168]
                    period = line[168:169]
                    period_stat = (
                        SESSION.query(PeriodStat)
                        .filter(
                            PeriodStat.racer_number == racer_number,
                            PeriodStat.year == year,
                            PeriodStat.period == period,
                        )
                        .one_or_none()
                    )
                    if period_stat is not None:
                        period_stat.sex = int(line[38:39])
                        period_stat.course1_entry_count = int(line[72:75])
                        period_stat.course1_top2_rate = round(int(line[75:79]) / 10, 1)
                        period_stat.course1_average_start_timing = round(int(line[79:82]) / 100, 2)
                        period_stat.course1_average_start_rank = round(int(line[82:85]) / 100, 2)
                        period_stat.course1_1st_count = int(line[188:191])
                        period_stat.course1_2nd_count = int(line[191:194])
                        period_stat.course1_3rd_count = int(line[194:197])
                        period_stat.course2_entry_count = int(line[85:88])
                        period_stat.course2_top2_rate = round(int(line[88:92]) / 10, 1)
                        period_stat.course2_average_start_timing = round(int(line[92:95]) / 100, 2)
                        period_stat.course2_average_start_rank = round(int(line[95:98]) / 100, 2)
                        period_stat.course2_1st_count = int(line[222:225])
                        period_stat.course2_2nd_count = int(line[225:228])
                        period_stat.course2_3rd_count = int(line[228:231])
                        period_stat.course3_entry_count = int(line[98:101])
                        period_stat.course3_top2_rate = round(int(line[101:105]) / 10, 1)
                        period_stat.course3_average_start_timing = round(int(line[105:108]) / 100, 2)
                        period_stat.course3_average_start_rank = round(int(line[108:111]) / 100, 2)
                        period_stat.course3_1st_count = int(line[256:259])
                        period_stat.course3_2nd_count = int(line[259:262])
                        period_stat.course3_3rd_count = int(line[262:265])
                        period_stat.course4_entry_count = int(line[111:114])
                        period_stat.course4_top2_rate = round(int(line[114:118]) / 10, 1)
                        period_stat.course4_average_start_timing = round(int(line[118:121]) / 100, 2)
                        period_stat.course4_average_start_rank = round(int(line[121:124]) / 100, 2)
                        period_stat.course4_1st_count = int(line[290:293])
                        period_stat.course4_2nd_count = int(line[293:296])
                        period_stat.course4_3rd_count = int(line[296:299])
                        period_stat.course5_entry_count = int(line[124:127])
                        period_stat.course5_top2_rate = round(int(line[127:131]) / 10, 1)
                        period_stat.course5_average_start_timing = round(int(line[131:134]) / 100, 2)
                        period_stat.course5_average_start_rank = round(int(line[134:137]) / 100, 2)
                        period_stat.course5_1st_count = int(line[324:327])
                        period_stat.course5_2nd_count = int(line[327:330])
                        period_stat.course5_3rd_count = int(line[330:333])
                        period_stat.course6_entry_count = int(line[137:140])
                        period_stat.course6_top2_rate = round(int(line[140:144]) / 10, 1)
                        period_stat.course6_average_start_timing = round(int(line[144:147]) / 100, 2)
                        period_stat.course6_average_start_rank = round(int(line[147:150]) / 100, 2)
                        period_stat.course6_1st_count = int(line[358:361])
                        period_stat.course6_2nd_count = int(line[361:364])
                        period_stat.course6_3rd_count = int(line[364:367])
                    else:
                        period_stats_list.append(
                            PeriodStat(
                                racer_number=racer_number,
                                year=year,
                                period=period,
                                sex=int(line[38:39]),
                                course1_entry_count=int(line[72:75]),
                                course1_top2_rate=round(int(line[75:79]) / 10, 1),
                                course1_average_start_timing=round(int(line[79:82]) / 100, 2),
                                course1_average_start_rank=round(int(line[82:85]) / 100, 2),
                                course1_1st_count=int(line[188:191]),
                                course1_2nd_count=int(line[191:194]),
                                course1_3rd_count=int(line[194:197]),
                                course2_entry_count=int(line[85:88]),
                                course2_top2_rate=round(int(line[88:92]) / 10, 1),
                                course2_average_start_timing=round(int(line[92:95]) / 100, 2),
                                course2_average_start_rank=round(int(line[95:98]) / 100, 2),
                                course2_1st_count=int(line[222:225]),
                                course2_2nd_count=int(line[225:228]),
                                course2_3rd_count=int(line[228:231]),
                                course3_entry_count=int(line[98:101]),
                                course3_top2_rate=round(int(line[101:105]) / 10, 1),
                                course3_average_start_timing=round(int(line[105:108]) / 100, 2),
                                course3_average_start_rank=round(int(line[108:111]) / 100, 2),
                                course3_1st_count=int(line[256:259]),
                                course3_2nd_count=int(line[259:262]),
                                course3_3rd_count=int(line[262:265]),
                                course4_entry_count=int(line[111:114]),
                                course4_top2_rate=round(int(line[114:118]) / 10, 1),
                                course4_average_start_timing=round(int(line[118:121]) / 100, 2),
                                course4_average_start_rank=round(int(line[121:124]) / 100, 2),
                                course4_1st_count=int(line[290:293]),
                                course4_2nd_count=int(line[293:296]),
                                course4_3rd_count=int(line[296:299]),
                                course5_entry_count=int(line[124:127]),
                                course5_top2_rate=round(int(line[127:131]) / 10, 1),
                                course5_average_start_timing=round(int(line[131:134]) / 100, 2),
                                course5_average_start_rank=round(int(line[134:137]) / 100, 2),
                                course5_1st_count=int(line[324:327]),
                                course5_2nd_count=int(line[327:330]),
                                course5_3rd_count=int(line[330:333]),
                                course6_entry_count=int(line[137:140]),
                                course6_top2_rate=round(int(line[140:144]) / 10, 1),
                                course6_average_start_timing=round(int(line[144:147]) / 100, 2),
                                course6_average_start_rank=round(int(line[147:150]) / 100, 2),
                                course6_1st_count=int(line[358:361]),
                                course6_2nd_count=int(line[361:364]),
                                course6_3rd_count=int(line[364:367]),
                            )
                        )
    SESSION.add_all(period_stats_list)
    SESSION.commit()


if __name__ == "__main__":
    main()
