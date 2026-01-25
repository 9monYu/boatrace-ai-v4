import argparse
import math
import os
import statistics

import lightgbm
import pandas
from tqdm import tqdm

from constants import SEED_COUNT, SESSION, TRIFECTA_LIST
from models import Ticket


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("year", type=int)
    parser.add_argument("period", type=int, choices=[1, 2])
    args = parser.parse_args()

    if os.path.exists(os.path.join(os.getcwd(), "dataset", f"{args.year}_{args.period}_test.csv")):
        test_df = pandas.read_csv(
            os.path.join(os.getcwd(), "dataset", f"{args.year}_{args.period}_test.csv"), index_col=0
        )

        deltas_list = []
        for seed in range(SEED_COUNT):
            model = lightgbm.Booster(
                model_file=os.path.join(os.getcwd(), "models", f"{args.year}_{args.period}_{seed + 1:02d}.txt")
            )
            deltas = model.predict(test_df, raw_score=True)
            deltas_list.append(deltas)

        for race_index, race_id in tqdm(enumerate(test_df.index), total=len(test_df)):
            ticket_list = (
                SESSION.query(Ticket)
                .filter(
                    Ticket.race_id == race_id,
                    Ticket.deadline_odds.isnot(None),
                    Ticket.market_share.isnot(None),
                )
                .all()
            )

            ticket_by_trifecta = {(ticket.first, ticket.second, ticket.third): ticket for ticket in ticket_list}

            sum_exp_score = 0.0
            for trifecta_index, trifecta in enumerate(TRIFECTA_LIST):
                ticket = ticket_by_trifecta[trifecta]
                ticket.delta = statistics.mean(deltas[race_index][trifecta_index] for deltas in deltas_list)
                sum_exp_score += ticket.market_share * math.exp(ticket.delta)
                # sum_exp_score += math.exp(math.log(ticket.market_share) + ticket.delta)

            for trifecta in TRIFECTA_LIST:
                ticket = ticket_by_trifecta[trifecta]
                ticket.model_share = (ticket.market_share * math.exp(ticket.delta)) / sum_exp_score
                ticket.funanyu_index = round((ticket.model_share / ticket.market_share) * 100, 2)

        SESSION.commit()


if __name__ == "__main__":
    main()
