import os
import re
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
MESSAGE_ID = os.environ["DISCORD_MESSAGE_ID"]

URL = "https://visual-novel-chart.ru/translation/utawarerumono"

GAME_TITLE = "Utawarerumono: Prelude to the Fallen"
GAME_URL = "https://visual-novel-chart.ru/translation/utawarerumono"

# Можешь потом заменить на другую картинку, если захочешь
THUMBNAIL_URL = "https://upload.wikimedia.org/wikipedia/en/3/31/Utawarerumono_Prelude_to_the_Fallen_cover.jpg"

EMBED_COLOR = 0x5865F2  # Discord blurple


def make_bar(percent, length=18):
    filled = round(percent / 100 * length)
    empty = length - filled
    return "█" * filled + "░" * empty


def extract_numbers(text):
    """
    Пытается вытащить:
    - процент
    - текущие строки
    - всего строк

    Подстраивается под формат вроде:
    '54.2% (1234 / 2276)'
    """
    percent = 0.0
    current = 0
    total = 0

    percent_match = re.search(r"(\d+(?:[.,]\d+)?)\s*%", text)
    if percent_match:
        percent = float(percent_match.group(1).replace(",", "."))

    frac_match = re.search(r"(\d+)\s*/\s*(\d+)", text)
    if frac_match:
        current = int(frac_match.group(1))
        total = int(frac_match.group(2))

    return percent, current, total


def find_progress_data(soup):
    """
    Ищем на странице блоки:
    Перевод / Редактура / Редактура 2
    и превращаем Редактура 2 -> Вычитка
    """
    text = soup.get_text("\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    result = {
        "Перевод": {"percent": 0.0, "current": 0, "total": 0},
        "Редактура": {"percent": 0.0, "current": 0, "total": 0},
        "Вычитка": {"percent": 0.0, "current": 0, "total": 0},
    }

    mapping = {
        "Перевод": "Перевод",
        "Редактура": "Редактура",
        "Редактура 2": "Вычитка",
    }

    for i, line in enumerate(lines):
        if line in mapping:
            label = mapping[line]

            # Ищем следующие 1-3 строки, где могут быть проценты / дроби
            search_chunk = " ".join(lines[i + 1:i + 4])
            percent, current, total = extract_numbers(search_chunk)

            result[label] = {
                "percent": percent,
                "current": current,
                "total": total,
            }

    return result


def build_field(name, percent, current, total):
    bar = make_bar(percent)
    value = f"`{bar}` **{percent:.1f}%**\n{current} / {total}"
    return {"name": name, "value": value, "inline": False}


def main():
    response = requests.get(URL, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    data = find_progress_data(soup)

    now_kyiv = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=3)))
    updated_at = now_kyiv.strftime("%d.%m.%Y %H:%M")

    embed = {
        "title": GAME_TITLE,
        "url": GAME_URL,
        "description": "Автоматически обновляемый прогресс перевода проекта **NightwhisperTL**.",
        "color": EMBED_COLOR,
        "thumbnail": {"url": THUMBNAIL_URL},
        "fields": [
            build_field(
                "Перевод",
                data["Перевод"]["percent"],
                data["Перевод"]["current"],
                data["Перевод"]["total"],
            ),
            build_field(
                "Редактура",
                data["Редактура"]["percent"],
                data["Редактура"]["current"],
                data["Редактура"]["total"],
            ),
            build_field(
                "Вычитка",
                data["Вычитка"]["percent"],
                data["Вычитка"]["current"],
                data["Вычитка"]["total"],
            ),
        ],
        "footer": {
            "text": f"Источник: visual-novel-chart.ru • Обновлено: {updated_at}"
        },
    }

    payload = {
        "username": "NightwhisperTL Progress",
        "content": "",
        "embeds": [embed],
    }

    edit_url = f"{WEBHOOK_URL}/messages/{MESSAGE_ID}"
    edit_response = requests.patch(edit_url, json=payload, timeout=30)
    edit_response.raise_for_status()

    print("Discord message updated successfully.")


if __name__ == "__main__":
    main()
