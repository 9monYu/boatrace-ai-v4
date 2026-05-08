from datetime import date

import numpy
from tqdm import tqdm

from constants import SESSION
from models import Race, Racer, VenueStat


def main():
    oldest_race = SESSION.query(Race).order_by(Race.id.asc()).first()

    # venue
    print("venue")
    for year in tqdm(range(oldest_race.date // 10000, date.today().year + 1)):
        venue_stat_list = []
        for venue in range(1, 25):
            normal_entry_race_count = 0
            normal_entry_course1_1st_count = 0
            normal_entry_course1_2nd_count = 0
            normal_entry_course1_3rd_count = 0
            normal_entry_course2_1st_count = 0
            normal_entry_course2_2nd_count = 0
            normal_entry_course2_3rd_count = 0
            normal_entry_course3_1st_count = 0
            normal_entry_course3_2nd_count = 0
            normal_entry_course3_3rd_count = 0
            normal_entry_course4_1st_count = 0
            normal_entry_course4_2nd_count = 0
            normal_entry_course4_3rd_count = 0
            normal_entry_course5_1st_count = 0
            normal_entry_course5_2nd_count = 0
            normal_entry_course5_3rd_count = 0
            normal_entry_course6_1st_count = 0
            normal_entry_course6_2nd_count = 0
            normal_entry_course6_3rd_count = 0
            race_list = (
                SESSION.query(Race)
                .filter(
                    Race.date >= year * 10000 + 101,
                    Race.date <= year * 10000 + 1231,
                    Race.venue == venue,
                )
                .all()
            )
            for race in race_list:
                racer_list = SESSION.query(Racer).filter(Racer.race_id == race.id).all()
                if (
                    len(racer_list) == 6
                    and racer_list[0].boat_number == racer_list[0].course
                    and racer_list[1].boat_number == racer_list[1].course
                    and racer_list[2].boat_number == racer_list[2].course
                    and racer_list[3].boat_number == racer_list[3].course
                    and racer_list[4].boat_number == racer_list[4].course
                    and racer_list[5].boat_number == racer_list[5].course
                ):
                    normal_entry_race_count += 1
                    match race.first:
                        case 1:
                            normal_entry_course1_1st_count += 1
                        case 2:
                            normal_entry_course2_1st_count += 1
                        case 3:
                            normal_entry_course3_1st_count += 1
                        case 4:
                            normal_entry_course4_1st_count += 1
                        case 5:
                            normal_entry_course5_1st_count += 1
                        case 6:
                            normal_entry_course6_1st_count += 1
                        case _:
                            pass
                    match race.second:
                        case 1:
                            normal_entry_course1_2nd_count += 1
                        case 2:
                            normal_entry_course2_2nd_count += 1
                        case 3:
                            normal_entry_course3_2nd_count += 1
                        case 4:
                            normal_entry_course4_2nd_count += 1
                        case 5:
                            normal_entry_course5_2nd_count += 1
                        case 6:
                            normal_entry_course6_2nd_count += 1
                        case _:
                            pass
                    match race.third:
                        case 1:
                            normal_entry_course1_3rd_count += 1
                        case 2:
                            normal_entry_course2_3rd_count += 1
                        case 3:
                            normal_entry_course3_3rd_count += 1
                        case 4:
                            normal_entry_course4_3rd_count += 1
                        case 5:
                            normal_entry_course5_3rd_count += 1
                        case 6:
                            normal_entry_course6_3rd_count += 1
                        case _:
                            pass
            venue_stat = SESSION.query(VenueStat).filter(VenueStat.venue == venue, VenueStat.year == year).one_or_none()
            if venue_stat is not None:
                venue_stat.normal_entry_race_count = normal_entry_race_count
                venue_stat.normal_entry_course1_1st_count = normal_entry_course1_1st_count
                venue_stat.normal_entry_course1_2nd_count = normal_entry_course1_2nd_count
                venue_stat.normal_entry_course1_3rd_count = normal_entry_course1_3rd_count
                venue_stat.normal_entry_course1_1st_rate = round((normal_entry_course1_1st_count / normal_entry_race_count) * 100, 2)
                venue_stat.normal_entry_course1_2nd_rate = round((normal_entry_course1_2nd_count / normal_entry_race_count) * 100, 2)
                venue_stat.normal_entry_course1_3rd_rate = round((normal_entry_course1_3rd_count / normal_entry_race_count) * 100, 2)
                venue_stat.normal_entry_course2_1st_count = normal_entry_course2_1st_count
                venue_stat.normal_entry_course2_2nd_count = normal_entry_course2_2nd_count
                venue_stat.normal_entry_course2_3rd_count = normal_entry_course2_3rd_count
                venue_stat.normal_entry_course2_1st_rate = round((normal_entry_course2_1st_count / normal_entry_race_count) * 100, 2)
                venue_stat.normal_entry_course2_2nd_rate = round((normal_entry_course2_2nd_count / normal_entry_race_count) * 100, 2)
                venue_stat.normal_entry_course2_3rd_rate = round((normal_entry_course2_3rd_count / normal_entry_race_count) * 100, 2)
                venue_stat.normal_entry_course3_1st_count = normal_entry_course3_1st_count
                venue_stat.normal_entry_course3_2nd_count = normal_entry_course3_2nd_count
                venue_stat.normal_entry_course3_3rd_count = normal_entry_course3_3rd_count
                venue_stat.normal_entry_course3_1st_rate = round((normal_entry_course3_1st_count / normal_entry_race_count) * 100, 2)
                venue_stat.normal_entry_course3_2nd_rate = round((normal_entry_course3_2nd_count / normal_entry_race_count) * 100, 2)
                venue_stat.normal_entry_course3_3rd_rate = round((normal_entry_course3_3rd_count / normal_entry_race_count) * 100, 2)
                venue_stat.normal_entry_course4_1st_count = normal_entry_course4_1st_count
                venue_stat.normal_entry_course4_2nd_count = normal_entry_course4_2nd_count
                venue_stat.normal_entry_course4_3rd_count = normal_entry_course4_3rd_count
                venue_stat.normal_entry_course4_1st_rate = round((normal_entry_course4_1st_count / normal_entry_race_count) * 100, 2)
                venue_stat.normal_entry_course4_2nd_rate = round((normal_entry_course4_2nd_count / normal_entry_race_count) * 100, 2)
                venue_stat.normal_entry_course4_3rd_rate = round((normal_entry_course4_3rd_count / normal_entry_race_count) * 100, 2)
                venue_stat.normal_entry_course5_1st_count = normal_entry_course5_1st_count
                venue_stat.normal_entry_course5_2nd_count = normal_entry_course5_2nd_count
                venue_stat.normal_entry_course5_3rd_count = normal_entry_course5_3rd_count
                venue_stat.normal_entry_course5_1st_rate = round((normal_entry_course5_1st_count / normal_entry_race_count) * 100, 2)
                venue_stat.normal_entry_course5_2nd_rate = round((normal_entry_course5_2nd_count / normal_entry_race_count) * 100, 2)
                venue_stat.normal_entry_course5_3rd_rate = round((normal_entry_course5_3rd_count / normal_entry_race_count) * 100, 2)
                venue_stat.normal_entry_course6_1st_count = normal_entry_course6_1st_count
                venue_stat.normal_entry_course6_2nd_count = normal_entry_course6_2nd_count
                venue_stat.normal_entry_course6_3rd_count = normal_entry_course6_3rd_count
                venue_stat.normal_entry_course6_1st_rate = round((normal_entry_course6_1st_count / normal_entry_race_count) * 100, 2)
                venue_stat.normal_entry_course6_2nd_rate = round((normal_entry_course6_2nd_count / normal_entry_race_count) * 100, 2)
                venue_stat.normal_entry_course6_3rd_rate = round((normal_entry_course6_3rd_count / normal_entry_race_count) * 100, 2)
            else:
                venue_stat_list.append(
                    VenueStat(
                        venue=venue,
                        year=year,
                        normal_entry_race_count=normal_entry_race_count,
                        normal_entry_course1_1st_count=normal_entry_course1_1st_count,
                        normal_entry_course1_2nd_count=normal_entry_course1_2nd_count,
                        normal_entry_course1_3rd_count=normal_entry_course1_3rd_count,
                        normal_entry_course1_1st_rate=round((normal_entry_course1_1st_count / normal_entry_race_count) * 100, 2),
                        normal_entry_course1_2nd_rate=round((normal_entry_course1_2nd_count / normal_entry_race_count) * 100, 2),
                        normal_entry_course1_3rd_rate=round((normal_entry_course1_3rd_count / normal_entry_race_count) * 100, 2),
                        normal_entry_course2_1st_count=normal_entry_course2_1st_count,
                        normal_entry_course2_2nd_count=normal_entry_course2_2nd_count,
                        normal_entry_course2_3rd_count=normal_entry_course2_3rd_count,
                        normal_entry_course2_1st_rate=round((normal_entry_course2_1st_count / normal_entry_race_count) * 100, 2),
                        normal_entry_course2_2nd_rate=round((normal_entry_course2_2nd_count / normal_entry_race_count) * 100, 2),
                        normal_entry_course2_3rd_rate=round((normal_entry_course2_3rd_count / normal_entry_race_count) * 100, 2),
                        normal_entry_course3_1st_count=normal_entry_course3_1st_count,
                        normal_entry_course3_2nd_count=normal_entry_course3_2nd_count,
                        normal_entry_course3_3rd_count=normal_entry_course3_3rd_count,
                        normal_entry_course3_1st_rate=round((normal_entry_course3_1st_count / normal_entry_race_count) * 100, 2),
                        normal_entry_course3_2nd_rate=round((normal_entry_course3_2nd_count / normal_entry_race_count) * 100, 2),
                        normal_entry_course3_3rd_rate=round((normal_entry_course3_3rd_count / normal_entry_race_count) * 100, 2),
                        normal_entry_course4_1st_count=normal_entry_course4_1st_count,
                        normal_entry_course4_2nd_count=normal_entry_course4_2nd_count,
                        normal_entry_course4_3rd_count=normal_entry_course4_3rd_count,
                        normal_entry_course4_1st_rate=round((normal_entry_course4_1st_count / normal_entry_race_count) * 100, 2),
                        normal_entry_course4_2nd_rate=round((normal_entry_course4_2nd_count / normal_entry_race_count) * 100, 2),
                        normal_entry_course4_3rd_rate=round((normal_entry_course4_3rd_count / normal_entry_race_count) * 100, 2),
                        normal_entry_course5_1st_count=normal_entry_course5_1st_count,
                        normal_entry_course5_2nd_count=normal_entry_course5_2nd_count,
                        normal_entry_course5_3rd_count=normal_entry_course5_3rd_count,
                        normal_entry_course5_1st_rate=round((normal_entry_course5_1st_count / normal_entry_race_count) * 100, 2),
                        normal_entry_course5_2nd_rate=round((normal_entry_course5_2nd_count / normal_entry_race_count) * 100, 2),
                        normal_entry_course5_3rd_rate=round((normal_entry_course5_3rd_count / normal_entry_race_count) * 100, 2),
                        normal_entry_course6_1st_count=normal_entry_course6_1st_count,
                        normal_entry_course6_2nd_count=normal_entry_course6_2nd_count,
                        normal_entry_course6_3rd_count=normal_entry_course6_3rd_count,
                        normal_entry_course6_1st_rate=round((normal_entry_course6_1st_count / normal_entry_race_count) * 100, 2),
                        normal_entry_course6_2nd_rate=round((normal_entry_course6_2nd_count / normal_entry_race_count) * 100, 2),
                        normal_entry_course6_3rd_rate=round((normal_entry_course6_3rd_count / normal_entry_race_count) * 100, 2),
                    )
                )
        SESSION.add_all(venue_stat_list)
    SESSION.commit()

    # racer
    print("racer")
    race_list = (
        SESSION.query(Race)
        .filter(
            Race.is_cancel == 0,
            Race.date >= (oldest_race.date // 10000 + 1) * 10000 + 101,
            Race.date <= date.today().year * 10000 + 1231,
        )
        .order_by(Race.id.asc())
        .all()
    )
    for race in tqdm(race_list):
        racer_list = SESSION.query(Racer).filter(Racer.race_id == race.id).order_by(Racer.boat_number.asc()).all()
        for racer in racer_list:
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
            last10_racer_list = (
                SESSION.query(Racer)
                .filter(
                    Racer.race_id < race.id,
                    Racer.racer_number == racer.racer_number,
                    Racer.start_timing.isnot(None),
                    Racer.result.isnot(None),
                )
                .order_by(Racer.race_id.desc())
                .limit(10)
                .all()
            )
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
                racer.last5_1st_count = last5_1st_count
                racer.last5_2nd_count = last5_2nd_count
                racer.last5_3rd_count = last5_3rd_count
                racer.last5_1st_rate = round((last5_1st_count / 5) * 100, 2)
                racer.last5_2nd_rate = round((last5_2nd_count / 5) * 100, 2)
                racer.last5_3rd_rate = round((last5_3rd_count / 5) * 100, 2)
                racer.last5_average_rank = numpy.mean(last5_result_list)
                racer.last5_average_start_timing = numpy.mean(last5_start_timing_list)
                racer.last5_start_timing_std = numpy.std(last5_start_timing_list)
            else:
                racer.last5_1st_count = None
                racer.last5_2nd_count = None
                racer.last5_3rd_count = None
                racer.last5_1st_rate = None
                racer.last5_2nd_rate = None
                racer.last5_3rd_rate = None
                racer.last5_average_rank = None
                racer.last5_average_start_timing = None
                racer.last5_start_timing_std = None
            if len(last10_racer_list) == 10:
                racer.last10_1st_count = last10_1st_count
                racer.last10_2nd_count = last10_2nd_count
                racer.last10_3rd_count = last10_3rd_count
                racer.last10_1st_rate = round((last10_1st_count / 10) * 100, 2)
                racer.last10_2nd_rate = round((last10_2nd_count / 10) * 100, 2)
                racer.last10_3rd_rate = round((last10_3rd_count / 10) * 100, 2)
                racer.last10_average_rank = numpy.mean(last10_result_list)
                racer.last10_average_start_timing = numpy.mean(last10_start_timing_list)
                racer.last10_start_timing_std = numpy.std(last10_start_timing_list)
            else:
                racer.last10_1st_count = None
                racer.last10_2nd_count = None
                racer.last10_3rd_count = None
                racer.last10_1st_rate = None
                racer.last10_2nd_rate = None
                racer.last10_3rd_rate = None
                racer.last10_average_rank = None
                racer.last10_average_start_timing = None
                racer.last10_start_timing_std = None
    SESSION.commit()


if __name__ == "__main__":
    main()
