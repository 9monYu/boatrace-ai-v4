import argparse
import csv
import os
from datetime import datetime

from constants import SESSION
from models import Race, Ticket


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
        .all()
    )

    for first_boat in [
        9,
        1,
        2,
        3,
        4,
        5,
        6,
    ]:
        with open(
            os.path.join(os.getcwd(), "temp", f"analysis{first_boat}_{args.start}_{args.end}.csv"),
            "w",
            newline="",
            encoding="utf-8",
        ) as f:
            writer = csv.writer(f, delimiter="\t")
            for expected_value in [
                0.80,
                0.85,
                0.90,
                0.95,
                1.00,
                1.05,
                1.10,
                1.15,
                1.20,
                1.25,
                1.30,
                1.35,
                1.40,
                1.45,
                1.50,
                1.55,
                1.60,
                1.65,
                1.70,
                1.75,
                1.80,
                1.85,
                1.90,
                1.95,
                2.00,
            ]:
                row = []
                for odds in [
                    (1.0, 20.0),
                    (20.0, 40.0),
                    (40.0, 60.0),
                    (60.0, 80.0),
                    (80.0, 100.0),
                    (100.0, 120.0),
                    (120.0, 140.0),
                    (140.0, 160.0),
                    (160.0, 180.0),
                    (180.0, 200.0),
                    (200.0, 220.0),
                    (220.0, 240.0),
                    (240.0, 260.0),
                    (260.0, 280.0),
                    (280.0, 300.0),
                ]:
                    bet_race = 0
                    hit_race = 0
                    bet_money = 0
                    hit_money = 0
                    peak = 0
                    max_dd = 0
                    for race in race_list:
                        conditions = [
                            Ticket.race_id == race.id,
                            Ticket.deadline_odds >= odds[0],
                            Ticket.deadline_odds < odds[1],
                            Ticket.expected_value >= expected_value,
                        ]
                        if first_boat in [1, 2, 3, 4, 5, 6]:
                            conditions.append(Ticket.first == first_boat)
                        ticket_list = SESSION.query(Ticket).filter(*conditions).all()
                        if ticket_list:
                            bet_race += 1
                            for ticket in ticket_list:
                                bet_money += 100
                                if ticket.is_hit == 1:
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

                    print("[rule]")
                    if first_boat in [1, 2, 3, 4, 5, 6]:
                        print(f"first boat    : {first_boat}")
                    print(f"odds          : {odds[0]} - {odds[1]}")
                    print(f"expected value: >={expected_value}")

                    print("\n[stats]")
                    print(f"bet race : {bet_race:,}")
                    print(f"hit race : {hit_race:,}")
                    print(f"hit rate : {hit_rate}%")
                    print(f"bet money: {bet_money:,}")
                    print(f"hit money: {hit_money:,}")
                    print(f"result   : {hit_money - bet_money:+,}")
                    print(f"roi      : {roi}%")
                    print(f"max dd   : {-max_dd:,}")
                    print("--\n\n")

                writer.writerow(row)


if __name__ == "__main__":
    main()
