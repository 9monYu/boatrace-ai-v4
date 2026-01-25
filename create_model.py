import argparse
import os
from datetime import datetime

import lightgbm
import numpy
import pandas

from constants import CATEGORICAL_FEATURE_LIST, PARAMETERS, SEED_COUNT, SESSION, TRIFECTA_LIST
from models import Ticket


def main():
    start = datetime.now()

    parser = argparse.ArgumentParser()
    parser.add_argument("year", type=int)
    parser.add_argument("period", type=int, choices=[1, 2])
    args = parser.parse_args()

    if os.path.exists(os.path.join(os.getcwd(), "dataset", f"{args.year}_{args.period}_train.csv")) and os.path.exists(
        os.path.join(os.getcwd(), "dataset", f"{args.year}_{args.period}_valid.csv")
    ):
        # train
        train_df = pandas.read_csv(
            os.path.join(os.getcwd(), "dataset", f"{args.year}_{args.period}_train.csv"), index_col=0
        )
        x_train = train_df.drop(["result"], axis=1)
        y_train = train_df["result"].astype(int)

        train_market_share_list = []
        for race_id in x_train.index:
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
            train_market_share_list.append([ticket_by_trifecta[trifecta].market_share for trifecta in TRIFECTA_LIST])

        train_set = lightgbm.Dataset(
            x_train,
            label=y_train,
            categorical_feature=CATEGORICAL_FEATURE_LIST,
            init_score=numpy.log(numpy.array(train_market_share_list, dtype=numpy.float32)),
        )

        # valid
        valid_df = pandas.read_csv(
            os.path.join(os.getcwd(), "dataset", f"{args.year}_{args.period}_valid.csv"), index_col=0
        )
        x_valid = valid_df.drop(["result"], axis=1)
        y_valid = valid_df["result"].astype(int)

        valid_market_share_list = []
        for race_id in x_valid.index:
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
            valid_market_share_list.append([ticket_by_trifecta[trifecta].market_share for trifecta in TRIFECTA_LIST])

        valid_set = lightgbm.Dataset(
            x_valid,
            label=y_valid,
            categorical_feature=CATEGORICAL_FEATURE_LIST,
            init_score=numpy.log(numpy.array(valid_market_share_list, dtype=numpy.float32)),
        )

        # train_all = train + valid
        train_set_all = lightgbm.Dataset(
            pandas.concat([x_train, x_valid], axis=0),
            label=pandas.concat([y_train, y_valid], axis=0),
            categorical_feature=CATEGORICAL_FEATURE_LIST,
            init_score=numpy.log(numpy.array(train_market_share_list + valid_market_share_list, dtype=numpy.float32)),
        )

        for seed in range(SEED_COUNT):
            params = PARAMETERS.copy()
            params["seed"] = seed
            params["feature_fraction_seed"] = seed
            params["bagging_seed"] = seed

            temp_model = lightgbm.train(
                params=params,
                train_set=train_set,
                valid_sets=[valid_set],
                valid_names=["valid"],
                num_boost_round=10000,
                callbacks=[lightgbm.early_stopping(200)],
            )

            model = lightgbm.train(
                params=params,
                train_set=train_set_all,
                num_boost_round=temp_model.best_iteration,
            )

            model.save_model(os.path.join(os.getcwd(), "models", f"{args.year}_{args.period}_{seed + 1:02d}.txt"))

    print(f"start: {start.strftime("%Y-%m-%d %H:%M:%S")}")
    print(f"end  : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}")


if __name__ == "__main__":
    main()
