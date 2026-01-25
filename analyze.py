import argparse
import csv
import os
from datetime import datetime

from constants import SESSION
from models import Race, Ticket


def main():
    start = datetime.now()

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

    for first_boat in [1, 2, 3, 4, 5, 6]:
        with open(
            os.path.join(os.getcwd(), "temp", f"analysis{first_boat}_{args.start}_{args.end}.csv"),
            "w",
            newline="",
            encoding="utf-8",
        ) as f:
            writer = csv.writer(f, delimiter="\t")
            for funanyu_index in range(101, 151):
                row = []
                for market_share in [
                    0.0300,  # 3.00% ≒ 25.0
                    0.0200,  # 2.00% ≒ 37.5
                    0.0150,  # 1.50% ≒ 50.0
                    0.0100,  # 1.00% ≒ 75.0
                    0.0075,  # 0.75% ≒ 100.0
                ]:
                    bet_race = 0
                    hit_race = 0
                    bet_money = 0
                    hit_money = 0
                    peak = 0
                    max_dd = 0
                    for race in race_list:
                        ticket_list = (
                            SESSION.query(Ticket)
                            .filter(
                                Ticket.race_id == race.id,
                                Ticket.first == first_boat,
                                Ticket.market_share >= market_share,
                                Ticket.funanyu_index >= funanyu_index,
                            )
                            .all()
                        )
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
                    print(f"first boat   : {first_boat}")
                    print(f"market share : >={market_share}")
                    print(f"funanyu index: >={funanyu_index}")

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

    print(f"start: {start.strftime("%Y-%m-%d %H:%M:%S")}")
    print(f"end  : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}")


if __name__ == "__main__":
    main()
