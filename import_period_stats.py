import os

from tqdm import tqdm

from constants import SESSION
from models import PeriodStat


def main():
    period_stats_list = []
    period_stats_directory_path = os.path.join(os.getcwd(), "official_data", "period_stats")
    for file in tqdm(os.listdir(period_stats_directory_path)):
        if file.startswith("fan") and (file.endswith(".txt") or file.endswith(".TXT")):
            with open(os.path.join(period_stats_directory_path, file), "r", encoding="CP932") as f:
                for line in f:
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
