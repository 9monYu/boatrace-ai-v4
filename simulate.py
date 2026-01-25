import argparse
import csv
import os
import statistics
from datetime import datetime

from sqlalchemy import and_, or_
from tqdm import tqdm

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

    with open(
        os.path.join(os.getcwd(), "temp", f"simulation_{args.start}_{args.end}.csv"), "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.writer(f, delimiter="\t")
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
            .order_by(Race.date.asc(), Race.deadline.asc())
            .all()
        )
        bet_race = 0
        hit_race = 0
        bet_money = 0
        hit_money = 0
        peak = 0
        max_dd = 0
        bet_odds_list = []
        hit_odds_list = []
        for race in tqdm(race_list):
            ticket_list = (
                SESSION.query(Ticket)
                .filter(
                    Ticket.race_id == race.id,
                    or_(
                        and_(
                            Ticket.first == 1,
                            Ticket.market_share >= 0.0075,
                            Ticket.funanyu_index >= 135,
                        ),
                        and_(
                            Ticket.first == 2,
                            Ticket.market_share >= 0.0075,
                            Ticket.funanyu_index >= 135,
                        ),
                        and_(
                            Ticket.first == 3,
                            Ticket.market_share >= 0.0075,
                            Ticket.funanyu_index >= 135,
                        ),
                        and_(
                            Ticket.first == 4,
                            Ticket.market_share >= 0.0075,
                            Ticket.funanyu_index >= 135,
                        ),
                        and_(
                            Ticket.first == 5,
                            Ticket.market_share >= 0.0075,
                            Ticket.funanyu_index >= 135,
                        ),
                        and_(
                            Ticket.first == 6,
                            Ticket.market_share >= 0.0075,
                            Ticket.funanyu_index >= 135,
                        ),
                    ),
                )
                .all()
            )
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
                    if ticket.is_hit == 1:
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

        print("\n[bet odds]")
        print(f"mean     : {round(statistics.mean(bet_odds_list), 1):,}")
        print(f"median   : {round(statistics.median(bet_odds_list), 1):,}")
        print(f"maximum  : {round(max(bet_odds_list), 1):,}")
        print(f"minimum  : {round(min(bet_odds_list), 1):,}")

        print("\n[hit odds]")
        print(f"mean     : {round(statistics.mean(hit_odds_list), 1):,}")
        print(f"median   : {round(statistics.median(hit_odds_list), 1):,}")
        print(f"maximum  : {round(max(hit_odds_list), 1):,}")
        print(f"minimum  : {round(min(hit_odds_list), 1):,}")


if __name__ == "__main__":
    main()
