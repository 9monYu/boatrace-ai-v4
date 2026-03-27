import csv
import os

import numpy
from tqdm import tqdm

from constants import SESSION, TRIFECTA_LIST
from models import Race, Racer, Ticket


def main():
    # race
    directory_path = os.path.join(os.getcwd(), "scraping_data", "race")
    for file in tqdm(os.listdir(directory_path)):
        if file.endswith(".csv") and file.startswith("race_"):
            with open(os.path.join(directory_path, file), "r", encoding="UTF-8") as f:
                for row in csv.reader(f):
                    race_id = int(row[0])
                    race = SESSION.query(Race).filter(Race.id == race_id).one_or_none()
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
            SESSION.commit()

    # racer
    directory_path = os.path.join(os.getcwd(), "scraping_data", "racer")
    for file in tqdm(os.listdir(directory_path)):
        if file.endswith(".csv") and file.startswith("racer_"):
            race_id_list = []
            racer_list = []
            with open(os.path.join(directory_path, file), "r", encoding="UTF-8") as f:
                for row in csv.reader(f):
                    race_id = int(row[0])
                    if race_id not in race_id_list:
                        race_id_list.append(race_id)
                    boat_number = int(row[1])
                    racer = (
                        SESSION.query(Racer)
                        .filter(Racer.race_id == race_id, Racer.boat_number == boat_number)
                        .one_or_none()
                    )
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
            SESSION.add_all(racer_list)
            SESSION.commit()

            for race_id in race_id_list:
                racer_list = SESSION.query(Racer).filter(Racer.race_id == race_id).all()

                # average_start_timing
                average_start_timing_list = [
                    racer.average_start_timing for racer in racer_list if racer.average_start_timing is not None
                ]
                average_start_timing_list.sort()
                average_start_timing_mean = (
                    numpy.mean(average_start_timing_list) if average_start_timing_list else None
                )
                average_start_timing_std = numpy.std(average_start_timing_list) if average_start_timing_list else None
                # all_venue_win_rate
                all_venue_win_rate_list = [
                    racer.all_venue_win_rate for racer in racer_list if racer.all_venue_win_rate is not None
                ]
                all_venue_win_rate_list.sort(reverse=True)
                all_venue_win_rate_mean = numpy.mean(all_venue_win_rate_list) if all_venue_win_rate_list else None
                all_venue_win_rate_std = numpy.std(all_venue_win_rate_list) if all_venue_win_rate_list else None
                # all_venue_top2_rate
                all_venue_top2_rate_list = [
                    racer.all_venue_top2_rate for racer in racer_list if racer.all_venue_top2_rate is not None
                ]
                all_venue_top2_rate_list.sort(reverse=True)
                all_venue_top2_rate_mean = numpy.mean(all_venue_top2_rate_list) if all_venue_top2_rate_list else None
                all_venue_top2_rate_std = numpy.std(all_venue_top2_rate_list) if all_venue_top2_rate_list else None
                # all_venue_top3_rate
                all_venue_top3_rate_list = [
                    racer.all_venue_top3_rate for racer in racer_list if racer.all_venue_top3_rate is not None
                ]
                all_venue_top3_rate_list.sort(reverse=True)
                all_venue_top3_rate_mean = numpy.mean(all_venue_top3_rate_list) if all_venue_top3_rate_list else None
                all_venue_top3_rate_std = numpy.std(all_venue_top3_rate_list) if all_venue_top3_rate_list else None
                # this_venue_win_rate
                this_venue_win_rate_list = [
                    racer.this_venue_win_rate for racer in racer_list if racer.this_venue_win_rate is not None
                ]
                this_venue_win_rate_list.sort(reverse=True)
                this_venue_win_rate_mean = numpy.mean(this_venue_win_rate_list) if this_venue_win_rate_list else None
                this_venue_win_rate_std = numpy.std(this_venue_win_rate_list) if this_venue_win_rate_list else None
                # this_venue_top2_rate
                this_venue_top2_rate_list = [
                    racer.this_venue_top2_rate for racer in racer_list if racer.this_venue_top2_rate is not None
                ]
                this_venue_top2_rate_list.sort(reverse=True)
                this_venue_top2_rate_mean = (
                    numpy.mean(this_venue_top2_rate_list) if this_venue_top2_rate_list else None
                )
                this_venue_top2_rate_std = numpy.std(this_venue_top2_rate_list) if this_venue_top2_rate_list else None
                # this_venue_top3_rate
                this_venue_top3_rate_list = [
                    racer.this_venue_top3_rate for racer in racer_list if racer.this_venue_top3_rate is not None
                ]
                this_venue_top3_rate_list.sort(reverse=True)
                this_venue_top3_rate_mean = (
                    numpy.mean(this_venue_top3_rate_list) if this_venue_top3_rate_list else None
                )
                this_venue_top3_rate_std = numpy.std(this_venue_top3_rate_list) if this_venue_top3_rate_list else None
                # motor_top2_rate
                motor_top2_rate_list = [
                    racer.motor_top2_rate for racer in racer_list if racer.motor_top2_rate is not None
                ]
                motor_top2_rate_list.sort(reverse=True)
                motor_top2_rate_mean = numpy.mean(motor_top2_rate_list) if motor_top2_rate_list else None
                motor_top2_rate_std = numpy.std(motor_top2_rate_list) if motor_top2_rate_list else None
                # motor_top3_rate
                motor_top3_rate_list = [
                    racer.motor_top3_rate for racer in racer_list if racer.motor_top3_rate is not None
                ]
                motor_top3_rate_list.sort(reverse=True)
                motor_top3_rate_mean = numpy.mean(motor_top3_rate_list) if motor_top3_rate_list else None
                motor_top3_rate_std = numpy.std(motor_top3_rate_list) if motor_top3_rate_list else None
                # boat_top2_rate
                boat_top2_rate_list = [
                    racer.boat_top2_rate for racer in racer_list if racer.boat_top2_rate is not None
                ]
                boat_top2_rate_list.sort(reverse=True)
                boat_top2_rate_mean = numpy.mean(boat_top2_rate_list) if boat_top2_rate_list else None
                boat_top2_rate_std = numpy.std(boat_top2_rate_list) if boat_top2_rate_list else None
                # boat_top3_rate
                boat_top3_rate_list = [
                    racer.boat_top3_rate for racer in racer_list if racer.boat_top3_rate is not None
                ]
                boat_top3_rate_list.sort(reverse=True)
                boat_top3_rate_mean = numpy.mean(boat_top3_rate_list) if boat_top3_rate_list else None
                boat_top3_rate_std = numpy.std(boat_top3_rate_list) if boat_top3_rate_list else None
                # before_info_start_timing_abs
                before_info_start_timing_abs_list = [
                    racer.before_info_start_timing_abs
                    for racer in racer_list
                    if racer.before_info_start_timing_abs is not None
                ]
                before_info_start_timing_abs_list.sort()
                before_info_start_timing_abs_mean = (
                    numpy.mean(before_info_start_timing_abs_list) if before_info_start_timing_abs_list else None
                )
                before_info_start_timing_abs_std = (
                    numpy.std(before_info_start_timing_abs_list) if before_info_start_timing_abs_list else None
                )
                # before_info_display_time
                before_info_display_time_list = [
                    racer.before_info_display_time
                    for racer in racer_list
                    if racer.before_info_display_time is not None
                ]
                before_info_display_time_list.sort()
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
                        racer.average_start_timing_rank = (
                            average_start_timing_list.index(racer.average_start_timing) + 1
                        )
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
                        racer.all_venue_win_rate_rank = all_venue_win_rate_list.index(racer.all_venue_win_rate) + 1
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
                        racer.all_venue_top2_rate_rank = all_venue_top2_rate_list.index(racer.all_venue_top2_rate) + 1
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
                        racer.all_venue_top3_rate_rank = all_venue_top3_rate_list.index(racer.all_venue_top3_rate) + 1
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
                        racer.this_venue_win_rate_rank = this_venue_win_rate_list.index(racer.this_venue_win_rate) + 1
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
                        racer.this_venue_top2_rate_rank = (
                            this_venue_top2_rate_list.index(racer.this_venue_top2_rate) + 1
                        )
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
                        racer.this_venue_top3_rate_rank = (
                            this_venue_top3_rate_list.index(racer.this_venue_top3_rate) + 1
                        )
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
                        racer.motor_top2_rate_rank = motor_top2_rate_list.index(racer.motor_top2_rate) + 1
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
                        racer.motor_top3_rate_rank = motor_top3_rate_list.index(racer.motor_top3_rate) + 1
                        racer.motor_top3_rate_z_score = (
                            (racer.motor_top3_rate - motor_top3_rate_mean) / motor_top3_rate_std
                            if motor_top3_rate_std > 0
                            else 0.0
                        )
                    # boat_top2_rate
                    if (
                        racer.boat_top2_rate is not None
                        and boat_top2_rate_mean is not None
                        and boat_top2_rate_std is not None
                    ):
                        racer.boat_top2_rate_rank = boat_top2_rate_list.index(racer.boat_top2_rate) + 1
                        racer.boat_top2_rate_z_score = (
                            (racer.boat_top2_rate - boat_top2_rate_mean) / boat_top2_rate_std
                            if boat_top2_rate_std > 0
                            else 0.0
                        )
                    # boat_top3_rate
                    if (
                        racer.boat_top3_rate is not None
                        and boat_top3_rate_mean is not None
                        and boat_top3_rate_std is not None
                    ):
                        racer.boat_top3_rate_rank = boat_top3_rate_list.index(racer.boat_top3_rate) + 1
                        racer.boat_top3_rate_z_score = (
                            (racer.boat_top3_rate - boat_top3_rate_mean) / boat_top3_rate_std
                            if boat_top3_rate_std > 0
                            else 0.0
                        )
                    # before_info_start_timing_abs
                    if (
                        racer.before_info_start_timing_abs is not None
                        and before_info_start_timing_abs_mean is not None
                        and before_info_start_timing_abs_std is not None
                    ):
                        racer.before_info_start_timing_abs_rank = (
                            before_info_start_timing_abs_list.index(racer.before_info_start_timing_abs) + 1
                        )
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
                        racer.before_info_display_time_rank = (
                            before_info_display_time_list.index(racer.before_info_display_time) + 1
                        )
                        racer.before_info_display_time_z_score = (
                            (before_info_display_time_mean - racer.before_info_display_time)
                            / before_info_display_time_std
                            if before_info_display_time_std > 0
                            else 0.0
                        )
                    # ability_index
                    if (
                        racer.average_start_timing_z_score is not None
                        and racer.all_venue_win_rate_z_score is not None
                        and racer.this_venue_win_rate_z_score is not None
                        and racer.motor_top2_rate_z_score is not None
                    ):
                        racer.ability_index = (
                            racer.average_start_timing_z_score
                            + racer.all_venue_win_rate_z_score
                            + racer.this_venue_win_rate_z_score
                            + racer.motor_top2_rate_z_score
                        )
                    # before_info_index
                    if (
                        racer.before_info_start_timing_abs_z_score is not None
                        and racer.before_info_display_time_z_score is not None
                    ):
                        racer.before_info_index = (
                            racer.before_info_start_timing_abs_z_score + racer.before_info_display_time_z_score
                        )

                # ability_index
                ability_index_list = [racer.ability_index for racer in racer_list if racer.ability_index is not None]
                ability_index_list.sort(reverse=True)
                ability_index_mean = numpy.mean(ability_index_list) if ability_index_list else None
                ability_index_std = numpy.std(ability_index_list) if ability_index_list else None
                # before_info_index
                before_info_index_list = [
                    racer.before_info_index for racer in racer_list if racer.before_info_index is not None
                ]
                before_info_index_list.sort(reverse=True)
                before_info_index_mean = numpy.mean(before_info_index_list) if before_info_index_list else None
                before_info_index_std = numpy.std(before_info_index_list) if before_info_index_list else None

                for racer in racer_list:
                    # ability_index
                    if (
                        racer.ability_index is not None
                        and ability_index_mean is not None
                        and ability_index_std is not None
                    ):
                        racer.ability_index_rank = ability_index_list.index(racer.ability_index) + 1
                        racer.ability_index_z_score = (
                            (racer.ability_index - ability_index_mean) / ability_index_std
                            if ability_index_std > 0
                            else 0.0
                        )
                    # before_info_index
                    if (
                        racer.before_info_index is not None
                        and before_info_index_mean is not None
                        and before_info_index_std is not None
                    ):
                        racer.before_info_index_rank = before_info_index_list.index(racer.before_info_index) + 1
                        racer.before_info_index_z_score = (
                            (racer.before_info_index - before_info_index_mean) / before_info_index_std
                            if before_info_index_std > 0
                            else 0.0
                        )

            SESSION.commit()

    # deadline odds
    directory_path = os.path.join(os.getcwd(), "scraping_data", "deadline_odds")
    for file in tqdm(os.listdir(directory_path)):
        if file.endswith(".csv") and file.startswith("deadline_odds_"):
            ticket_list = []
            with open(os.path.join(directory_path, file), "r", encoding="UTF-8") as f:
                for row in csv.reader(f):
                    race_id = int(row.pop(0))
                    race = SESSION.query(Race).filter(Race.id == race_id).one()
                    deadline_odds_list = sorted([float(x) for x in row if x and x != "0.0"])
                    sum_deadline_odds_inverse = sum(1.0 / deadline_odds for deadline_odds in deadline_odds_list)
                    SESSION.query(Ticket).filter(Ticket.race_id == race_id).delete()
                    for index in range(120):
                        is_hit = (
                            1
                            if race.first == TRIFECTA_LIST[index][0]
                            and race.second == TRIFECTA_LIST[index][1]
                            and race.third == TRIFECTA_LIST[index][2]
                            else 0
                        )
                        deadline_odds = float(row[index]) if row[index] and row[index] != "0.0" else None
                        market_share = (
                            (1.0 / deadline_odds) / sum_deadline_odds_inverse if deadline_odds is not None else None
                        )
                        deadline_odds_rank = deadline_odds_list.index(deadline_odds) + 1 if deadline_odds else None
                        ticket_list.append(
                            Ticket(
                                race_id=race_id,
                                first=TRIFECTA_LIST[index][0],
                                second=TRIFECTA_LIST[index][1],
                                third=TRIFECTA_LIST[index][2],
                                is_hit=is_hit,
                                deadline_odds=deadline_odds,
                                deadline_odds_rank=deadline_odds_rank,
                                market_share=market_share,
                            )
                        )
            SESSION.add_all(ticket_list)
            SESSION.commit()


if __name__ == "__main__":
    main()
