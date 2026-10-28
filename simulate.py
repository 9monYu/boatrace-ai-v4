import argparse
import csv
import os
import statistics
from datetime import datetime

from sqlalchemy import select, tuple_
from tqdm import tqdm

from database import Session
from models import Race, Ticket


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("start_date", type=int)
    parser.add_argument("end_date", type=int)
    args = parser.parse_args()

    try:
        datetime.strptime(str(args.start_date), "%Y%m%d")
        datetime.strptime(str(args.end_date), "%Y%m%d")
    except ValueError:
        return

    with open(
        os.path.join(os.getcwd(), "temp", f"simulation_{args.start_date}_{args.end_date}.tsv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.writer(f, delimiter="\t")
        race_list = Session.scalars(
            select(Race)
            .where(
                Race.is_cancel == 0,
                Race.date >= args.start_date,
                Race.date <= args.end_date,
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
            )
            .order_by(Race.date.asc(), Race.deadline.asc())
        ).all()
        bet_race = 0
        hit_race = 0
        bet_money = 0
        hit_money = 0
        peak = 0
        max_dd = 0
        bet_odds_list = []
        hit_odds_list = []
        progress_bar = tqdm(race_list)
        for index, race in enumerate(progress_bar):
            if index % 100 == 0:
                progress_bar.set_description(f"{race.id}")
            ticket_list = Session.scalars(
                select(Ticket).where(
                    Ticket.race_id == race.id,
                    # tuple_(Ticket.first, Ticket.second).in_(
                    #     [
                    #         (2, 1),
                    #         (2, 3),
                    #         (2, 4),
                    #         (3, 1),
                    #         (3, 2),
                    #         (4, 3),
                    #         (4, 5),
                    #         (4, 6),
                    #         (5, 1),
                    #         (5, 2),
                    #     ]
                    # ),
                    # Ticket.deadline_odds >= 100.0,
                    # Ticket.deadline_odds < 400.0,
                    Ticket.deadline_odds_expected_value >= 1.00,
                    Ticket.deadline_odds_expected_value < 2.00,
                )
            ).all()
            if ticket_list:
                bet_race += 1
                for ticket in ticket_list:
                    bet_money += 100
                    bet_odds_list.append(ticket.deadline_odds)
                    row = []
                    row.append(race.id)
                    row.append(datetime.strptime(str(race.date), "%Y%m%d").strftime("%Y/%m/%d"))
                    row.append(race.grade)
                    row.append(race.venue)
                    row.append(f"{ticket.first}-{ticket.second}-{ticket.third}")
                    row.append(ticket.deadline_odds)
                    row.append(100)
                    if ticket.is_win == 1:
                        hit_race += 1
                        hit_money += round(100 * race.odds_trifecta)
                        hit_odds_list.append(race.odds_trifecta)
                        row.append(round(100 * race.odds_trifecta))
                    else:
                        row.append(0)
                    writer.writerow(row)
                if hit_money - bet_money > peak:
                    peak = hit_money - bet_money
                if hit_money - bet_money - peak < max_dd:
                    max_dd = hit_money - bet_money - peak

        hit_rate = round((hit_race / bet_race) * 100, 1) if bet_race > 0 else 0.0
        roi = round((hit_money / bet_money) * 100, 1) if bet_money > 0 else 0.0

        print("\n[stats]")
        print(f"bet race : {bet_race:,}")
        print(f"hit race : {hit_race:,}")
        print(f"hit rate : {hit_rate}%")
        print(f"bet money: {bet_money:,}")
        print(f"hit money: {hit_money:,}")
        print(f"result   : {hit_money - bet_money:+,}")
        print(f"roi      : {roi}%")
        print(f"max dd   : {-max_dd:,}")

        if bet_odds_list:
            print("\n[bet odds]")
            print(f"mean     : {round(statistics.mean(bet_odds_list), 1):,}")
            print(f"median   : {round(statistics.median(bet_odds_list), 1):,}")
            print(f"maximum  : {round(max(bet_odds_list), 1):,}")
            print(f"minimum  : {round(min(bet_odds_list), 1):,}")

        if hit_odds_list:
            print("\n[hit odds]")
            print(f"mean     : {round(statistics.mean(hit_odds_list), 1):,}")
            print(f"median   : {round(statistics.median(hit_odds_list), 1):,}")
            print(f"maximum  : {round(max(hit_odds_list), 1):,}")
            print(f"minimum  : {round(min(hit_odds_list), 1):,}")


if __name__ == "__main__":
    main()
