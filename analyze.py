import argparse
import csv
import os

from tqdm import tqdm

from constants import SESSION
from models import Race, Ticket

BATCH_SIZE = 1000


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("years", type=int, nargs="+")
    args = parser.parse_args()

    race_list_by_year: dict[int, list[Race]] = {}
    for year in args.years:
        race_list_by_year[year] = (
            SESSION.query(Race)
            .filter(
                Race.is_cancel == 0,
                Race.date >= year * 10000 + 101,
                Race.date <= year * 10000 + 1231,
                Race.grade.isnot(None),
                Race.venue.isnot(None),
                Race.day_number.isnot(None),
                Race.is_last_day.isnot(None),
                Race.race_number.isnot(None),
                Race.has_stabilizer.isnot(None),
                Race.before_info_temperature.isnot(None),
                Race.before_info_weather.isnot(None),
                Race.before_info_wind_speed.isnot(None),
                Race.before_info_wind_direction.isnot(None),
                Race.before_info_water_temperature.isnot(None),
                Race.before_info_wave_height.isnot(None),
            )
            .order_by(
                Race.date.asc(),
                Race.deadline.asc(),
            )
            .all()
        )

    for trifecta in [
        "2345-9-9",
        "2-1-9",
        "9-9-9",
        "1-9-9",
        "2-9-9",
        "3-9-9",
        "4-9-9",
        "5-9-9",
        "6-9-9",
    ]:
        first, second, third = trifecta.split("-")
        first = [1, 2, 3, 4, 5, 6] if first == "9" else [int(x) for x in first]
        second = [1, 2, 3, 4, 5, 6] if second == "9" else [int(x) for x in second]
        third = [1, 2, 3, 4, 5, 6] if third == "9" else [int(x) for x in third]
        for year in args.years:
            with open(
                os.path.join(os.getcwd(), "temp", f"analysis_{trifecta}_{year}.csv"),
                "w",
                newline="",
                encoding="utf-8",
            ) as f:
                writer = csv.writer(f, delimiter="\t")
                for ev in tqdm(range(75, 151), desc=f"{trifecta} {year}"):
                    row = []
                    for odds in [
                        (1.0, 50.0),
                        (50.0, 100.0),
                        (100.0, 200.0),
                        (200.0, 300.0),
                        (300.0, 400.0),
                        (400.0, 500.0),
                        (500.0, 1000.0),
                        (1000.0, 10000.0),
                    ]:
                        bet_race = 0
                        hit_race = 0
                        bet_money = 0
                        hit_money = 0
                        peak = 0
                        max_dd = 0
                        for offset in range(0, len(race_list_by_year[year]), BATCH_SIZE):
                            race_batch = race_list_by_year[year][offset : offset + BATCH_SIZE]
                            ticket_list = (
                                SESSION.query(Ticket)
                                .filter(
                                    Ticket.race_id.in_([race.id for race in race_batch]),
                                    Ticket.first.in_(first),
                                    Ticket.second.in_(second),
                                    Ticket.third.in_(third),
                                    Ticket.deadline_odds >= odds[0],
                                    Ticket.deadline_odds < odds[1],
                                    Ticket.deadline_odds_expected_value >= ev / 100,
                                )
                                .all()
                            )

                            tickets_by_race: dict[int, list[Ticket]] = {}
                            for ticket in ticket_list:
                                tickets_by_race.setdefault(ticket.race_id, []).append(ticket)

                            for race in race_batch:
                                race_ticket_list = tickets_by_race.get(race.id)
                                if race_ticket_list is not None:
                                    bet_race += 1
                                    for ticket in race_ticket_list:
                                        bet_money += 100
                                        if ticket.is_win == 1:
                                            hit_race += 1
                                            hit_money += round(100 * race.odds_trifecta)
                                    if hit_money - bet_money > peak:
                                        peak = hit_money - bet_money
                                    if hit_money - bet_money - peak < max_dd:
                                        max_dd = hit_money - bet_money - peak

                        hit_rate = round((hit_race / bet_race) * 100, 1) if bet_race > 0 else 0.0
                        roi = round((hit_money / bet_money) * 100, 1) if bet_money > 0 else 0.0

                        row.append(bet_race)
                        row.append(hit_race)
                        row.append(f"{hit_rate}%")
                        row.append(bet_money)
                        row.append(hit_money)
                        row.append(hit_money - bet_money)
                        row.append(f"{roi}%")
                        row.append(-max_dd)

                    writer.writerow(row)

        for odds in [
            (1.0, 100.0),
            (100.0, 400.0),
        ]:
            with open(
                os.path.join(os.getcwd(), "temp", f"analysis_{trifecta}_{odds[0]}-{odds[1]}.csv"),
                "w",
                newline="",
                encoding="utf-8",
            ) as f:
                writer = csv.writer(f, delimiter="\t")
                for ev in tqdm(range(75, 151), desc=f"{trifecta} {odds[0]:>5.1f}-{odds[1]:>5.1f}"):
                    row = []
                    for year in args.years:
                        bet_race = 0
                        hit_race = 0
                        bet_money = 0
                        hit_money = 0
                        peak = 0
                        max_dd = 0
                        for offset in range(0, len(race_list_by_year[year]), BATCH_SIZE):
                            race_batch = race_list_by_year[year][offset : offset + BATCH_SIZE]
                            ticket_list = (
                                SESSION.query(Ticket)
                                .filter(
                                    Ticket.race_id.in_([race.id for race in race_batch]),
                                    Ticket.first.in_(first),
                                    Ticket.second.in_(second),
                                    Ticket.third.in_(third),
                                    Ticket.deadline_odds >= odds[0],
                                    Ticket.deadline_odds < odds[1],
                                    Ticket.deadline_odds_expected_value >= ev / 100,
                                )
                                .all()
                            )

                            tickets_by_race: dict[int, list[Ticket]] = {}
                            for ticket in ticket_list:
                                tickets_by_race.setdefault(ticket.race_id, []).append(ticket)

                            for race in race_batch:
                                race_ticket_list = tickets_by_race.get(race.id)
                                if race_ticket_list is not None:
                                    bet_race += 1
                                    for ticket in race_ticket_list:
                                        bet_money += 100
                                        if ticket.is_win == 1:
                                            hit_race += 1
                                            hit_money += round(100 * race.odds_trifecta)
                                    if hit_money - bet_money > peak:
                                        peak = hit_money - bet_money
                                    if hit_money - bet_money - peak < max_dd:
                                        max_dd = hit_money - bet_money - peak

                        hit_rate = round((hit_race / bet_race) * 100, 1) if bet_race > 0 else 0.0
                        roi = round((hit_money / bet_money) * 100, 1) if bet_money > 0 else 0.0

                        row.append(bet_race)
                        row.append(hit_race)
                        row.append(f"{hit_rate}%")
                        row.append(bet_money)
                        row.append(hit_money)
                        row.append(hit_money - bet_money)
                        row.append(f"{roi}%")
                        row.append(-max_dd)

                    writer.writerow(row)


if __name__ == "__main__":
    main()
