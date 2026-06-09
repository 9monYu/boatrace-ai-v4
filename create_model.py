import argparse
import os

import lightgbm
import numpy
import pandas

from constants import CATEGORICAL_FEATURE_LIST, PARAMETERS, SEED_COUNT, SESSION, TRIFECTA_LIST
from models import Ticket


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("year", type=int)
    args = parser.parse_args()

    if os.path.exists(os.path.join(os.getcwd(), "dataset", f"{args.year}_train.csv")):
        train_df = pandas.read_csv(os.path.join(os.getcwd(), "dataset", f"{args.year}_train.csv"), index_col=0)
        x_train = train_df.drop(["result"], axis=1)
        y_train = train_df["result"].astype(int)

        train_market_share_list = []
        for race_id in x_train.index:
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
            train_market_share_list.append([ticket_by_trifecta[trifecta].deadline_odds_market_share for trifecta in TRIFECTA_LIST])

        train_set = lightgbm.Dataset(
            x_train,
            label=y_train,
            categorical_feature=CATEGORICAL_FEATURE_LIST,
            init_score=numpy.log(numpy.array(train_market_share_list, dtype=numpy.float32)),
        )

        for seed in range(SEED_COUNT):
            params = PARAMETERS.copy()
            params["seed"] = seed
            params["feature_fraction_seed"] = seed
            params["bagging_seed"] = seed

            model = lightgbm.train(
                params=params,
                train_set=train_set,
                num_boost_round=5000,
            )

            model.save_model(os.path.join(os.getcwd(), "models", f"{args.year}_{seed + 1:02d}.txt"))


if __name__ == "__main__":
    main()
