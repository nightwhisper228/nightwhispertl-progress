import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup


PAGE_URL = "https://visual-novel-chart.ru/translation/utawarerumono"

STEAM_URL = "https://store.steampowered.com/app/1151450/"

BANNER_URL = (
    "https://shared.fastly.steamstatic.com/"
    "store_item_assets/steam/apps/1151450/"
    "header.jpg?t=1732445188"
)

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"].rstrip("/")
MESSAGE_ID = os.environ["DISCORD_MESSAGE_ID"].strip()

GAME_TITLE = "Utawarerumono: Prelude to the Fallen"


def clean_number(value):
    return int(re.sub(r"\D", "", value))


def format_number(value):
    return f"{value:,}".replace(",", " ")


def progress_bar(percent, width=34):
    filled = round(percent / 100 * width)
    filled = max(0, min(width, filled))

    return "█" * filled + "░" * (width - filled)


def get_total(text):
    match = re.search(
        r"Всего\s+строк\s*:\s*([\d\s]+)",
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        raise RuntimeError(
            "Не удалось найти общее количество строк"
        )

    return clean_number(match.group(1))


def get_stage(text, label):
    match = re.search(
        rf"{re.escape(label)}\s*:\s*([\d\s]+)\s*"
        rf"\(\s*([\d.,]+)\s*%\s*\)",
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        raise RuntimeError(
            f"Не удалось найти данные: {label}"
        )

    current = clean_number(match.group(1))
    percent = float(
        match.group(2).replace(",", ".")
    )

    return current, percent


def make_field(name, current, total, percent):
    return {
        "name": name,
        "value": (
            f"`{progress_bar(percent)}` "
            f"**{percent:.2f}%**\n"
            f"{format_number(current)} / "
            f"{format_number(total)}"
        ),
        "inline": False,
    }


response = requests.get(
    PAGE_URL,
    timeout=30,
    headers={
        "User-Agent": (
            "NightwhisperTL "
            "translation progress monitor"
        )
    },
)

response.raise_for_status()

soup = BeautifulSoup(
    response.text,
    "html.parser",
)

text = (
    soup
    .get_text(" ", strip=True)
    .replace("\xa0", " ")
)


total = get_total(text)

translation, translation_percent = get_stage(
    text,
    "Перевод",
)

editing, editing_percent = get_stage(
    text,
    "Редактура 1",
)

proofreading, proofreading_percent = get_stage(
    text,
    "Редактура 2",
)


now = datetime.now(
    ZoneInfo("Europe/Kyiv")
)


banner_embed = {
    "url": STEAM_URL,
    "color": 0x5865F2,
    "image": {
        "url": BANNER_URL
    },
}


progress_embed = {
    "title": f"📊 {GAME_TITLE}",

    "url": PAGE_URL,

    "color": 0x5865F2,

    "fields": [
        make_field(
            "🌐 Перевод",
            translation,
            total,
            translation_percent,
        ),

        make_field(
            "✏️ Редактура",
            editing,
            total,
            editing_percent,
        ),

        make_field(
            "🔎 Вычитка",
            proofreading,
            total,
            proofreading_percent,
        ),
    ],

    "footer": {
        "text": (
            "Источник: Visual Novel Chart"
            f" • Обновлено: "
            f"{now:%d.%m.%Y %H:%M}"
        )
    },
}


payload = {
    "username": "NightwhisperTL Progress",

    "allowed_mentions": {
        "parse": []
    },

    "embeds": [
        banner_embed,
        progress_embed,
    ],
}


result = requests.patch(
    f"{WEBHOOK_URL}/messages/{MESSAGE_ID}",
    json=payload,
    timeout=30,
)

result.raise_for_status()


print("Сообщение успешно обновлено.")

print(
    f"Перевод: "
    f"{translation}/{total} "
    f"({translation_percent:.2f}%)"
)

print(
    f"Редактура: "
    f"{editing}/{total} "
    f"({editing_percent:.2f}%)"
)

print(
    f"Вычитка: "
    f"{proofreading}/{total} "
    f"({proofreading_percent:.2f}%)"
)
