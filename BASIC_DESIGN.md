# 📄 設計書

## 🧱 基本

- Python
- LightGBM
- 予測対象：ボートレース 3 連単 120 通り（120 クラス分類）
- データ形式：1 レース 1 行
- 目的：年間回収率 100%超え

## 🧠 学習

予測年ごとに、過去 5 年間のレースを使って学習し、seed 違いで 5 つのモデルを作成。

| 予測年 | 学習期間   |
| ------ | ---------- |
| 2023   | 2018〜2022 |
| 2024   | 2019〜2023 |
| 2025   | 2020〜2024 |
| 2026   | 2021〜2025 |

```text
market_share = (1 / odds) / sum(1 / odds)

init_score = log(market_share)
```

※`market_share` はレース内 120 通りで正規化。

LightGBM の `raw_score` を `delta` とする。

## 📊 確率・期待値

```text
score = log(market_share) + mean(delta_1, ..., delta_5)

probability = softmax(score)

expected_value = probability * odds
```

## 🎯 購入条件

オッズ帯：

- 1.0〜49.9
- 50.0〜99.9
- 100.0〜199.9
- 200.0〜399.9

※400 倍以上は対象外。

各オッズ帯で EV 0.75〜1.50 程度を 0.01 刻みで検証。

EV の上昇に伴い、回収率も上昇するゾーンを確認。

運用対象年の直前 3 年間すべてで回収率 100%超えとなるゾーンから、各オッズ帯の EV 閾値を決定。

以下を満たす買い目を購入対象とする。

```text
expected_value >= EV閾値
```

## 📝 補足

過去の学習・検証では締切時オッズを使用。

本番運用では締切直前オッズを使用。

過去レースは締切時オッズしか取得できないため、この差は前提として許容する。

## 🧩 特徴量

