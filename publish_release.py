import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests


WEBHOOK_URL = (
    os.environ["DISCORD_RELEASE_WEBHOOK_URL"]
    .split("?")[0]
    .rstrip("/")
)


def get_env(name, default=""):
    return os.environ.get(name, default).strip()


def text(name, default=""):
    """
    Позволяет вводить \n в форме GitHub Actions,
    чтобы получить перенос строки в Discord.
    """
    return get_env(name, default).replace("\\n", "\n")


GAME_TITLE = text("GAME_TITLE")
VERSION = text("VERSION")
RELEASE_TYPE = text("RELEASE_TYPE")
DATE_TEXT = text("DATE_TEXT")

BANNER_URL = get_env("BANNER_URL")
GAME_URL = get_env("GAME_URL")

DESCRIPTION = text("DESCRIPTION")

STATUS_1 = text("STATUS_1")
STATUS_2 = text("STATUS_2")
STATUS_3 = text("STATUS_3")
STATUS_4 = text("STATUS_4")
STATUS_5 = text("STATUS_5")

INSTALL_TEXT = text("INSTALL_TEXT")
NOTE_TEXT = text("NOTE_TEXT")

DOWNLOAD_URL = get_env("DOWNLOAD_URL")
BUTTON_LABEL = text(
    "BUTTON_LABEL",
    "Скачать перевод",
)

FOOTER_TEXT = text(
    "FOOTER_TEXT",
    "NightwhisperTL",
)

ACCENT_COLOR = get_env(
    "ACCENT_COLOR",
    "5865F2",
)

MESSAGE_ID = get_env("MESSAGE_ID")


# Если дата не указана вручную —
# подставляем сегодняшнюю по Киеву.
if not DATE_TEXT:
    now = datetime.now(
        ZoneInfo("Europe/Kyiv")
    )

    DATE_TEXT = now.strftime(
        "%d.%m.%Y"
    )


# HEX -> число Discord.
try:
    color = int(
        ACCENT_COLOR
        .replace("#", "")
        .replace("0x", ""),
        16,
    )

except ValueError:
    color = 0x5865F2


# ----------------------------
# Заголовок
# ----------------------------

title = f"📦 {GAME_TITLE}"

if VERSION:
    title += f" — {VERSION}"


# ----------------------------
# Описание
# ----------------------------

description_parts = []


meta = []

if RELEASE_TYPE:
    meta.append(RELEASE_TYPE)

if DATE_TEXT:
    meta.append(DATE_TEXT)


if meta:
    description_parts.append(
        "**" + " • ".join(meta) + "**"
    )


if DESCRIPTION:
    description_parts.append(
        DESCRIPTION
    )


description = "\n\n".join(
    description_parts
)


# ----------------------------
# Поля
# ----------------------------

fields = []


status_lines = [
    STATUS_1,
    STATUS_2,
    STATUS_3,
    STATUS_4,
    STATUS_5,
]

status_lines = [
    line
    for line in status_lines
    if line
]


if status_lines:
    fields.append(
        {
            "name": "📖 Что переведено",
            "value": "\n".join(
                f"• {line}"
                for line in status_lines
            ),
            "inline": False,
        }
    )


if INSTALL_TEXT:
    fields.append(
        {
            "name": "🛠 Установка",
            "value": INSTALL_TEXT,
            "inline": False,
        }
    )


if NOTE_TEXT:
    fields.append(
        {
            "name": "ℹ️ Примечание",
            "value": NOTE_TEXT,
            "inline": False,
        }
    )


# ----------------------------
# Embed'ы
# ----------------------------

embeds = []


# Первый embed — широкий баннер сверху.
if BANNER_URL:
    embeds.append(
        {
            "color": color,
            "image": {
                "url": BANNER_URL
            },
        }
    )


# Второй embed — карточка релиза.
main_embed = {
    "title": title,
    "color": color,
    "fields": fields,
}


if GAME_URL:
    main_embed["url"] = GAME_URL


if description:
    main_embed["description"] = (
        description
    )


if FOOTER_TEXT:
    main_embed["footer"] = {
        "text": FOOTER_TEXT
    }


embeds.append(
    main_embed
)


# ----------------------------
# Настоящая кнопка-ссылка
# ----------------------------

button = {
    "type": 2,
    "style": 5,
    "label": BUTTON_LABEL,
    "url": DOWNLOAD_URL,
    "emoji": {
        "name": "⬇️"
    },
}


components = [
    {
        "type": 1,
        "components": [
            button
        ],
    }
]


payload = {
    "username": (
        "NightwhisperTL Releases"
    ),

    "embeds": embeds,

    "components": components,

    # Защита от случайных
    # @everyone/@here/ролей в тексте.
    "allowed_mentions": {
        "parse": []
    },
}


# ----------------------------
# Создание / редактирование
# ----------------------------

if MESSAGE_ID:
    # Редактируем старый пост.
    url = (
        f"{WEBHOOK_URL}"
        f"/messages/{MESSAGE_ID}"
        f"?with_components=true"
    )

    response = requests.patch(
        url,
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    print(
        "Публикация успешно обновлена."
    )

    print(
        "MESSAGE_ID="
        + str(data["id"])
    )


else:
    # Создаём новый пост.
    url = (
        f"{WEBHOOK_URL}"
        "?wait=true"
        "&with_components=true"
    )

    response = requests.post(
        url,
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    print(
        "Новая публикация создана."
    )

    print()
    print(
        "ID сообщения:"
    )
    print(
        data["id"]
    )

    print()
    print(
        "Сохрани этот ID, если "
        "захочешь позже изменить "
        "эту публикацию."
    )
