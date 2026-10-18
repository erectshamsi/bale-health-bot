from http.server import BaseHTTPRequestHandler
import json
import random
import urllib.request

BOT_TOKEN = "785765554:joOk2VXb5fly_tmuiqVsBM7RnuaHm60LMHg"

BASE_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}"

CARDS = [
    {
        "title": "🍵 کارت ۱: نوشیدن آب یا چای ایستاده!",
        "desc": "همین الان بلند شو، لیوانت رو پر کن و ایستاده، آروم و جرعه‌جرعه بنوش. بدنت از این تغییر زاویه سپاسگزاره!",
    },
    {
        "title": "🦋 کارت ۲: ۵ حرکت پروانه‌ای در جا!",
        "desc": "از پشت میز بلند شو! ۵ تا حرکت پروانه‌ای سبک و سریع در جا بزن تا خواب‌آلودگی کامل بپره!",
    },
    {
        "title": "🪑 کارت ۳: کشش شانه و پشت بازو!",
        "desc": "دست راستت رو ببر پشت گردن و با دست چپ آرنجت رو آروم به سمت عقب بکش (۱۰ ثانیه)، بعد دستت رو عوض کن.",
    },
    {
        "title": "👀 کارت ۴: قانون ۲۰-۲۰-۲۰ چشم‌ها!",
        "desc": "۲۰ ثانیه از مانیتور چشم بردار و به دورترین نقطه ممکن نگاه کن. ۳ تا نفس عمیق بکش!",
    },
]


def send_msg(chat_id, text, reply_markup=None):
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)
        update = json.loads(post_data.decode("utf-8"))

        main_kbd = {
            "keyboard": [
                [{"text": "🎯 گردونه شانس حرکت امروز"}],
                [{"text": "🏆 راهنمای امتیاز و مسابقه"}],
            ],
            "resize_keyboard": True,
        }

        confirm_kbd = {
            "inline_keyboard": [
                [
                    {
                        "text": "✅ انجامش دادم! (دریافت کد شانس)",
                        "callback_data": "done",
                    }
                ]
            ]
        }

        if "message" in update:
            chat_id = update["message"]["chat"]["id"]
            text = update["message"].get("text", "")

            if text == "/start":
                send_msg(
                    chat_id,
                    "سلام همکار پرانرژی! 🌿\nبه مینی‌چالش «کارت برنده سلامت» خوش اومدی.\n\nهر وقت پشت سیستم خسته شدی، دکمه زیر رو لمس کن تا ببینی شانس امروزت چه حرکتیه! 👇",
                    main_kbd,
                )
            elif text == "🎯 گردونه شانس حرکت امروز":
                card = random.choice(CARDS)
                msg = f"🎉 کارت امروز شما:\n\n{card['title']}\n\n{card['desc']}\n\n👇 به محض اینکه انجامش دادی، دکمه زیر رو بزن:"
                send_msg(chat_id, msg, confirm_kbd)
            elif text == "🏆 راهنمای امتیاز و مسابقه":
                send_msg(
                    chat_id,
                    "🌟 هر حرکت کوتاه = ۱۰ امتیاز سلامتی + یک کد شانس ۶ رقمی برای قرعه‌کشی باشگاه فرهنگی!",
                    main_kbd,
                )
            else:
                send_msg(chat_id, "لطفاً از دکمه‌های پایین صفحه استفاده کن 👇", main_kbd)

        elif "callback_query" in update:
            chat_id = update["callback_query"]["message"]["chat"]["id"]
            code = random.randint(100000, 999999)
            send_msg(
                chat_id,
                f"دمت گرم و خسته نباشی! 💪🔥\n\n✅ ۱۰ امتیاز سلامتی برات ثبت شد.\n🎁 کد شانس امروزت: {code}\n\n(این کد رو برای قرعه‌کشی نگه دار!)",
                main_kbd,
            )

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Health Bot is running!")
