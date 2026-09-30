# 🚤 ボートレース AI ふなんゆさん 🤖

## 📖 概要

ボートレース（競艇）のレース結果を AI で予測し、期待値のある舟券を選別して自動購入するシステム。

## 📄 設計書

[`BASIC_DESIGN.md`](BASIC_DESIGN.md)

## 🛠 技術

- Python 3.14.6
- LightGBM
- SQLite
- Alembic
- Google Chrome
- Selenium
- systemd
- cron

## 🖥 VPS

### 1. 環境

- Ubuntu 24.04
- メモリ 12GB
- CPU 6Core
- SSD 100GB
- セキュリティグループ IPv4v6-SSH

### 2. 更新

```zsh
apt update && apt upgrade -y

reboot
```

### 3. パッケージ

```zsh
apt install -y git gcc
```

### 4. Python

```zsh
curl -LsSf https://astral.sh/uv/install.sh | sh

source $HOME/.local/bin/env

uv python install 3.14.6

ln -sf /root/.local/bin/python3.14 /root/.local/bin/python
```

### 5. GitHub SSH

```zsh
ssh-keygen -t ed25519
```

### 6. Google Chrome

```zsh
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

apt install -y ./google-chrome-stable_current_amd64.deb
```

### 7. セットアップ

```zsh
cd /root

git clone <GitHub SSH URL>

cd boatrace-ai-v4

python -m venv venv

source venv/bin/activate

pip install -r requirements.txt
```

## 🗄 データベース

### 1. 準備

```zsh
cd /root/boatrace-ai-v4

source venv/bin/activate
```

### 2. マイグレーション

```zsh
alembic upgrade head
```

### 3. 公式データ

[BOAT RACE ダウンロード・他](https://www.boatrace.jp/owpc/pc/extra/data/download.html)

```zsh
python download_official_data.py 201701 202612

python decompress.py

python import_official_data.py
```

### 4. スクレイピングデータ

```zsh
python scrape.py 20180101 20261231

python import_scraping_data.py
```

### 5. スタッツ計算

```zsh
python calculate_venue_stats.py

python calculate_racer_stats.py
```

## 🤖 学習・予測

### 1. データセット出力

```zsh
python output_dataset.py 2023 2024 2025 2026
```

### 2. モデル作成

```zsh
python create_model.py 2023 2024 2025 2026
```

### 3. 予測

```zsh
python predict.py 2023 2024 2025 2026
```

### 4. 分析・シミュレーション

```zsh
python analyze.py 2023 2024 2025 2026

python simulate.py 20230101 20261231
```

## ⚙️ 運用

### 1. 設定ファイル

`config/config.py`

```python
SUBSCRIBER_NUMBER = "12345678"
PASSWORD_NUMBER = "1234"
AUTH_PASSWORD = "123456"
BET_PASSWORD = "123456"

PAYPAY_BANK_STORE_NUMBER = "123"
PAYPAY_BANK_ACCOUNT_NUMBER = "1234567"
PAYPAY_BANK_PASSWORD = "1234567890"

GMAIL = "abcd1234@gmail.com"
APP_PASSWORD = "abcdefghijklmnop"
```

### 2. systemd

```zsh
cp systemd/*.service /etc/systemd/system/

systemctl daemon-reload
```

### 3. cron

```zsh
crontab -e
```

```cron
55 6 * * * systemctl start boatrace-ai || (cd /root/boatrace-ai-v4 && /root/boatrace-ai-v4/venv/bin/python -Bc "import mail; mail.send('🚨 START ERROR 🚨', '')")

55 23 * * * systemctl stop boatrace-ai || (cd /root/boatrace-ai-v4 && /root/boatrace-ai-v4/venv/bin/python -Bc "import mail; mail.send('🚨 STOP ERROR 🚨', '')")
```
