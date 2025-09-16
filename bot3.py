import os
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SEEN_FILE = "seen_links.txt"

if not os.path.exists(SEEN_FILE):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        pass

def is_seen(url: str) -> bool:
    with open(SEEN_FILE, "r", encoding="utf-8") as f:
        seen = f.read().splitlines()
    return url in seen

def mark_seen(url: str):
    with open(SEEN_FILE, "a", encoding="utf-8") as f:
        f.write(url + "\n")

def scrape_baomoi():
    url = "https://baomoi.com/tim-kiem/lua-dao-tag102.epi"
    r = requests.get(url, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    links = []
    for a in soup.select("a.bm_L"):
        href = a.get("href")
        if href and href.startswith("/"):
            full_url = "https://baomoi.com" + href
            title = a.get_text(strip=True)
            links.append((title, full_url))
    return links

async def scan_and_send(context: ContextTypes.DEFAULT_TYPE):
    links = scrape_baomoi()
    new_links = [l for l in links if not is_seen(l[1])]
    if not new_links:
        return
    msg = "📰 Tin mới về lừa đảo:\n\n"
    for title, url in new_links[:5]:
        msg += f"- {title}\n{url}\n\n"
        mark_seen(url)
    await context.bot.send_message(chat_id=CHAT_ID, text=msg)

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await scan_and_send(context)

async def post_init(app: Application):
    # Đăng ký job tự động sau khi app đã init
    app.job_queue.run_repeating(scan_and_send, interval=3600, first=5)

def main():
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("scan", scan))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
