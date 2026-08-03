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
    args = parser.parse_args()

    if os.path.exists(os.path.join(os.getcwd(), "dataset", f"{args.year}_eval.csv")):
        eval_df = pandas.read_csv(os.path.join(os.getcwd(), "dataset", f"{args.year}_eval.csv"), index_col=0)

        deltas_list = []
        for seed in range(SEED_COUNT):
            model = lightgbm.Booster(model_file=os.path.join(os.getcwd(), "models", f"{args.year}_{seed + 1:02d}.txt"))
            deltas = model.predict(eval_df, raw_score=True)
            deltas_list.append(deltas)

        for race_index, race_id in tqdm(enumerate(eval_df.index), total=len(eval_df)):
            ticket_list = (
                SESSION.query(Ticket)
                .filter(
                    Ticket.race_id == race_id,
                    Ticket.deadline_odds.isnot(None),
                    Ticket.deadline_odds_market_share.isnot(None),
                )
                .all()
            )

            ticket_by_trifecta = {(ticket.first, ticket.second, ticket.third): ticket for ticket in ticket_list}

            sum_exp_score = 0.0
            for trifecta_index, trifecta in enumerate(TRIFECTA_LIST):
                ticket = ticket_by_trifecta[trifecta]
                ticket.delta = statistics.mean(deltas[race_index][trifecta_index] for deltas in deltas_list)
                sum_exp_score += ticket.deadline_odds_market_share * math.exp(ticket.delta)
                # sum_exp_score += math.exp(math.log(ticket.deadline_odds_market_share) + ticket.delta)

            for trifecta in TRIFECTA_LIST:
                ticket = ticket_by_trifecta[trifecta]
                ticket.deadline_odds_probability = (
                    ticket.deadline_odds_market_share * math.exp(ticket.delta)
                ) / sum_exp_score
                ticket.deadline_odds_expected_value = ticket.deadline_odds_probability * ticket.deadline_odds

        SESSION.commit()


if __name__ == "__main__":
    main()
