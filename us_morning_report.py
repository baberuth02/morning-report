"""
美股晨間彙報：三大指數 + 納指市值前10大
每日盤後或開盤前執行，推播至 Telegram
"""
import json
import requests
import yfinance as yf
from datetime import datetime, timezone, timedelta

CONFIG_FILE = r"C:\Users\User\tradingview-mcp-jackson\nq_report_config.json"

INDICES = [
    ("^DJI",  "道瓊"),
    ("^IXIC", "那斯達克"),
    ("^GSPC", "S&P 500"),
    ("^SOX",  "費城半導體"),
]

# 納指重點個股
TOP10 = [
    ("NVDA",  "輝達"),
    ("AAPL",  "蘋果"),
    ("MSFT",  "微軟"),
    ("TSM",   "台積電"),
    ("AMZN",  "亞馬遜"),
    ("GOOGL", "Alphabet"),
    ("META",  "Meta"),
    ("TSLA",  "特斯拉"),
    ("AVGO",  "博通"),
    ("SPCX",  "SpaceX"),
]

def get_quote(ticker):
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        prev_close = info.previous_close
        last_price = info.last_price
        if not prev_close or not last_price:
            hist = t.history(period="2d")
            if len(hist) >= 2:
                prev_close = hist["Close"].iloc[-2]
                last_price = hist["Close"].iloc[-1]
            elif len(hist) == 1:
                prev_close = hist["Close"].iloc[-1]
                last_price = prev_close
        chg     = last_price - prev_close
        chg_pct = chg / prev_close * 100 if prev_close else 0
        return last_price, chg, chg_pct
    except Exception:
        return None, None, None

def fmt_chg(chg, pct):
    if chg is None:
        return "N/A"
    sign = "+" if chg >= 0 else ""
    return f"{sign}{chg:,.2f} ({sign}{pct:.2f}%)"

def arrow(pct):
    if pct is None:
        return "⬜"
    return "🔴" if pct < 0 else "🟢"

def build_message():
    tz_tw = timezone(timedelta(hours=8))
    today = datetime.now(tz_tw).strftime("%Y/%m/%d %H:%M")
    lines = [f"🇺🇸 <b>美股彙報 — {today}</b>\n"]

    # 三大指數
    lines.append("📊 <b>四大指數</b>")
    for sym, name in INDICES:
        price, chg, pct = get_quote(sym)
        if price:
            lines.append(f"{arrow(pct)} {name}：{price:,.2f}　{fmt_chg(chg, pct)}")
        else:
            lines.append(f"⬜ {name}：N/A")

    lines.append("")

    # 納指重點個股
    lines.append("💹 <b>納指重點個股</b>")
    for sym, name in TOP10:
        price, chg, pct = get_quote(sym)
        if price:
            lines.append(f"{arrow(pct)} {name}({sym})：${price:,.2f}　{fmt_chg(chg, pct)}")
        else:
            lines.append(f"⬜ {name}({sym})：N/A")

    return "\n".join(lines)

def send_telegram(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": chat_id, "text": message, "parse_mode": "HTML"}, timeout=15)
        return r.ok, r.text
    except Exception as e:
        return False, str(e)

def main():
    import os
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id   = os.environ.get("TELEGRAM_CHAT_ID")
    if bot_token and chat_id:
        cfg = {"bot_token": bot_token, "chat_id": chat_id}
    else:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            cfg = json.load(f)

    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("抓取資料中...")
    msg = build_message()
    print(msg.encode("utf-8", errors="replace").decode("utf-8", errors="replace"))
    print()

    ok, resp = send_telegram(cfg["bot_token"], cfg["chat_id"], msg)
    print("推播成功" if ok else f"推播失敗：{resp}")

if __name__ == "__main__":
    main()
