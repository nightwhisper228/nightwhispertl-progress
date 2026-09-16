import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

PAGE_URL = "https://visual-novel-chart.ru/translation/utawarerumono"
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"].rstrip("/")
MESSAGE_ID = os.environ.get("DISCORD_MESSAGE_ID", "").strip()


def get_number(text, label):
    match = re.search(
        rf"{re.escape(label)}\s*:\s*([\d\s]+)",
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        raise RuntimeError(f"Не удалось найти поле: {label}")

    return int(re.sub(r"\D", "", match.group(1)))


def format_number(value):
    return f"{value:,}".replace(",", " ")


def progress_bar(percent, width=20):
    filled = round(percent / 100 * width)
    filled = max(0, min(width, filled))
    return "█" * filled + "░" * (width - filled)


response = requests.get(
    PAGE_URL,
    timeout=30,
    headers={
        "User-Agent": "NightwhisperTL translation progress monitor"
    },
)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")
text = soup.get_text(" ", strip=True).replace("\xa0", " ")

total = get_number(text, "Всего строк")
translation = get_number(text, "Перевод")
editing = get_number(text, "Редактура 1")
proofreading = get_number(text, "Редактура 2")


def make_field(name, value):
    percent = value / total * 100 if total else 0

    return {
        "name": name,
        "value": (
            f"`{progress_bar(percent)}`\n"
            f"**{percent:.2f}%** — "
            f"{format_number(value)} / {format_number(total)}"
        ),
        "inline": False,
    }


now = datetime.now(ZoneInfo("Europe/Kyiv"))

payload = {
    "username": "NightwhisperTL Progress",
    "allowed_mentions": {"parse": []},
    "embeds": [
        {
            "title": "📊 Utawarerumono: Prelude to the Fallen",
            "url": PAGE_URL,
            "description": "Текущий прогресс перевода",
            "fields": [
                make_field("Перевод", translation),
                make_field("Редактура", editing),
                make_field("Вычитка", proofreading),
            ],
            "footer": {
                "text": (
                    "Данные: Visual Novel Chart"
                    f" • Обновлено {now:%d.%m.%Y %H:%M}"
                )
            },
        }
    ],
}

if MESSAGE_ID:
    result = requests.patch(
        f"{WEBHOOK_URL}/messages/{MESSAGE_ID}",
        json=payload,
        timeout=30,
    )
    result.raise_for_status()

    print(f"Обновлено сообщение {MESSAGE_ID}")

else:
    separator = "&" if "?" in WEBHOOK_URL else "?"

    result = requests.post(
        f"{WEBHOOK_URL}{separator}wait=true",
        json=payload,
        timeout=30,
    )
    result.raise_for_status()

    message_id = result.json()["id"]

    print()
    print("Сообщение успешно создано.")
    print("Теперь создай GitHub Variable:")
    print()
    print("DISCORD_MESSAGE_ID")
    print()
    print("со значением:")
    print()
    print(message_id)
