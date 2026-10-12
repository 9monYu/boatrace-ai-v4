import argparse
import csv
import os
from datetime import datetime

import numpy
from sqlalchemy import func, select
from tqdm import tqdm

from constants import CSV_COLUMN_LIST, GRADE_LIST, RACER_CLASS_LIST, TRIFECTA_LIST, WEATHER_LIST, WIND_DIRECTION_ANGLES
from database import Session
from models import PeriodStat, Race, Racer, Ticket, VenueStat


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("years", type=int, nargs="+")
    args = parser.parse_args()

    year_venue_stats: dict[int, dict[int, VenueStat]] = {}
    for venue_stat in Session.scalars(select(VenueStat)).all():
        year_venue_stats.setdefault(venue_stat.year, {})[venue_stat.venue] = venue_stat

    for year in args.years:
        for dataset, (start, end) in {
            "train": ((year - 5) * 10000 + 101, (year - 1) * 10000 + 1231),
            "eval": ((year) * 10000 + 101, (year) * 10000 + 1231),
        }.items():
            with open(
                os.path.join(os.getcwd(), "dataset", f"{year}_{dataset}.csv"),
                mode="w",
                encoding="UTF-8",
                newline="",
            ) as f:
                writer = csv.writer(f)
                header = CSV_COLUMN_LIST if dataset != "eval" else CSV_COLUMN_LIST[:-1]
                writer.writerow(header)
                conditions = [
                    Race.is_cancel == 0,
                    Race.date >= start,
                    Race.date <= end,
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
                ]
                if dataset != "eval":
                    conditions.append(Race.first.is_not(None))
                    conditions.append(Race.second.is_not(None))
                    conditions.append(Race.third.is_not(None))
                race_list = Session.scalars(select(Race).where(*conditions).order_by(Race.id.asc())).all()
                for race in tqdm(race_list, desc=f"{year} {dataset:<5}"):
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
                                round(
                                    (boat1_period_stat.course1_1st_count / boat1_period_stat.course1_entry_count) * 100,
                                    2,
                                ),
                                round(
                                    (boat2_period_stat.course2_1st_count / boat2_period_stat.course2_entry_count) * 100,
                                    2,
                                ),
                                round(
                                    (boat3_period_stat.course3_1st_count / boat3_period_stat.course3_entry_count) * 100,
                                    2,
                                ),
                                round(
                                    (boat4_period_stat.course4_1st_count / boat4_period_stat.course4_entry_count) * 100,
                                    2,
                                ),
                                round(
                                    (boat5_period_stat.course5_1st_count / boat5_period_stat.course5_entry_count) * 100,
                                    2,
                                ),
                                round(
                                    (boat6_period_stat.course6_1st_count / boat6_period_stat.course6_entry_count) * 100,
                                    2,
                                ),
                            ]
                            # course_2nd_rate
                            course_2nd_rate_list = [
                                round(
                                    (boat1_period_stat.course1_2nd_count / boat1_period_stat.course1_entry_count) * 100,
                                    2,
                                ),
                                round(
                                    (boat2_period_stat.course2_2nd_count / boat2_period_stat.course2_entry_count) * 100,
                                    2,
                                ),
                                round(
                                    (boat3_period_stat.course3_2nd_count / boat3_period_stat.course3_entry_count) * 100,
                                    2,
                                ),
                                round(
                                    (boat4_period_stat.course4_2nd_count / boat4_period_stat.course4_entry_count) * 100,
                                    2,
                                ),
                                round(
                                    (boat5_period_stat.course5_2nd_count / boat5_period_stat.course5_entry_count) * 100,
                                    2,
                                ),
                                round(
                                    (boat6_period_stat.course6_2nd_count / boat6_period_stat.course6_entry_count) * 100,
                                    2,
                                ),
                            ]
                            # course_3rd_rate
                            course_3rd_rate_list = [
                                round(
                                    (boat1_period_stat.course1_3rd_count / boat1_period_stat.course1_entry_count) * 100,
                                    2,
                                ),
                                round(
                                    (boat2_period_stat.course2_3rd_count / boat2_period_stat.course2_entry_count) * 100,
                                    2,
                                ),
                                round(
                                    (boat3_period_stat.course3_3rd_count / boat3_period_stat.course3_entry_count) * 100,
                                    2,
                                ),
                                round(
                                    (boat4_period_stat.course4_3rd_count / boat4_period_stat.course4_entry_count) * 100,
                                    2,
                                ),
                                round(
                                    (boat5_period_stat.course5_3rd_count / boat5_period_stat.course5_entry_count) * 100,
                                    2,
                                ),
                                round(
                                    (boat6_period_stat.course6_3rd_count / boat6_period_stat.course6_entry_count) * 100,
                                    2,
                                ),
                            ]

                            row = []
                            row.append(race.id)
                            row.append(GRADE_LIST.index(race.grade))
                            row.append((race.date // 100) % 100)
                            row.append(datetime.strptime(str(race.date), "%Y%m%d").date().weekday())
                            row.append(race.period_progress_rate)
                            row.append(race.venue)
                            venue_stat = year_venue_stats[(race.date // 10000) - 1][race.venue]
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
                            average_start_timing_z_score_list = [
                                racer.average_start_timing_z_score for racer in racer_list
                            ]
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
                                racer_list[0].all_venue_win_rate_z_score
                                - numpy.mean(boat23456_all_venue_win_rate_z_score_list)
                            )

                            # this_venue_win_rate
                            row.append(numpy.std([racer.this_venue_win_rate for racer in racer_list]))
                            this_venue_win_rate_z_score_list = [
                                racer.this_venue_win_rate_z_score for racer in racer_list
                            ]
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
                                racer_list[0].motor_top2_rate_z_score
                                - numpy.mean(boat23456_motor_top2_rate_z_score_list)
                            )

                            # before_info_start_timing
                            row.append(numpy.std([racer.before_info_start_timing_abs for racer in racer_list]))
                            before_info_start_timing_abs_z_score_list = [
                                racer.before_info_start_timing_abs_z_score for racer in racer_list
                            ]
                            row.append(
                                before_info_start_timing_abs_z_score_list[0]
                                - before_info_start_timing_abs_z_score_list[1]
                            )
                            row.append(
                                before_info_start_timing_abs_z_score_list[0]
                                - before_info_start_timing_abs_z_score_list[2]
                            )
                            row.append(
                                before_info_start_timing_abs_z_score_list[0]
                                - before_info_start_timing_abs_z_score_list[3]
                            )
                            row.append(
                                before_info_start_timing_abs_z_score_list[0]
                                - before_info_start_timing_abs_z_score_list[4]
                            )
                            row.append(
                                before_info_start_timing_abs_z_score_list[0]
                                - before_info_start_timing_abs_z_score_list[5]
                            )
                            row.append(
                                before_info_start_timing_abs_z_score_list[1]
                                - before_info_start_timing_abs_z_score_list[2]
                            )
                            row.append(
                                before_info_start_timing_abs_z_score_list[1]
                                - before_info_start_timing_abs_z_score_list[3]
                            )
                            row.append(
                                before_info_start_timing_abs_z_score_list[1]
                                - before_info_start_timing_abs_z_score_list[4]
                            )
                            row.append(
                                before_info_start_timing_abs_z_score_list[1]
                                - before_info_start_timing_abs_z_score_list[5]
                            )
                            row.append(
                                before_info_start_timing_abs_z_score_list[2]
                                - before_info_start_timing_abs_z_score_list[3]
                            )
                            row.append(
                                before_info_start_timing_abs_z_score_list[2]
                                - before_info_start_timing_abs_z_score_list[4]
                            )
                            row.append(
                                before_info_start_timing_abs_z_score_list[2]
                                - before_info_start_timing_abs_z_score_list[5]
                            )
                            row.append(
                                before_info_start_timing_abs_z_score_list[3]
                                - before_info_start_timing_abs_z_score_list[4]
                            )
                            row.append(
                                before_info_start_timing_abs_z_score_list[3]
                                - before_info_start_timing_abs_z_score_list[5]
                            )
                            row.append(
                                before_info_start_timing_abs_z_score_list[4]
                                - before_info_start_timing_abs_z_score_list[5]
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
                            row.append(
                                before_info_display_time_z_score_list[0] - before_info_display_time_z_score_list[1]
                            )
                            row.append(
                                before_info_display_time_z_score_list[0] - before_info_display_time_z_score_list[2]
                            )
                            row.append(
                                before_info_display_time_z_score_list[0] - before_info_display_time_z_score_list[3]
                            )
                            row.append(
                                before_info_display_time_z_score_list[0] - before_info_display_time_z_score_list[4]
                            )
                            row.append(
                                before_info_display_time_z_score_list[0] - before_info_display_time_z_score_list[5]
                            )
                            row.append(
                                before_info_display_time_z_score_list[1] - before_info_display_time_z_score_list[2]
                            )
                            row.append(
                                before_info_display_time_z_score_list[1] - before_info_display_time_z_score_list[3]
                            )
                            row.append(
                                before_info_display_time_z_score_list[1] - before_info_display_time_z_score_list[4]
                            )
                            row.append(
                                before_info_display_time_z_score_list[1] - before_info_display_time_z_score_list[5]
                            )
                            row.append(
                                before_info_display_time_z_score_list[2] - before_info_display_time_z_score_list[3]
                            )
                            row.append(
                                before_info_display_time_z_score_list[2] - before_info_display_time_z_score_list[4]
                            )
                            row.append(
                                before_info_display_time_z_score_list[2] - before_info_display_time_z_score_list[5]
                            )
                            row.append(
                                before_info_display_time_z_score_list[3] - before_info_display_time_z_score_list[4]
                            )
                            row.append(
                                before_info_display_time_z_score_list[3] - before_info_display_time_z_score_list[5]
                            )
                            row.append(
                                before_info_display_time_z_score_list[4] - before_info_display_time_z_score_list[5]
                            )
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

                            if dataset != "eval":
                                row.append(TRIFECTA_LIST.index((race.first, race.second, race.third)))

                            writer.writerow(row)


if __name__ == "__main__":
    main()