| 変数名                                                          | 説明                                                       |
| --------------------------------------------------------------- | ---------------------------------------------------------- |
| `grade`                                                         | グレード                                                   |
| `month`                                                         | 月                                                         |
| `weekday`                                                       | 曜日                                                       |
| `period_progress_rate`                                          | 級別審査期間進行率                                         |
| `venue`                                                         | 場                                                         |
| `venue_normal_entry_course1_1st_rate`                           | 場別 枠なり 1コース 1着率                                  |
| `venue_normal_entry_course1_2nd_rate`                           | 場別 枠なり 1コース 2着率                                  |
| `venue_normal_entry_course1_3rd_rate`                           | 場別 枠なり 1コース 3着率                                  |
| `venue_normal_entry_course2_1st_rate`                           | 場別 枠なり 2コース 1着率                                  |
| `venue_normal_entry_course2_2nd_rate`                           | 場別 枠なり 2コース 2着率                                  |
| `venue_normal_entry_course2_3rd_rate`                           | 場別 枠なり 2コース 3着率                                  |
| `venue_normal_entry_course3_1st_rate`                           | 場別 枠なり 3コース 1着率                                  |
| `venue_normal_entry_course3_2nd_rate`                           | 場別 枠なり 3コース 2着率                                  |
| `venue_normal_entry_course3_3rd_rate`                           | 場別 枠なり 3コース 3着率                                  |
| `venue_normal_entry_course4_1st_rate`                           | 場別 枠なり 4コース 1着率                                  |
| `venue_normal_entry_course4_2nd_rate`                           | 場別 枠なり 4コース 2着率                                  |
| `venue_normal_entry_course4_3rd_rate`                           | 場別 枠なり 4コース 3着率                                  |
| `venue_normal_entry_course5_1st_rate`                           | 場別 枠なり 5コース 1着率                                  |
| `venue_normal_entry_course5_2nd_rate`                           | 場別 枠なり 5コース 2着率                                  |
| `venue_normal_entry_course5_3rd_rate`                           | 場別 枠なり 5コース 3着率                                  |
| `venue_normal_entry_course6_1st_rate`                           | 場別 枠なり 6コース 1着率                                  |
| `venue_normal_entry_course6_2nd_rate`                           | 場別 枠なり 6コース 2着率                                  |
| `venue_normal_entry_course6_3rd_rate`                           | 場別 枠なり 6コース 3着率                                  |
| `day_number`                                                    | ｎ日目                                                     |
| `is_last_day`                                                   | 最終日                                                     |
| `race_number`                                                   | ｎレース目                                                 |
| `has_stabilizer`                                                | 安定板                                                     |
| `before_info_temperature`                                       | 直前情報 気温                                              |
| `before_info_weather`                                           | 直前情報 天気                                              |
| `before_info_wind_sin`                                          | 直前情報 風 sin                                            |
| `before_info_wind_cos`                                          | 直前情報 風 cos                                            |
| `before_info_water_temperature`                                 | 直前情報 水温                                              |
| `before_info_wave_height`                                       | 直前情報 波高                                              |
| `stabilizer_x_wind_sin`                                         | 安定板 × 風 sin                                            |
| `stabilizer_x_wind_cos`                                         | 安定板 × 風 cos                                            |
| `stabilizer_x_wave_height`                                      | 安定板 × 波高                                              |
| `female_count`                                                  | 女子レーサー数                                             |
| `boat1_racer_class`                                             | 1号艇 級                                                   |
| `boat1_sex`                                                     | 1号艇 性別                                                 |
| `boat1_age`                                                     | 1号艇 年齢                                                 |
| `boat1_flying_late`                                             | 1号艇 フライング + 出遅れ                                  |
| `boat1_average_start_timing`                                    | 1号艇 平均スタートタイミング                               |
| `boat1_average_start_timing_z_score`                            | 1号艇 平均スタートタイミング レース内Zスコア               |
| `boat1_all_venue_win_rate`                                      | 1号艇 全国勝率                                             |
| `boat1_all_venue_win_rate_z_score`                              | 1号艇 全国勝率 レース内Zスコア                             |
| `boat1_all_venue_top2_rate`                                     | 1号艇 全国2連対率                                          |
| `boat1_this_venue_win_rate`                                     | 1号艇 当地勝率                                             |
| `boat1_this_venue_win_rate_z_score`                             | 1号艇 当地勝率 レース内Zスコア                             |
| `boat1_this_venue_top2_rate`                                    | 1号艇 当地2連対率                                          |
| `boat1_motor_top2_rate`                                         | 1号艇 モーター2連対率                                      |
| `boat1_motor_top2_rate_z_score`                                 | 1号艇 モーター2連対率 レース内Zスコア                      |
| `boat1_before_info_start_timing`                                | 1号艇 直前情報 スタートタイミング                          |
| `boat1_before_info_start_timing_abs_z_score`                    | 1号艇 直前情報 スタートタイミング絶対値 レース内Zスコア    |
| `boat1_before_info_adjusted_weight`                             | 1号艇 直前情報 調整体重                                    |
| `boat1_before_info_total_weight`                                | 1号艇 直前情報 合計体重                                    |
| `boat1_before_info_display_time`                                | 1号艇 直前情報 展示タイム                                  |
| `boat1_before_info_display_time_z_score`                        | 1号艇 直前情報 展示タイム レース内Zスコア                  |
| `boat1_before_info_tilt`                                        | 1号艇 直前情報 チルト                                      |
| `boat1_course1_average_start_timing`                            | 1号艇 1コース 平均スタートタイミング                       |
| `boat1_course1_average_start_rank`                              | 1号艇 1コース 平均スタート順位                             |
| `boat1_course1_1st_rate`                                        | 1号艇 1コース 1着率                                        |
| `boat1_course1_2nd_rate`                                        | 1号艇 1コース 2着率                                        |
| `boat1_course1_3rd_rate`                                        | 1号艇 1コース 3着率                                        |
| `boat1_last5_1st_rate`                                          | 1号艇 直近5走 1着率                                        |
| `boat1_last5_2nd_rate`                                          | 1号艇 直近5走 2着率                                        |
| `boat1_last5_3rd_rate`                                          | 1号艇 直近5走 3着率                                        |
| `boat1_last5_average_rank`                                      | 1号艇 直近5走 平均着順                                     |
| `boat1_last5_average_start_timing`                              | 1号艇 直近5走 平均スタートタイミング                       |
| `boat1_last5_start_timing_std`                                  | 1号艇 直近5走 スタートタイミング標準偏差                   |
| `boat1_last10_1st_rate`                                         | 1号艇 直近10走 1着率                                       |
| `boat1_last10_2nd_rate`                                         | 1号艇 直近10走 2着率                                       |
| `boat1_last10_3rd_rate`                                         | 1号艇 直近10走 3着率                                       |
| `boat1_last10_average_rank`                                     | 1号艇 直近10走 平均着順                                    |
| `boat1_last10_average_start_timing`                             | 1号艇 直近10走 平均スタートタイミング                      |
| `boat1_last10_start_timing_std`                                 | 1号艇 直近10走 スタートタイミング標準偏差                  |
| `boat2_racer_class`                                             | 2号艇 級                                                   |
| `boat2_sex`                                                     | 2号艇 性別                                                 |
| `boat2_age`                                                     | 2号艇 年齢                                                 |
| `boat2_flying_late`                                             | 2号艇 フライング + 出遅れ                                  |
| `boat2_average_start_timing`                                    | 2号艇 平均スタートタイミング                               |
| `boat2_average_start_timing_z_score`                            | 2号艇 平均スタートタイミング レース内Zスコア               |
| `boat2_all_venue_win_rate`                                      | 2号艇 全国勝率                                             |
| `boat2_all_venue_win_rate_z_score`                              | 2号艇 全国勝率 レース内Zスコア                             |
| `boat2_all_venue_top2_rate`                                     | 2号艇 全国2連対率                                          |
| `boat2_this_venue_win_rate`                                     | 2号艇 当地勝率                                             |
| `boat2_this_venue_win_rate_z_score`                             | 2号艇 当地勝率 レース内Zスコア                             |
| `boat2_this_venue_top2_rate`                                    | 2号艇 当地2連対率                                          |
| `boat2_motor_top2_rate`                                         | 2号艇 モーター2連対率                                      |
| `boat2_motor_top2_rate_z_score`                                 | 2号艇 モーター2連対率 レース内Zスコア                      |
| `boat2_before_info_start_timing`                                | 2号艇 直前情報 スタートタイミング                          |
| `boat2_before_info_start_timing_abs_z_score`                    | 2号艇 直前情報 スタートタイミング絶対値 レース内Zスコア    |
| `boat2_before_info_adjusted_weight`                             | 2号艇 直前情報 調整体重                                    |
| `boat2_before_info_total_weight`                                | 2号艇 直前情報 合計体重                                    |
| `boat2_before_info_display_time`                                | 2号艇 直前情報 展示タイム                                  |
| `boat2_before_info_display_time_z_score`                        | 2号艇 直前情報 展示タイム レース内Zスコア                  |
| `boat2_before_info_tilt`                                        | 2号艇 直前情報 チルト                                      |
| `boat2_course2_average_start_timing`                            | 2号艇 2コース 平均スタートタイミング                       |
| `boat2_course2_average_start_rank`                              | 2号艇 2コース 平均スタート順位                             |
| `boat2_course2_1st_rate`                                        | 2号艇 2コース 1着率                                        |
| `boat2_course2_2nd_rate`                                        | 2号艇 2コース 2着率                                        |
| `boat2_course2_3rd_rate`                                        | 2号艇 2コース 3着率                                        |
| `boat2_last5_1st_rate`                                          | 2号艇 直近5走 1着率                                        |
| `boat2_last5_2nd_rate`                                          | 2号艇 直近5走 2着率                                        |
| `boat2_last5_3rd_rate`                                          | 2号艇 直近5走 3着率                                        |
| `boat2_last5_average_rank`                                      | 2号艇 直近5走 平均着順                                     |
| `boat2_last5_average_start_timing`                              | 2号艇 直近5走 平均スタートタイミング                       |
| `boat2_last5_start_timing_std`                                  | 2号艇 直近5走 スタートタイミング標準偏差                   |
| `boat2_last10_1st_rate`                                         | 2号艇 直近10走 1着率                                       |
| `boat2_last10_2nd_rate`                                         | 2号艇 直近10走 2着率                                       |
| `boat2_last10_3rd_rate`                                         | 2号艇 直近10走 3着率                                       |
| `boat2_last10_average_rank`                                     | 2号艇 直近10走 平均着順                                    |
| `boat2_last10_average_start_timing`                             | 2号艇 直近10走 平均スタートタイミング                      |
| `boat2_last10_start_timing_std`                                 | 2号艇 直近10走 スタートタイミング標準偏差                  |
| `boat3_racer_class`                                             | 3号艇 級                                                   |
| `boat3_sex`                                                     | 3号艇 性別                                                 |
| `boat3_age`                                                     | 3号艇 年齢                                                 |
| `boat3_flying_late`                                             | 3号艇 フライング + 出遅れ                                  |
| `boat3_average_start_timing`                                    | 3号艇 平均スタートタイミング                               |
| `boat3_average_start_timing_z_score`                            | 3号艇 平均スタートタイミング レース内Zスコア               |
| `boat3_all_venue_win_rate`                                      | 3号艇 全国勝率                                             |
| `boat3_all_venue_win_rate_z_score`                              | 3号艇 全国勝率 レース内Zスコア                             |
| `boat3_all_venue_top2_rate`                                     | 3号艇 全国2連対率                                          |
| `boat3_this_venue_win_rate`                                     | 3号艇 当地勝率                                             |
| `boat3_this_venue_win_rate_z_score`                             | 3号艇 当地勝率 レース内Zスコア                             |
| `boat3_this_venue_top2_rate`                                    | 3号艇 当地2連対率                                          |
| `boat3_motor_top2_rate`                                         | 3号艇 モーター2連対率                                      |
| `boat3_motor_top2_rate_z_score`                                 | 3号艇 モーター2連対率 レース内Zスコア                      |
| `boat3_before_info_start_timing`                                | 3号艇 直前情報 スタートタイミング                          |
| `boat3_before_info_start_timing_abs_z_score`                    | 3号艇 直前情報 スタートタイミング絶対値 レース内Zスコア    |
| `boat3_before_info_adjusted_weight`                             | 3号艇 直前情報 調整体重                                    |
| `boat3_before_info_total_weight`                                | 3号艇 直前情報 合計体重                                    |
| `boat3_before_info_display_time`                                | 3号艇 直前情報 展示タイム                                  |
| `boat3_before_info_display_time_z_score`                        | 3号艇 直前情報 展示タイム レース内Zスコア                  |
| `boat3_before_info_tilt`                                        | 3号艇 直前情報 チルト                                      |
| `boat3_course3_average_start_timing`                            | 3号艇 3コース 平均スタートタイミング                       |
| `boat3_course3_average_start_rank`                              | 3号艇 3コース 平均スタート順位                             |
| `boat3_course3_1st_rate`                                        | 3号艇 3コース 1着率                                        |
| `boat3_course3_2nd_rate`                                        | 3号艇 3コース 2着率                                        |
| `boat3_course3_3rd_rate`                                        | 3号艇 3コース 3着率                                        |
| `boat3_last5_1st_rate`                                          | 3号艇 直近5走 1着率                                        |
| `boat3_last5_2nd_rate`                                          | 3号艇 直近5走 2着率                                        |
| `boat3_last5_3rd_rate`                                          | 3号艇 直近5走 3着率                                        |
| `boat3_last5_average_rank`                                      | 3号艇 直近5走 平均着順                                     |
| `boat3_last5_average_start_timing`                              | 3号艇 直近5走 平均スタートタイミング                       |
| `boat3_last5_start_timing_std`                                  | 3号艇 直近5走 スタートタイミング標準偏差                   |
| `boat3_last10_1st_rate`                                         | 3号艇 直近10走 1着率                                       |
| `boat3_last10_2nd_rate`                                         | 3号艇 直近10走 2着率                                       |
| `boat3_last10_3rd_rate`                                         | 3号艇 直近10走 3着率                                       |
| `boat3_last10_average_rank`                                     | 3号艇 直近10走 平均着順                                    |
| `boat3_last10_average_start_timing`                             | 3号艇 直近10走 平均スタートタイミング                      |
| `boat3_last10_start_timing_std`                                 | 3号艇 直近10走 スタートタイミング標準偏差                  |
| `boat4_racer_class`                                             | 4号艇 級                                                   |
| `boat4_sex`                                                     | 4号艇 性別                                                 |
| `boat4_age`                                                     | 4号艇 年齢                                                 |
| `boat4_flying_late`                                             | 4号艇 フライング + 出遅れ                                  |
| `boat4_average_start_timing`                                    | 4号艇 平均スタートタイミング                               |
| `boat4_average_start_timing_z_score`                            | 4号艇 平均スタートタイミング レース内Zスコア               |
| `boat4_all_venue_win_rate`                                      | 4号艇 全国勝率                                             |
| `boat4_all_venue_win_rate_z_score`                              | 4号艇 全国勝率 レース内Zスコア                             |
| `boat4_all_venue_top2_rate`                                     | 4号艇 全国2連対率                                          |
| `boat4_this_venue_win_rate`                                     | 4号艇 当地勝率                                             |
| `boat4_this_venue_win_rate_z_score`                             | 4号艇 当地勝率 レース内Zスコア                             |
| `boat4_this_venue_top2_rate`                                    | 4号艇 当地2連対率                                          |
| `boat4_motor_top2_rate`                                         | 4号艇 モーター2連対率                                      |
| `boat4_motor_top2_rate_z_score`                                 | 4号艇 モーター2連対率 レース内Zスコア                      |
| `boat4_before_info_start_timing`                                | 4号艇 直前情報 スタートタイミング                          |
| `boat4_before_info_start_timing_abs_z_score`                    | 4号艇 直前情報 スタートタイミング絶対値 レース内Zスコア    |
| `boat4_before_info_adjusted_weight`                             | 4号艇 直前情報 調整体重                                    |
| `boat4_before_info_total_weight`                                | 4号艇 直前情報 合計体重                                    |
| `boat4_before_info_display_time`                                | 4号艇 直前情報 展示タイム                                  |
| `boat4_before_info_display_time_z_score`                        | 4号艇 直前情報 展示タイム レース内Zスコア                  |
| `boat4_before_info_tilt`                                        | 4号艇 直前情報 チルト                                      |
| `boat4_course4_average_start_timing`                            | 4号艇 4コース 平均スタートタイミング                       |
| `boat4_course4_average_start_rank`                              | 4号艇 4コース 平均スタート順位                             |
| `boat4_course4_1st_rate`                                        | 4号艇 4コース 1着率                                        |
| `boat4_course4_2nd_rate`                                        | 4号艇 4コース 2着率                                        |
| `boat4_course4_3rd_rate`                                        | 4号艇 4コース 3着率                                        |
| `boat4_last5_1st_rate`                                          | 4号艇 直近5走 1着率                                        |
| `boat4_last5_2nd_rate`                                          | 4号艇 直近5走 2着率                                        |
| `boat4_last5_3rd_rate`                                          | 4号艇 直近5走 3着率                                        |
| `boat4_last5_average_rank`                                      | 4号艇 直近5走 平均着順                                     |
| `boat4_last5_average_start_timing`                              | 4号艇 直近5走 平均スタートタイミング                       |
| `boat4_last5_start_timing_std`                                  | 4号艇 直近5走 スタートタイミング標準偏差                   |
| `boat4_last10_1st_rate`                                         | 4号艇 直近10走 1着率                                       |
| `boat4_last10_2nd_rate`                                         | 4号艇 直近10走 2着率                                       |
| `boat4_last10_3rd_rate`                                         | 4号艇 直近10走 3着率                                       |
| `boat4_last10_average_rank`                                     | 4号艇 直近10走 平均着順                                    |
| `boat4_last10_average_start_timing`                             | 4号艇 直近10走 平均スタートタイミング                      |
| `boat4_last10_start_timing_std`                                 | 4号艇 直近10走 スタートタイミング標準偏差                  |
| `boat5_racer_class`                                             | 5号艇 級                                                   |
| `boat5_sex`                                                     | 5号艇 性別                                                 |
| `boat5_age`                                                     | 5号艇 年齢                                                 |
| `boat5_flying_late`                                             | 5号艇 フライング + 出遅れ                                  |
| `boat5_average_start_timing`                                    | 5号艇 平均スタートタイミング                               |
| `boat5_average_start_timing_z_score`                            | 5号艇 平均スタートタイミング レース内Zスコア               |
| `boat5_all_venue_win_rate`                                      | 5号艇 全国勝率                                             |
| `boat5_all_venue_win_rate_z_score`                              | 5号艇 全国勝率 レース内Zスコア                             |
| `boat5_all_venue_top2_rate`                                     | 5号艇 全国2連対率                                          |
| `boat5_this_venue_win_rate`                                     | 5号艇 当地勝率                                             |
| `boat5_this_venue_win_rate_z_score`                             | 5号艇 当地勝率 レース内Zスコア                             |
| `boat5_this_venue_top2_rate`                                    | 5号艇 当地2連対率                                          |
| `boat5_motor_top2_rate`                                         | 5号艇 モーター2連対率                                      |
| `boat5_motor_top2_rate_z_score`                                 | 5号艇 モーター2連対率 レース内Zスコア                      |
| `boat5_before_info_start_timing`                                | 5号艇 直前情報 スタートタイミング                          |
| `boat5_before_info_start_timing_abs_z_score`                    | 5号艇 直前情報 スタートタイミング絶対値 レース内Zスコア    |
| `boat5_before_info_adjusted_weight`                             | 5号艇 直前情報 調整体重                                    |
| `boat5_before_info_total_weight`                                | 5号艇 直前情報 合計体重                                    |
| `boat5_before_info_display_time`                                | 5号艇 直前情報 展示タイム                                  |
| `boat5_before_info_display_time_z_score`                        | 5号艇 直前情報 展示タイム レース内Zスコア                  |
| `boat5_before_info_tilt`                                        | 5号艇 直前情報 チルト                                      |
| `boat5_course5_average_start_timing`                            | 5号艇 5コース 平均スタートタイミング                       |
| `boat5_course5_average_start_rank`                              | 5号艇 5コース 平均スタート順位                             |
| `boat5_course5_1st_rate`                                        | 5号艇 5コース 1着率                                        |
| `boat5_course5_2nd_rate`                                        | 5号艇 5コース 2着率                                        |
| `boat5_course5_3rd_rate`                                        | 5号艇 5コース 3着率                                        |
| `boat5_last5_1st_rate`                                          | 5号艇 直近5走 1着率                                        |
| `boat5_last5_2nd_rate`                                          | 5号艇 直近5走 2着率                                        |
| `boat5_last5_3rd_rate`                                          | 5号艇 直近5走 3着率                                        |
| `boat5_last5_average_rank`                                      | 5号艇 直近5走 平均着順                                     |
| `boat5_last5_average_start_timing`                              | 5号艇 直近5走 平均スタートタイミング                       |
| `boat5_last5_start_timing_std`                                  | 5号艇 直近5走 スタートタイミング標準偏差                   |
| `boat5_last10_1st_rate`                                         | 5号艇 直近10走 1着率                                       |
| `boat5_last10_2nd_rate`                                         | 5号艇 直近10走 2着率                                       |
| `boat5_last10_3rd_rate`                                         | 5号艇 直近10走 3着率                                       |
| `boat5_last10_average_rank`                                     | 5号艇 直近10走 平均着順                                    |
| `boat5_last10_average_start_timing`                             | 5号艇 直近10走 平均スタートタイミング                      |
| `boat5_last10_start_timing_std`                                 | 5号艇 直近10走 スタートタイミング標準偏差                  |
| `boat6_racer_class`                                             | 6号艇 級                                                   |
| `boat6_sex`                                                     | 6号艇 性別                                                 |
| `boat6_age`                                                     | 6号艇 年齢                                                 |
| `boat6_flying_late`                                             | 6号艇 フライング + 出遅れ                                  |
| `boat6_average_start_timing`                                    | 6号艇 平均スタートタイミング                               |
| `boat6_average_start_timing_z_score`                            | 6号艇 平均スタートタイミング レース内Zスコア               |
| `boat6_all_venue_win_rate`                                      | 6号艇 全国勝率                                             |
| `boat6_all_venue_win_rate_z_score`                              | 6号艇 全国勝率 レース内Zスコア                             |
| `boat6_all_venue_top2_rate`                                     | 6号艇 全国2連対率                                          |
| `boat6_this_venue_win_rate`                                     | 6号艇 当地勝率                                             |
| `boat6_this_venue_win_rate_z_score`                             | 6号艇 当地勝率 レース内Zスコア                             |
| `boat6_this_venue_top2_rate`                                    | 6号艇 当地2連対率                                          |
| `boat6_motor_top2_rate`                                         | 6号艇 モーター2連対率                                      |
| `boat6_motor_top2_rate_z_score`                                 | 6号艇 モーター2連対率 レース内Zスコア                      |
| `boat6_before_info_start_timing`                                | 6号艇 直前情報 スタートタイミング                          |
| `boat6_before_info_start_timing_abs_z_score`                    | 6号艇 直前情報 スタートタイミング絶対値 レース内Zスコア    |
| `boat6_before_info_adjusted_weight`                             | 6号艇 直前情報 調整体重                                    |
| `boat6_before_info_total_weight`                                | 6号艇 直前情報 合計体重                                    |
| `boat6_before_info_display_time`                                | 6号艇 直前情報 展示タイム                                  |
| `boat6_before_info_display_time_z_score`                        | 6号艇 直前情報 展示タイム レース内Zスコア                  |
| `boat6_before_info_tilt`                                        | 6号艇 直前情報 チルト                                      |
| `boat6_course6_average_start_timing`                            | 6号艇 6コース 平均スタートタイミング                       |
| `boat6_course6_average_start_rank`                              | 6号艇 6コース 平均スタート順位                             |
| `boat6_course6_1st_rate`                                        | 6号艇 6コース 1着率                                        |
| `boat6_course6_2nd_rate`                                        | 6号艇 6コース 2着率                                        |
| `boat6_course6_3rd_rate`                                        | 6号艇 6コース 3着率                                        |
| `boat6_last5_1st_rate`                                          | 6号艇 直近5走 1着率                                        |
| `boat6_last5_2nd_rate`                                          | 6号艇 直近5走 2着率                                        |
| `boat6_last5_3rd_rate`                                          | 6号艇 直近5走 3着率                                        |
| `boat6_last5_average_rank`                                      | 6号艇 直近5走 平均着順                                     |
| `boat6_last5_average_start_timing`                              | 6号艇 直近5走 平均スタートタイミング                       |
| `boat6_last5_start_timing_std`                                  | 6号艇 直近5走 スタートタイミング標準偏差                   |
| `boat6_last10_1st_rate`                                         | 6号艇 直近10走 1着率                                       |
| `boat6_last10_2nd_rate`                                         | 6号艇 直近10走 2着率                                       |
| `boat6_last10_3rd_rate`                                         | 6号艇 直近10走 3着率                                       |
| `boat6_last10_average_rank`                                     | 6号艇 直近10走 平均着順                                    |
| `boat6_last10_average_start_timing`                             | 6号艇 直近10走 平均スタートタイミング                      |
| `boat6_last10_start_timing_std`                                 | 6号艇 直近10走 スタートタイミング標準偏差                  |
| `start_timing_std`                                              | 平均スタートタイミング 標準偏差                            |
| `average_start_timing_z_score_diff_boat12`                      | 平均スタートタイミング Zスコア 1号艇 - 2号艇               |
| `average_start_timing_z_score_diff_boat13`                      | 平均スタートタイミング Zスコア 1号艇 - 3号艇               |
| `average_start_timing_z_score_diff_boat14`                      | 平均スタートタイミング Zスコア 1号艇 - 4号艇               |
| `average_start_timing_z_score_diff_boat15`                      | 平均スタートタイミング Zスコア 1号艇 - 5号艇               |
| `average_start_timing_z_score_diff_boat16`                      | 平均スタートタイミング Zスコア 1号艇 - 6号艇               |
| `average_start_timing_z_score_diff_boat23`                      | 平均スタートタイミング Zスコア 2号艇 - 3号艇               |
| `average_start_timing_z_score_diff_boat24`                      | 平均スタートタイミング Zスコア 2号艇 - 4号艇               |
| `average_start_timing_z_score_diff_boat25`                      | 平均スタートタイミング Zスコア 2号艇 - 5号艇               |
| `average_start_timing_z_score_diff_boat26`                      | 平均スタートタイミング Zスコア 2号艇 - 6号艇               |
| `average_start_timing_z_score_diff_boat34`                      | 平均スタートタイミング Zスコア 3号艇 - 4号艇               |
| `average_start_timing_z_score_diff_boat35`                      | 平均スタートタイミング Zスコア 3号艇 - 5号艇               |
| `average_start_timing_z_score_diff_boat36`                      | 平均スタートタイミング Zスコア 3号艇 - 6号艇               |
| `average_start_timing_z_score_diff_boat45`                      | 平均スタートタイミング Zスコア 4号艇 - 5号艇               |
| `average_start_timing_z_score_diff_boat46`                      | 平均スタートタイミング Zスコア 4号艇 - 6号艇               |
| `average_start_timing_z_score_diff_boat56`                      | 平均スタートタイミング Zスコア 5号艇 - 6号艇               |
| `average_start_timing_z_score_diff_boat1_boat23456mean`         | 平均スタートタイミング Zスコア 1号艇 - 他艇平均            |
| `all_venue_win_rate_std`                                        | 全国勝率 標準偏差                                          |
| `all_venue_win_rate_z_score_diff_boat12`                        | 全国勝率 Zスコア 1号艇 - 2号艇                             |
| `all_venue_win_rate_z_score_diff_boat13`                        | 全国勝率 Zスコア 1号艇 - 3号艇                             |
| `all_venue_win_rate_z_score_diff_boat14`                        | 全国勝率 Zスコア 1号艇 - 4号艇                             |
| `all_venue_win_rate_z_score_diff_boat15`                        | 全国勝率 Zスコア 1号艇 - 5号艇                             |
| `all_venue_win_rate_z_score_diff_boat16`                        | 全国勝率 Zスコア 1号艇 - 6号艇                             |
| `all_venue_win_rate_z_score_diff_boat23`                        | 全国勝率 Zスコア 2号艇 - 3号艇                             |
| `all_venue_win_rate_z_score_diff_boat24`                        | 全国勝率 Zスコア 2号艇 - 4号艇                             |
| `all_venue_win_rate_z_score_diff_boat25`                        | 全国勝率 Zスコア 2号艇 - 5号艇                             |
| `all_venue_win_rate_z_score_diff_boat26`                        | 全国勝率 Zスコア 2号艇 - 6号艇                             |
| `all_venue_win_rate_z_score_diff_boat34`                        | 全国勝率 Zスコア 3号艇 - 4号艇                             |
| `all_venue_win_rate_z_score_diff_boat35`                        | 全国勝率 Zスコア 3号艇 - 5号艇                             |
| `all_venue_win_rate_z_score_diff_boat36`                        | 全国勝率 Zスコア 3号艇 - 6号艇                             |
| `all_venue_win_rate_z_score_diff_boat45`                        | 全国勝率 Zスコア 4号艇 - 5号艇                             |
| `all_venue_win_rate_z_score_diff_boat46`                        | 全国勝率 Zスコア 4号艇 - 6号艇                             |
| `all_venue_win_rate_z_score_diff_boat56`                        | 全国勝率 Zスコア 5号艇 - 6号艇                             |
| `all_venue_win_rate_z_score_diff_boat1_boat23456mean`           | 全国勝率 Zスコア 1号艇 - 他艇平均                          |
| `this_venue_win_rate_std`                                       | 当地勝率 標準偏差                                          |
| `this_venue_win_rate_z_score_diff_boat12`                       | 当地勝率 Zスコア 1号艇 - 2号艇                             |
| `this_venue_win_rate_z_score_diff_boat13`                       | 当地勝率 Zスコア 1号艇 - 3号艇                             |
| `this_venue_win_rate_z_score_diff_boat14`                       | 当地勝率 Zスコア 1号艇 - 4号艇                             |
| `this_venue_win_rate_z_score_diff_boat15`                       | 当地勝率 Zスコア 1号艇 - 5号艇                             |
| `this_venue_win_rate_z_score_diff_boat16`                       | 当地勝率 Zスコア 1号艇 - 6号艇                             |
| `this_venue_win_rate_z_score_diff_boat23`                       | 当地勝率 Zスコア 2号艇 - 3号艇                             |
| `this_venue_win_rate_z_score_diff_boat24`                       | 当地勝率 Zスコア 2号艇 - 4号艇                             |
| `this_venue_win_rate_z_score_diff_boat25`                       | 当地勝率 Zスコア 2号艇 - 5号艇                             |
| `this_venue_win_rate_z_score_diff_boat26`                       | 当地勝率 Zスコア 2号艇 - 6号艇                             |
| `this_venue_win_rate_z_score_diff_boat34`                       | 当地勝率 Zスコア 3号艇 - 4号艇                             |
| `this_venue_win_rate_z_score_diff_boat35`                       | 当地勝率 Zスコア 3号艇 - 5号艇                             |
| `this_venue_win_rate_z_score_diff_boat36`                       | 当地勝率 Zスコア 3号艇 - 6号艇                             |
| `this_venue_win_rate_z_score_diff_boat45`                       | 当地勝率 Zスコア 4号艇 - 5号艇                             |
| `this_venue_win_rate_z_score_diff_boat46`                       | 当地勝率 Zスコア 4号艇 - 6号艇                             |
| `this_venue_win_rate_z_score_diff_boat56`                       | 当地勝率 Zスコア 5号艇 - 6号艇                             |
| `this_venue_win_rate_z_score_diff_boat1_boat23456mean`          | 当地勝率 Zスコア 1号艇 - 他艇平均                          |
| `motor_top2_rate_std`                                           | モーター2連対率 標準偏差                                   |
| `motor_top2_rate_z_score_diff_boat12`                           | モーター2連対率 Zスコア 1号艇 - 2号艇                      |
| `motor_top2_rate_z_score_diff_boat13`                           | モーター2連対率 Zスコア 1号艇 - 3号艇                      |
| `motor_top2_rate_z_score_diff_boat14`                           | モーター2連対率 Zスコア 1号艇 - 4号艇                      |
| `motor_top2_rate_z_score_diff_boat15`                           | モーター2連対率 Zスコア 1号艇 - 5号艇                      |
| `motor_top2_rate_z_score_diff_boat16`                           | モーター2連対率 Zスコア 1号艇 - 6号艇                      |
| `motor_top2_rate_z_score_diff_boat23`                           | モーター2連対率 Zスコア 2号艇 - 3号艇                      |
| `motor_top2_rate_z_score_diff_boat24`                           | モーター2連対率 Zスコア 2号艇 - 4号艇                      |
| `motor_top2_rate_z_score_diff_boat25`                           | モーター2連対率 Zスコア 2号艇 - 5号艇                      |
| `motor_top2_rate_z_score_diff_boat26`                           | モーター2連対率 Zスコア 2号艇 - 6号艇                      |
| `motor_top2_rate_z_score_diff_boat34`                           | モーター2連対率 Zスコア 3号艇 - 4号艇                      |
| `motor_top2_rate_z_score_diff_boat35`                           | モーター2連対率 Zスコア 3号艇 - 5号艇                      |
| `motor_top2_rate_z_score_diff_boat36`                           | モーター2連対率 Zスコア 3号艇 - 6号艇                      |
| `motor_top2_rate_z_score_diff_boat45`                           | モーター2連対率 Zスコア 4号艇 - 5号艇                      |
| `motor_top2_rate_z_score_diff_boat46`                           | モーター2連対率 Zスコア 4号艇 - 6号艇                      |
| `motor_top2_rate_z_score_diff_boat56`                           | モーター2連対率 Zスコア 5号艇 - 6号艇                      |
| `motor_top2_rate_z_score_diff_boat1_boat23456mean`              | モーター2連対率 Zスコア 1号艇 - 他艇平均                   |
| `before_info_start_timing_abs_std`                              | 直前情報 スタートタイミング絶対値 標準偏差                 |
| `before_info_start_timing_abs_z_score_diff_boat12`              | 直前情報 スタートタイミング絶対値 Zスコア 1号艇 - 2号艇    |
| `before_info_start_timing_abs_z_score_diff_boat13`              | 直前情報 スタートタイミング絶対値 Zスコア 1号艇 - 3号艇    |
| `before_info_start_timing_abs_z_score_diff_boat14`              | 直前情報 スタートタイミング絶対値 Zスコア 1号艇 - 4号艇    |
| `before_info_start_timing_abs_z_score_diff_boat15`              | 直前情報 スタートタイミング絶対値 Zスコア 1号艇 - 5号艇    |
| `before_info_start_timing_abs_z_score_diff_boat16`              | 直前情報 スタートタイミング絶対値 Zスコア 1号艇 - 6号艇    |
| `before_info_start_timing_abs_z_score_diff_boat23`              | 直前情報 スタートタイミング絶対値 Zスコア 2号艇 - 3号艇    |
| `before_info_start_timing_abs_z_score_diff_boat24`              | 直前情報 スタートタイミング絶対値 Zスコア 2号艇 - 4号艇    |
| `before_info_start_timing_abs_z_score_diff_boat25`              | 直前情報 スタートタイミング絶対値 Zスコア 2号艇 - 5号艇    |
| `before_info_start_timing_abs_z_score_diff_boat26`              | 直前情報 スタートタイミング絶対値 Zスコア 2号艇 - 6号艇    |
| `before_info_start_timing_abs_z_score_diff_boat34`              | 直前情報 スタートタイミング絶対値 Zスコア 3号艇 - 4号艇    |
| `before_info_start_timing_abs_z_score_diff_boat35`              | 直前情報 スタートタイミング絶対値 Zスコア 3号艇 - 5号艇    |
| `before_info_start_timing_abs_z_score_diff_boat36`              | 直前情報 スタートタイミング絶対値 Zスコア 3号艇 - 6号艇    |
| `before_info_start_timing_abs_z_score_diff_boat45`              | 直前情報 スタートタイミング絶対値 Zスコア 4号艇 - 5号艇    |
| `before_info_start_timing_abs_z_score_diff_boat46`              | 直前情報 スタートタイミング絶対値 Zスコア 4号艇 - 6号艇    |
| `before_info_start_timing_abs_z_score_diff_boat56`              | 直前情報 スタートタイミング絶対値 Zスコア 5号艇 - 6号艇    |
| `before_info_start_timing_abs_z_score_diff_boat1_boat23456mean` | 直前情報 スタートタイミング絶対値 Zスコア 1号艇 - 他艇平均 |
| `before_info_display_time_std`                                  | 直前情報 展示タイム 標準偏差                               |
| `before_info_display_time_z_score_diff_boat12`                  | 直前情報 展示タイム Zスコア 1号艇 - 2号艇                  |
| `before_info_display_time_z_score_diff_boat13`                  | 直前情報 展示タイム Zスコア 1号艇 - 3号艇                  |
| `before_info_display_time_z_score_diff_boat14`                  | 直前情報 展示タイム Zスコア 1号艇 - 4号艇                  |
| `before_info_display_time_z_score_diff_boat15`                  | 直前情報 展示タイム Zスコア 1号艇 - 5号艇                  |
| `before_info_display_time_z_score_diff_boat16`                  | 直前情報 展示タイム Zスコア 1号艇 - 6号艇                  |
| `before_info_display_time_z_score_diff_boat23`                  | 直前情報 展示タイム Zスコア 2号艇 - 3号艇                  |
| `before_info_display_time_z_score_diff_boat24`                  | 直前情報 展示タイム Zスコア 2号艇 - 4号艇                  |
| `before_info_display_time_z_score_diff_boat25`                  | 直前情報 展示タイム Zスコア 2号艇 - 5号艇                  |
| `before_info_display_time_z_score_diff_boat26`                  | 直前情報 展示タイム Zスコア 2号艇 - 6号艇                  |
| `before_info_display_time_z_score_diff_boat34`                  | 直前情報 展示タイム Zスコア 3号艇 - 4号艇                  |
| `before_info_display_time_z_score_diff_boat35`                  | 直前情報 展示タイム Zスコア 3号艇 - 5号艇                  |
| `before_info_display_time_z_score_diff_boat36`                  | 直前情報 展示タイム Zスコア 3号艇 - 6号艇                  |
| `before_info_display_time_z_score_diff_boat45`                  | 直前情報 展示タイム Zスコア 4号艇 - 5号艇                  |
| `before_info_display_time_z_score_diff_boat46`                  | 直前情報 展示タイム Zスコア 4号艇 - 6号艇                  |
| `before_info_display_time_z_score_diff_boat56`                  | 直前情報 展示タイム Zスコア 5号艇 - 6号艇                  |
| `before_info_display_time_z_score_diff_boat1_boat23456mean`     | 直前情報 展示タイム Zスコア 1号艇 - 他艇平均               |
| `course_1st_rate_diff_boat12`                                   | コース別 1着率 1号艇 - 2号艇                               |
| `course_1st_rate_diff_boat13`                                   | コース別 1着率 1号艇 - 3号艇                               |
| `course_1st_rate_diff_boat14`                                   | コース別 1着率 1号艇 - 4号艇                               |
| `course_1st_rate_diff_boat15`                                   | コース別 1着率 1号艇 - 5号艇                               |
| `course_1st_rate_diff_boat16`                                   | コース別 1着率 1号艇 - 6号艇                               |
| `course_1st_rate_diff_boat23`                                   | コース別 1着率 2号艇 - 3号艇                               |
| `course_1st_rate_diff_boat24`                                   | コース別 1着率 2号艇 - 4号艇                               |
| `course_1st_rate_diff_boat25`                                   | コース別 1着率 2号艇 - 5号艇                               |
| `course_1st_rate_diff_boat26`                                   | コース別 1着率 2号艇 - 6号艇                               |
| `course_1st_rate_diff_boat34`                                   | コース別 1着率 3号艇 - 4号艇                               |
| `course_1st_rate_diff_boat35`                                   | コース別 1着率 3号艇 - 5号艇                               |
| `course_1st_rate_diff_boat36`                                   | コース別 1着率 3号艇 - 6号艇                               |
| `course_1st_rate_diff_boat45`                                   | コース別 1着率 4号艇 - 5号艇                               |
| `course_1st_rate_diff_boat46`                                   | コース別 1着率 4号艇 - 6号艇                               |
| `course_1st_rate_diff_boat56`                                   | コース別 1着率 5号艇 - 6号艇                               |
| `course_2nd_rate_diff_boat12`                                   | コース別 2着率 1号艇 - 2号艇                               |
| `course_2nd_rate_diff_boat13`                                   | コース別 2着率 1号艇 - 3号艇                               |
| `course_2nd_rate_diff_boat14`                                   | コース別 2着率 1号艇 - 4号艇                               |
| `course_2nd_rate_diff_boat15`                                   | コース別 2着率 1号艇 - 5号艇                               |
| `course_2nd_rate_diff_boat16`                                   | コース別 2着率 1号艇 - 6号艇                               |
| `course_2nd_rate_diff_boat23`                                   | コース別 2着率 2号艇 - 3号艇                               |
| `course_2nd_rate_diff_boat24`                                   | コース別 2着率 2号艇 - 4号艇                               |
| `course_2nd_rate_diff_boat25`                                   | コース別 2着率 2号艇 - 5号艇                               |
| `course_2nd_rate_diff_boat26`                                   | コース別 2着率 2号艇 - 6号艇                               |
| `course_2nd_rate_diff_boat34`                                   | コース別 2着率 3号艇 - 4号艇                               |
| `course_2nd_rate_diff_boat35`                                   | コース別 2着率 3号艇 - 5号艇                               |
| `course_2nd_rate_diff_boat36`                                   | コース別 2着率 3号艇 - 6号艇                               |
| `course_2nd_rate_diff_boat45`                                   | コース別 2着率 4号艇 - 5号艇                               |
| `course_2nd_rate_diff_boat46`                                   | コース別 2着率 4号艇 - 6号艇                               |
| `course_2nd_rate_diff_boat56`                                   | コース別 2着率 5号艇 - 6号艇                               |
| `course_3rd_rate_diff_boat12`                                   | コース別 3着率 1号艇 - 2号艇                               |
| `course_3rd_rate_diff_boat13`                                   | コース別 3着率 1号艇 - 3号艇                               |
| `course_3rd_rate_diff_boat14`                                   | コース別 3着率 1号艇 - 4号艇                               |
| `course_3rd_rate_diff_boat15`                                   | コース別 3着率 1号艇 - 5号艇                               |
| `course_3rd_rate_diff_boat16`                                   | コース別 3着率 1号艇 - 6号艇                               |
| `course_3rd_rate_diff_boat23`                                   | コース別 3着率 2号艇 - 3号艇                               |
| `course_3rd_rate_diff_boat24`                                   | コース別 3着率 2号艇 - 4号艇                               |
| `course_3rd_rate_diff_boat25`                                   | コース別 3着率 2号艇 - 5号艇                               |
| `course_3rd_rate_diff_boat26`                                   | コース別 3着率 2号艇 - 6号艇                               |
| `course_3rd_rate_diff_boat34`                                   | コース別 3着率 3号艇 - 4号艇                               |
| `course_3rd_rate_diff_boat35`                                   | コース別 3着率 3号艇 - 5号艇                               |
| `course_3rd_rate_diff_boat36`                                   | コース別 3着率 3号艇 - 6号艇                               |
| `course_3rd_rate_diff_boat45`                                   | コース別 3着率 4号艇 - 5号艇                               |
| `course_3rd_rate_diff_boat46`                                   | コース別 3着率 4号艇 - 6号艇                               |
| `course_3rd_rate_diff_boat56`                                   | コース別 3着率 5号艇 - 6号艇                               |
