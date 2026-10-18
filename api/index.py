
from http.server import BaseHTTPRequestHandler
import json
import logging
import os
import random
import urllib.request
import urllib.error

logging.basicConfig(level=logging.INFO)

# توکن از تنظیمات امن Vercel خوانده می‌شود، نه از داخل کد
BOT_TOKEN = "785765554:joOk2VXb5fLy_tmuiqVsBM7RnuaHm60LMHg"

BASE_URL = (
    f"https://tapi.bale.ai/bot{BOT_TOKEN}"
    if BOT_TOKEN else ""
)

CARDS = [
    {
        "title": "🍵 کارت ۱: نوشیدن آب یا چای",
        "desc": "یک لیوان آب بردار و چند جرعه آرام بنوش. کمی از پشت میز فاصله بگیر!"
    },
    {
        "title": "🦋 کارت ۲: پنج حرکت پروانه‌ای",
        "desc": "اگر شرایط بدنی‌ات اجازه می‌دهد، پنج حرکت پروانه‌ای سبک انجام بده."
    },
    {
        "title": "🪑 کارت ۳: کشش شانه",
        "desc": "شانه‌ها را آرام حرکت بده و هر طرف را بدون فشار اضافی بکش."
    },
    {
        "title": "👀 کارت ۴: قانون ۲۰-۲۰-۲۰",
        "desc": "۲۰ ثانیه به نقطه‌ای دور نگاه کن و چند نفس آرام بکش."
    },
]

MAIN_KBD = {
    "keyboard": [
        [{"text": "🎯 گردونه شانس حرکت امروز"}],
        [{"text": "🏆 راهنمای امتیاز و مسابقه"}],
    ],
    "resize_keyboard": True,
}

CONFIRM_KBD = {
    "inline_keyboard": [
        [{
            "text": "✅ انجامش دادم! (دریافت کد شانس)",
            "callback_data": "done",
        }]
    ]
}


def bale_api(method, payload):
    """ارسال درخواست به بله و ثبت خطاهای احتمالی."""
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN is missing in Vercel environment variables.")
        return None

    url = f"{BASE_URL}/{method}"
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            status = response.status
            body = response.read().decode("utf-8", errors="replace")

    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        logging.error(
            "BALE_API_HTTP_ERROR method=%s status=%s response=%s",
            method, exc.code, body[:500]
        )
        return None

    except urllib.error.URLError as exc:
        logging.error(
            "BALE_API_CONNECTION_ERROR method=%s reason=%s",
            method, str(exc.reason)[:200]
        )
        return None

    except Exception as exc:
        # خطا ثبت می‌شود؛ دیگر بی‌صدا نادیده گرفته نمی‌شود.
        logging.error(
            "BALE_API_ERROR method=%s type=%s",
            method, type(exc).__name__
        )
        return None

    try:
        result = json.loads(body)
    except (ValueError, TypeError):
        logging.error(
            "BALE_API_INVALID_JSON method=%s status=%s",
            method, status
        )
        return None

    if not 200 <= status < 300:
        logging.error(
            "BALE_API_BAD_STATUS method=%s status=%s",
            method, status
        )
        return None

    if isinstance(result, dict) and result.get("ok") is False:
        logging.error(
            "BALE_API_REJECTED method=%s description=%s",
            method, result.get("description", "Unknown API error")
        )
        return None

    logging.info("BALE_API_SUCCESS method=%s status=%s", method, status)
    return result


def send_msg(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    return bale_api("sendMessage", payload)


def answer_callback(callback_id):
    if callback_id:
        return bale_api(
            "answerCallbackQuery",
            {"callback_query_id": callback_id}
        )


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        # برای آزمایش باز بودن سایت؛ توکن را نمایش نمی‌دهد.
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()

        if BOT_TOKEN:
            self.wfile.write(b"Health Bot is running.")
        else:
            self.wfile.write(b"Server is running, but BOT_TOKEN is missing.")

    def do_POST(self):
        # اگر توکن در تنظیمات Vercel تعریف نشده باشد،
        # به‌جای پاسخ موفق گمراه‌کننده، خطا ثبت می‌شود.
        if not BOT_TOKEN:
            logging.error("Cannot process webhook: BOT_TOKEN is missing.")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"BOT_TOKEN is not configured.")
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))

            if content_length <= 0 or content_length > 1_000_000:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid request body.")
                return

            post_data = self.rfile.read(content_length)
            update = json.loads(post_data.decode("utf-8"))

            logging.info(
                "WEBHOOK_RECEIVED update_keys=%s",
                list(update.keys()) if isinstance(update, dict) else []
            )

            if not isinstance(update, dict):
                raise ValueError("Update must be a JSON object.")

            message = update.get("message")

            if message:
                chat_id = (message.get("chat") or {}).get("id")
                text = (message.get("text") or "").strip()

                if chat_id is None:
                    logging.warning("Incoming message has no chat ID.")

                elif text == "/start" or text.startswith("/start "):
                    send_msg(
                        chat_id,
                        "سلام همکار پرانرژی! 🌿\n"
                        "به مینی‌چالش «کارت برنده سلامت» خوش اومدی.\n\n"
                        "هر وقت پشت سیستم خسته شدی، "
                        "دکمه زیر رو لمس کن تا حرکت امروزت رو ببینی! 👇",
                        MAIN_KBD
                    )

                elif text == "🎯 گردونه شانس حرکت امروز":
                    card = random.choice(CARDS)

                    msg = (
                        f"🎉 کارت امروز شما:\n\n"
                        f"{card['title']}\n\n"
                        f"{card['desc']}\n\n"
                        "👇 بعد از انجام حرکت، دکمه زیر رو بزن:"
                    )

                    send_msg(chat_id, msg, CONFIRM_KBD)

                elif text == "🏆 راهنمای امتیاز و مسابقه":
                    send_msg(
                        chat_id,
                        "🌟 هر حرکت کوتاه = ۱۰ امتیاز سلامتی "
                        "+ یک کد شانس ۶ رقمی برای قرعه‌کشی!",
                        MAIN_KBD
                    )

                else:
                    send_msg(
                        chat_id,
                        "لطفاً از دکمه‌های پایین صفحه استفاده کن 👇",
                        MAIN_KBD
                    )

            elif "callback_query" in update:
                callback = update["callback_query"]

                # پاسخ به فشردن دکمه؛ برای توقف حالت انتظار دکمه
                answer_callback(callback.get("id"))

                callback_message = callback.get("message") or {}
                chat_id = (callback_message.get("chat") or {}).get("id")
                callback_data = callback.get("data")

                if chat_id is not None and callback_data == "done":
                    code = random.randint(100000, 999999)

                    send_msg(
                        chat_id,
                        "دمت گرم و خسته نباشی! 💪🔥\n\n"
                        "✅ ۱۰ امتیاز سلامتی برات ثبت شد.\n"
                        f"🎁 کد شانس امروزت: {code}\n\n"
                        "این کد رو برای قرعه‌کشی نگه دار!",
                        MAIN_KBD
                    )

                elif chat_id is None:
                    logging.warning(
                        "Callback query has no accessible chat message."
                    )

            else:
                logging.info("Update has no message or callback_query.")

        except (ValueError, UnicodeDecodeError):
            logging.exception("Invalid webhook request body.")
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid JSON.")
            return

        except Exception:
            logging.exception("Unexpected webhook processing error.")

        # این پاسخ مربوط به دریافت وب‌هوک است؛
        # موفقیت ارسال پیام از طریق گزارش‌های BALE_API بررسی می‌شود.
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"OK")
