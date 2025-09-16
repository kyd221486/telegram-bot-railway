import os, requests, feedparser, re
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from openai import OpenAI

# ------------------ NẠP BIẾN MÔI TRƯỜNG ------------------
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ------------------ OPENAI CLIENT ------------------
client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------ NGUỒN TIN ------------------
NEWS_SOURCES = {
    "baomoi": "https://baomoi.com/rss/the-gioi.rss",
    "CAND": "https://cand.com.vn/rss/phap-luat.rss",
    "VnExpress": "https://vnexpress.net/rss/phap-luat.rss",
    "Dân Trí": "https://dantri.com.vn/phap-luat.rss",
    "Thanh Niên": "https://thanhnien.vn/rss/thoi-su/phap-luat.rss",
    "PLO ‒ Pháp Luật TP. HCM": "https://plo.vn/rss/phap-luat.rss",
    "Vietnamnet": "https://vietnamnet.vn/rss/phap-luat.rss",
    "Tuổi Trẻ": "https://tuoitre.vn/rss/phap-luat.rss",
    "Lao Động": "https://laodong.vn/rss/phap-luat.rss",
    "Đời sống & Pháp luật": "https://doisongphapluat.com.vn/main-rss.html",
}

# ------------------ LẤY TIN ------------------
def fetch_news():
    articles = []
    for src, rss_url in NEWS_SOURCES.items():
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:10]:  # lấy 10 bài mới nhất
            if re.search(r"lừa đảo|chiếm đoạt|mạo danh", entry.title, re.I):
                articles.append({
                    "title": entry.title,
                    "link": entry.link,
                    "source": src
                })
    return articles

# ------------------ AI TÓM TẮT ------------------
def summarize(text: str):
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Bạn là trợ lý AI chuyên tóm tắt tin tức ngắn gọn."},
                {"role": "user", "content": f"Tóm tắt ngắn 2 câu cho tin sau:\n{text}"}
            ],
            temperature=0.3
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"(Lỗi tóm tắt: {e})"

# ------------------ TELEGRAM BOT ------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Xin chào, mình là Duy-Agent 🕵️! Gõ /scan để quét tin mới.")

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    articles = fetch_news()
    if not articles:
        await update.message.reply_text("Không tìm thấy tin nào về lừa đảo.")
        return
    for art in articles:
        summary = summarize(art["title"])
        msg = f"📌 *{art['title']}*\nNguồn: {art['source']}\nTóm tắt: {summary}\n🔗 {art['link']}"
        await update.message.reply_text(msg, parse_mode="Markdown")

# ------------------ LỊCH TỰ ĐỘNG ------------------
def daily_job(app):
    import asyncio
    async def send_news():
        articles = fetch_news()
        if articles:
            for art in articles[:5]:
                summary = summarize(art["title"])
                msg = f"📌 *{art['title']}*\nNguồn: {art['source']}\nTóm tắt: {summary}\n🔗 {art['link']}"
                await app.bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")
    asyncio.run(send_news())

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))

    # Lịch tự động gửi tin 9h sáng mỗi ngày
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: daily_job(app), "cron", hour=9, minute=0)
    scheduler.start()

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
