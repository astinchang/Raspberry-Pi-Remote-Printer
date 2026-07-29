#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import logging
import os
import textwrap
from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)


logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)

TOKEN = os.environ["TELEGRAM_TOKEN"]
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0"))

PRINTER_DEVICE = os.getenv("PRINTER_DEVICE", "/dev/usb/lp0")
LINE_WIDTH = int(os.getenv("LINE_WIDTH", "32"))
MAX_CHARS = int(os.getenv("MAX_CHARS", "2000"))


def is_authorized(update: Update) -> bool:
    user = update.effective_user
    return bool(
        user is not None
        and ALLOWED_USER_ID != 0
        and user.id == ALLOWED_USER_ID
    )


def format_message(text: str, width: int = LINE_WIDTH) -> str:
    """Clean and wrap text for a narrow receipt printer."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove control characters while preserving normal newlines and tabs.
    text = "".join(
        character
        if character.isprintable() or character in "\n\t"
        else " "
        for character in text
    )

    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + "\n[Message truncated]"

    wrapped: list[str] = []

    for line in text.splitlines():
        if not line:
            wrapped.append("")
            continue

        wrapped.extend(
            textwrap.wrap(
                line,
                width=width,
                replace_whitespace=False,
                drop_whitespace=True,
            )
        )

    return "\n".join(wrapped)


def print_receipt(text: str, sender: str) -> None:
    timestamp = datetime.now().astimezone().strftime(
        "%Y-%m-%d %I:%M %p %Z"
    )

    double_text_width = max(1, LINE_WIDTH // 2)
    body = format_message(text, width = double_text_width)

    header = (
        "TELEGRAM MESSAGE\n"
        + "=" * LINE_WIDTH
        + "\n"
        + f"From: {sender}\n"
        + f"Time: {timestamp}\n"
        + "-" * LINE_WIDTH
        + "\n"
    )

    with open(PRINTER_DEVICE, "wb", buffering=0) as printer:
        printer.write(b"\x1b@")  # ESC/POS initialize

        printer.write(b"\n\n\n") # blank paper at top

        printer.write(header.encode("cp437", errors="replace")) # header

        printer.write(b"\x1d\x21\x11") # 2x width & 2x height
        printer.write((body + "\n").encode("cp437", errors="replace")) # body

        printer.write(b"\x1d\x21\x00") # normal size again

        printer.write(b"\n\n\n\n\n\n") # blank at bottom


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    del context

    await update.effective_message.reply_text(
        "Receipt printer bot is online.\n"
        "Send /id to obtain your Telegram user ID."
    )


async def show_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    del context

    user = update.effective_user
    chat = update.effective_chat

    await update.effective_message.reply_text(
        f"User ID: {user.id if user else 'unknown'}\n"
        f"Chat ID: {chat.id if chat else 'unknown'}"
    )


async def status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    del context

    if not is_authorized(update):
        return

    await update.effective_message.reply_text(
        "The Raspberry Pi printer is online."
    )


async def receive_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    del context

    message = update.effective_message

    if message is None or message.text is None:
        return

    if not is_authorized(update):
        logging.warning(
            "Rejected Telegram user ID %s",
            update.effective_user.id
            if update.effective_user
            else None,
        )
        return

    sender = (
        update.effective_user.full_name
        if update.effective_user
        else "Telegram"
    )

    try:
        # Printing is blocking, so perform it outside the bot event loop.
        await asyncio.to_thread(
            print_receipt,
            message.text,
            sender,
        )
    except Exception:
        logging.exception("Printing failed")
        await message.reply_text(
            "Printer error. Check the Raspberry Pi logs."
        )
        return

    await message.reply_text("Printed.")


async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    logging.error(
        "Unhandled error while processing %r",
        update,
        exc_info=context.error,
    )


def main() -> None:
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("id", show_id))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receive_text,
        )
    )
    application.add_error_handler(error_handler)

    application.run_polling()


if __name__ == "__main__":
    main()
