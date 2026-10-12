import numpy
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from tqdm import tqdm

from database import Session
from models import Race, Racer


def main():
    oldest_race = Session.scalars(select(Race).order_by(Race.id.asc())).first()
    latest_race = Session.scalars(select(Race).order_by(Race.id.desc())).first()

    for year in range(oldest_race.date // 10000 + 1, latest_race.date // 10000 + 1):
        race_list = Session.scalars(
            select(Race)
            .options(selectinload(Race.racers))
            .where(
                Race.is_cancel == 0,
                Race.date >= year * 10000 + 101,
                Race.date <= year * 10000 + 1231,
            )
            .order_by(Race.id.asc())
        ).all()
        for race in tqdm(race_list, desc=f"{year}"):
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

                boat_number_course_last5_1st_count = 0
                boat_number_course_last5_2nd_count = 0
                boat_number_course_last5_3rd_count = 0
                boat_number_course_last5_result_list = []
                boat_number_course_last5_start_timing_list = []
                boat_number_course_last10_1st_count = 0
                boat_number_course_last10_2nd_count = 0
                boat_number_course_last10_3rd_count = 0
                boat_number_course_last10_result_list = []
                boat_number_course_last10_start_timing_list = []
                boat_number_course_last10_racer_list = Session.scalars(
                    select(Racer)
                    .where(
                        Racer.race_id < race.id,
                        Racer.racer_number == racer.racer_number,
                        Racer.boat_number == racer.boat_number,
                        Racer.course == racer.boat_number,
                        Racer.start_timing.isnot(None),
                        Racer.result.isnot(None),
                    )
                    .order_by(Racer.race_id.desc())
                    .limit(10)
                ).all()
                for index, boat_number_course_last10_racer in enumerate(boat_number_course_last10_racer_list):
                    if boat_number_course_last10_racer.result == 1:
                        if index < 5:
                            boat_number_course_last5_1st_count += 1
                        boat_number_course_last10_1st_count += 1
                    elif boat_number_course_last10_racer.result == 2:
                        if index < 5:
                            boat_number_course_last5_2nd_count += 1
                        boat_number_course_last10_2nd_count += 1
                    elif boat_number_course_last10_racer.result == 3:
                        if index < 5:
                            boat_number_course_last5_3rd_count += 1
                        boat_number_course_last10_3rd_count += 1
                    else:
                        pass
                    if index < 5:
                        boat_number_course_last5_result_list.append(boat_number_course_last10_racer.result)
                    boat_number_course_last10_result_list.append(boat_number_course_last10_racer.result)
                    if index < 5:
                        boat_number_course_last5_start_timing_list.append(boat_number_course_last10_racer.start_timing)
                    boat_number_course_last10_start_timing_list.append(boat_number_course_last10_racer.start_timing)
                if len(boat_number_course_last10_racer_list) >= 5:
                    racer.boat_number_course_last5_1st_rate = round((boat_number_course_last5_1st_count / 5) * 100, 2)
                    racer.boat_number_course_last5_2nd_rate = round((boat_number_course_last5_2nd_count / 5) * 100, 2)
                    racer.boat_number_course_last5_3rd_rate = round((boat_number_course_last5_3rd_count / 5) * 100, 2)
                    racer.boat_number_course_last5_average_rank = numpy.mean(boat_number_course_last5_result_list)
                    racer.boat_number_course_last5_average_start_timing = numpy.mean(
                        boat_number_course_last5_start_timing_list
                    )
                    racer.boat_number_course_last5_start_timing_std = numpy.std(
                        boat_number_course_last5_start_timing_list
                    )
                else:
                    racer.boat_number_course_last5_1st_rate = None
                    racer.boat_number_course_last5_2nd_rate = None
                    racer.boat_number_course_last5_3rd_rate = None
                    racer.boat_number_course_last5_average_rank = None
                    racer.boat_number_course_last5_average_start_timing = None
                    racer.boat_number_course_last5_start_timing_std = None
                if len(boat_number_course_last10_racer_list) == 10:
                    racer.boat_number_course_last10_1st_rate = round(
                        (boat_number_course_last10_1st_count / 10) * 100, 2
                    )
                    racer.boat_number_course_last10_2nd_rate = round(
                        (boat_number_course_last10_2nd_count / 10) * 100, 2
                    )
                    racer.boat_number_course_last10_3rd_rate = round(
                        (boat_number_course_last10_3rd_count / 10) * 100, 2
                    )
                    racer.boat_number_course_last10_average_rank = numpy.mean(boat_number_course_last10_result_list)
                    racer.boat_number_course_last10_average_start_timing = numpy.mean(
                        boat_number_course_last10_start_timing_list
                    )
                    racer.boat_number_course_last10_start_timing_std = numpy.std(
                        boat_number_course_last10_start_timing_list
                    )
                else:
                    racer.boat_number_course_last10_1st_rate = None
                    racer.boat_number_course_last10_2nd_rate = None
                    racer.boat_number_course_last10_3rd_rate = None
                    racer.boat_number_course_last10_average_rank = None
                    racer.boat_number_course_last10_average_start_timing = None
                    racer.boat_number_course_last10_start_timing_std = None

        Session.commit()


if __name__ == "__main__":
    main()
