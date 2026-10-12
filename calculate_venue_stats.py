from sqlalchemy import select
from sqlalchemy.orm import selectinload
from tqdm import tqdm

from database import Session
from models import Race, Racer, VenueStat


def main():
    oldest_race = Session.scalars(select(Race).order_by(Race.id.asc())).first()
    latest_race = Session.scalars(select(Race).order_by(Race.id.desc())).first()

    for year in range(
        oldest_race.date // 10000,
        (latest_race.date // 10000) + 1 if latest_race.date % 10000 == 1231 else latest_race.date // 10000,
    ):
        venue_stat_list = []
        for venue in tqdm(range(1, 25), desc=f"{year}"):
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
            race_list = Session.scalars(
                select(Race)
                .options(selectinload(Race.racers))
                .where(
                    Race.is_cancel == 0,
                    Race.date >= year * 10000 + 101,
                    Race.date <= year * 10000 + 1231,
                    Race.venue == venue,
                )
            ).all()
            for race in race_list:
                if (
                    len(race.racers) == 6
                    and race.racers[0].boat_number == race.racers[0].course
                    and race.racers[1].boat_number == race.racers[1].course
                    and race.racers[2].boat_number == race.racers[2].course
                    and race.racers[3].boat_number == race.racers[3].course
                    and race.racers[4].boat_number == race.racers[4].course
                    and race.racers[5].boat_number == race.racers[5].course
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
            venue_stat = Session.scalars(
                select(VenueStat).where(VenueStat.venue == venue, VenueStat.year == year)
            ).one_or_none()
            if venue_stat is not None:
                venue_stat.normal_entry_race_count = normal_entry_race_count
                venue_stat.normal_entry_course1_1st_rate = round(
                    (normal_entry_course1_1st_count / normal_entry_race_count) * 100, 2
                )
                venue_stat.normal_entry_course1_2nd_rate = round(
                    (normal_entry_course1_2nd_count / normal_entry_race_count) * 100, 2
                )
                venue_stat.normal_entry_course1_3rd_rate = round(
                    (normal_entry_course1_3rd_count / normal_entry_race_count) * 100, 2
                )
                venue_stat.normal_entry_course2_1st_rate = round(
                    (normal_entry_course2_1st_count / normal_entry_race_count) * 100, 2
                )
                venue_stat.normal_entry_course2_2nd_rate = round(
                    (normal_entry_course2_2nd_count / normal_entry_race_count) * 100, 2
                )
                venue_stat.normal_entry_course2_3rd_rate = round(
                    (normal_entry_course2_3rd_count / normal_entry_race_count) * 100, 2
                )
                venue_stat.normal_entry_course3_1st_rate = round(
                    (normal_entry_course3_1st_count / normal_entry_race_count) * 100, 2
                )
                venue_stat.normal_entry_course3_2nd_rate = round(
                    (normal_entry_course3_2nd_count / normal_entry_race_count) * 100, 2
                )
                venue_stat.normal_entry_course3_3rd_rate = round(
                    (normal_entry_course3_3rd_count / normal_entry_race_count) * 100, 2
                )
                venue_stat.normal_entry_course4_1st_rate = round(
                    (normal_entry_course4_1st_count / normal_entry_race_count) * 100, 2
                )
                venue_stat.normal_entry_course4_2nd_rate = round(
                    (normal_entry_course4_2nd_count / normal_entry_race_count) * 100, 2
                )
                venue_stat.normal_entry_course4_3rd_rate = round(
                    (normal_entry_course4_3rd_count / normal_entry_race_count) * 100, 2
                )
                venue_stat.normal_entry_course5_1st_rate = round(
                    (normal_entry_course5_1st_count / normal_entry_race_count) * 100, 2
                )
                venue_stat.normal_entry_course5_2nd_rate = round(
                    (normal_entry_course5_2nd_count / normal_entry_race_count) * 100, 2
                )
                venue_stat.normal_entry_course5_3rd_rate = round(
                    (normal_entry_course5_3rd_count / normal_entry_race_count) * 100, 2
                )
                venue_stat.normal_entry_course6_1st_rate = round(
                    (normal_entry_course6_1st_count / normal_entry_race_count) * 100, 2
                )
                venue_stat.normal_entry_course6_2nd_rate = round(
                    (normal_entry_course6_2nd_count / normal_entry_race_count) * 100, 2
                )
                venue_stat.normal_entry_course6_3rd_rate = round(
                    (normal_entry_course6_3rd_count / normal_entry_race_count) * 100, 2
                )
            else:
                venue_stat_list.append(
                    VenueStat(
                        venue=venue,
                        year=year,
                        normal_entry_race_count=normal_entry_race_count,
                        normal_entry_course1_1st_rate=round(
                            (normal_entry_course1_1st_count / normal_entry_race_count) * 100, 2
                        ),
                        normal_entry_course1_2nd_rate=round(
                            (normal_entry_course1_2nd_count / normal_entry_race_count) * 100, 2
                        ),
                        normal_entry_course1_3rd_rate=round(
                            (normal_entry_course1_3rd_count / normal_entry_race_count) * 100, 2
                        ),
                        normal_entry_course2_1st_rate=round(
                            (normal_entry_course2_1st_count / normal_entry_race_count) * 100, 2
                        ),
                        normal_entry_course2_2nd_rate=round(
                            (normal_entry_course2_2nd_count / normal_entry_race_count) * 100, 2
                        ),
                        normal_entry_course2_3rd_rate=round(
                            (normal_entry_course2_3rd_count / normal_entry_race_count) * 100, 2
                        ),
                        normal_entry_course3_1st_rate=round(
                            (normal_entry_course3_1st_count / normal_entry_race_count) * 100, 2
                        ),
                        normal_entry_course3_2nd_rate=round(
                            (normal_entry_course3_2nd_count / normal_entry_race_count) * 100, 2
                        ),
                        normal_entry_course3_3rd_rate=round(
                            (normal_entry_course3_3rd_count / normal_entry_race_count) * 100, 2
                        ),
                        normal_entry_course4_1st_rate=round(
                            (normal_entry_course4_1st_count / normal_entry_race_count) * 100, 2
                        ),
                        normal_entry_course4_2nd_rate=round(
                            (normal_entry_course4_2nd_count / normal_entry_race_count) * 100, 2
                        ),
                        normal_entry_course4_3rd_rate=round(
                            (normal_entry_course4_3rd_count / normal_entry_race_count) * 100, 2
                        ),
                        normal_entry_course5_1st_rate=round(
                            (normal_entry_course5_1st_count / normal_entry_race_count) * 100, 2
                        ),
                        normal_entry_course5_2nd_rate=round(
                            (normal_entry_course5_2nd_count / normal_entry_race_count) * 100, 2
                        ),
                        normal_entry_course5_3rd_rate=round(
                            (normal_entry_course5_3rd_count / normal_entry_race_count) * 100, 2
                        ),
                        normal_entry_course6_1st_rate=round(
                            (normal_entry_course6_1st_count / normal_entry_race_count) * 100, 2
                        ),
                        normal_entry_course6_2nd_rate=round(
                            (normal_entry_course6_2nd_count / normal_entry_race_count) * 100, 2
                        ),
                        normal_entry_course6_3rd_rate=round(
                            (normal_entry_course6_3rd_count / normal_entry_race_count) * 100, 2
                        ),
                    )
                )
        Session.add_all(venue_stat_list)
    Session.commit()


if __name__ == "__main__":
    main()
