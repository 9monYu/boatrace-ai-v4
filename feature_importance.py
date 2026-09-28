import os

import lightgbm
import pandas


def main():
    results: list[pandas.DataFrame] = []

    for file_name in os.listdir(os.path.join(os.getcwd(), "models")):
        if file_name.endswith(".txt"):
            model = lightgbm.Booster(model_file=os.path.join(os.getcwd(), "models", file_name))
            dataframe = pandas.DataFrame(
                {
                    "feature": model.feature_name(),
                    "gain": model.feature_importance(importance_type="gain"),
                    "split": model.feature_importance(importance_type="split"),
                }
            )
            dataframe["gain_percent"] = dataframe["gain"] / dataframe["gain"].sum() * 100
            dataframe = dataframe[["feature", "gain_percent", "gain", "split"]]
            results.append(dataframe)

    if results:
        summary = (
            pandas.concat(results)
            .groupby("feature", as_index=False)
            .mean()
            .sort_values("gain_percent", ascending=False)
        )
        summary["gain_percent"] = summary["gain_percent"].map(lambda x: f"{x:.4f}%")
        summary.to_csv(
            os.path.join(os.getcwd(), "temp", "feature_importance.tsv"),
            index=False,
            header=False,
            encoding="utf-8-sig",
            sep="\t",
        )


if __name__ == "__main__":
    main()
