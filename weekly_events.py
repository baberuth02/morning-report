"""
本週事件：重大經濟數據（Forex Factory 免費日曆）+ 重點個股財報日（yfinance）
供美股彙報、NQ 晨間彙報共用
"""
import requests
import yfinance as yf
from datetime import datetime, date, timezone, timedelta

TZ_TW = timezone(timedelta(hours=8))
ECON_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
WEEKDAY = "一二三四五六日"

# 常見經濟數據中文名稱（未列出的保留英文）
ECON_NAMES = {
    "Non-Farm Employment Change": "非農就業人數",
    "Unemployment Rate": "失業率",
    "Average Hourly Earnings m/m": "平均時薪月增率",
    "CPI m/m": "CPI 月增率",
    "CPI y/y": "CPI 年增率",
    "Core CPI m/m": "核心 CPI 月增率",
    "PPI m/m": "PPI 月增率",
    "Core PPI m/m": "核心 PPI 月增率",
    "Core PCE Price Index m/m": "核心 PCE 物價指數月增率",
    "Federal Funds Rate": "聯準會利率決議",
    "FOMC Statement": "FOMC 聲明",
    "FOMC Press Conference": "FOMC 記者會",
    "FOMC Meeting Minutes": "FOMC 會議紀要",
    "Advance GDP q/q": "GDP 季增率（初值）",
    "Prelim GDP q/q": "GDP 季增率（修正值）",
    "Final GDP q/q": "GDP 季增率（終值）",
    "Retail Sales m/m": "零售銷售月增率",
    "Core Retail Sales m/m": "核心零售銷售月增率",
    "ISM Manufacturing PMI": "ISM 製造業 PMI",
    "ISM Services PMI": "ISM 服務業 PMI",
    "JOLTS Job Openings": "JOLTS 職缺數",
    "Unemployment Claims": "初領失業救濟金人數",
    "ADP Non-Farm Employment Change": "ADP 就業人數",
    "Prelim UoM Consumer Sentiment": "密大消費者信心（初值）",
    "CB Consumer Confidence": "諮商會消費者信心",
}


def week_range(now=None):
    """本週一至週日（台灣時間）"""
    today = (now or datetime.now(TZ_TW)).date()
    monday = today - timedelta(days=today.weekday())
    return monday, monday + timedelta(days=6)


def fmt_day(d):
    return f"{d.month}/{d.day}({WEEKDAY[d.weekday()]})"


def get_econ_events(impacts=("High",), country="USD"):
    """回傳本週美國重大經濟數據，時間轉為台灣時間；失敗回傳 None"""
    try:
        r = requests.get(ECON_URL, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        rows = r.json()
    except Exception:
        return None
    events = []
    for e in rows:
        if e.get("country") != country or e.get("impact") not in impacts:
            continue
        try:
            t = datetime.fromisoformat(e["date"]).astimezone(TZ_TW)
        except (KeyError, ValueError):
            continue
        title = e.get("title", "")
        events.append({
            "time": t,
            "title": ECON_NAMES.get(title, title),
            "forecast": e.get("forecast") or "",
            "previous": e.get("previous") or "",
        })
    events.sort(key=lambda x: x["time"])
    return events


def _earnings_date(ticker):
    cal = yf.Ticker(ticker).calendar
    dates = cal.get("Earnings Date") if isinstance(cal, dict) else None
    if not dates:
        return None
    d = dates[0]
    return d.date() if isinstance(d, datetime) else d if isinstance(d, date) else None


def get_week_earnings(tickers, now=None):
    """tickers: [(代號, 名稱)]；回傳本週有財報嘅 [(日期, 代號, 名稱)]，按日期排序"""
    start, end = week_range(now)
    found = []
    for sym, name in tickers:
        try:
            d = _earnings_date(sym)
        except Exception:
            continue
        if d and start <= d <= end:
            found.append((d, sym, name))
    found.sort()
    return found


def econ_lines(now=None):
    events = get_econ_events()
    lines = ["📅 <b>本週重大經濟數據</b>（台灣時間）"]
    if events is None:
        lines.append("⚠️ 經濟日曆暫時無法讀取")
        return lines
    if not events:
        lines.append("本週沒有高影響力美國數據")
        return lines
    today = (now or datetime.now(TZ_TW)).date()
    for e in events:
        t = e["time"]
        mark = "👉" if t.date() == today else "✅" if t.date() < today else "▫️"
        extra = "　".join(x for x in (
            f"預期 {e['forecast']}" if e["forecast"] else "",
            f"前值 {e['previous']}" if e["previous"] else "") if x)
        lines.append(f"{mark} {fmt_day(t.date())} {t:%H:%M} {e['title']}" + (f"　{extra}" if extra else ""))
    return lines


def earnings_lines(tickers, now=None):
    found = get_week_earnings(tickers, now)
    lines = ["📊 <b>本週重點個股財報</b>"]
    if not found:
        lines.append("本週清單內沒有個股公布財報")
        return lines
    today = (now or datetime.now(TZ_TW)).date()
    for d, sym, name in found:
        mark = "👉" if d == today else "✅" if d < today else "▫️"
        lines.append(f"{mark} {fmt_day(d)} {name}({sym})")
    return lines


if __name__ == "__main__":
    print("\n".join(econ_lines()))
    print()
    print("\n".join(earnings_lines([("NVDA", "輝達"), ("AAPL", "蘋果"), ("MSFT", "微軟")])))
