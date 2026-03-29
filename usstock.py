"""
📉 美股回檔分析 & 分段買進建議器 v3.0
==========================================
UI/UX 全面升級版

使用方式:
  1. pip install streamlit yfinance plotly pandas numpy
  2. streamlit run stock_pullback_analyzer_v3.py

v3 UI/UX 升級:
  ✅ 頂部快速總覽儀表板（一眼掃完所有標的狀態）
  ✅ 回檔排名用互動式水平長條圖取代靜態 HTML
  ✅ 雷達圖多維度對比（回檔深度 / RSI / 量比 / 均線距離 / 估值）
  ✅ 甜甜圈圖顯示資金分配
  ✅ 買進計畫用 Step 進度條呈現（取代堆疊文字框）
  ✅ K線圖預設展開第一檔，其餘折疊
  ✅ 側邊欄加入常用組合快捷按鈕
  ✅ 整體配色、間距、字型一致性大幅改善
  ✅ 行動裝置響應式優化
"""

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ─────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="美股回檔分析器 v3",
    page_icon="📉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Colors
# ─────────────────────────────────────────────
TICKER_COLORS = [
    "#76b900", "#2d6cdf", "#e31937", "#f59e0b", "#8b5cf6",
    "#06b6d4", "#ec4899", "#14b8a6", "#f97316", "#6366f1",
]
BG_DARK = "#0b1120"
SURFACE = "#111827"
SURFACE2 = "#1a2332"
BORDER = "#1f2e40"
TEXT = "#e2e8f0"
TEXT_DIM = "#8b9bb4"
GREEN = "#10b981"
RED = "#ef4444"
AMBER = "#f59e0b"
BLUE = "#3b82f6"
PURPLE = "#8b5cf6"

def get_color(idx: int) -> str:
    return TICKER_COLORS[idx % len(TICKER_COLORS)]

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

/* ── Global ── */
[data-testid="stAppViewContainer"] {{
    font-family: 'Noto Sans TC', -apple-system, sans-serif;
}}
[data-testid="stSidebar"] {{
    background: {SURFACE};
}}
.block-container {{ padding-top: 2rem; }}
.mono {{ font-family: 'JetBrains Mono', monospace; }}

/* ── Hero Header ── */
.hero-bar {{
    background: linear-gradient(135deg, {SURFACE} 0%, {SURFACE2} 100%);
    border: 1px solid {BORDER};
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 16px;
}}
.hero-left h1 {{
    font-size: 1.6rem;
    font-weight: 800;
    margin: 0;
    background: linear-gradient(135deg, #e2e8f0, #8b9bb4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.hero-left .sub {{ font-size: 0.82rem; color: {TEXT_DIM}; margin-top: 4px; }}
.hero-stats {{
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
}}
.hero-stat {{
    text-align: center;
    min-width: 80px;
}}
.hero-stat .val {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.5rem;
    font-weight: 700;
}}
.hero-stat .lbl {{
    font-size: 0.68rem;
    color: {TEXT_DIM};
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

/* ── Quick Scan Cards ── */
.scan-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 12px;
    margin-bottom: 32px;
}}
.scan-card {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 18px;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
    cursor: default;
}}
.scan-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.4);
}}
.scan-card .accent-bar {{
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
}}
.scan-card .ticker {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.1rem;
    font-weight: 700;
    margin-top: 4px;
}}
.scan-card .name {{
    font-size: 0.72rem;
    color: {TEXT_DIM};
    margin-bottom: 10px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.scan-card .price-row {{
    display: flex;
    align-items: baseline;
    gap: 8px;
    margin-bottom: 6px;
}}
.scan-card .price {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.3rem;
    font-weight: 600;
}}
.scan-card .change {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    font-weight: 600;
}}
.scan-card .mini-stats {{
    display: flex;
    justify-content: space-between;
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid {BORDER};
}}
.scan-card .mini-stat .v {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    font-weight: 600;
}}
.scan-card .mini-stat .l {{
    font-size: 0.62rem;
    color: {TEXT_DIM};
    text-transform: uppercase;
}}

/* ── Signal badge ── */
.sig {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 600;
}}
.sig-buy {{ background: rgba(16,185,129,0.12); color: {GREEN}; }}
.sig-watch {{ background: rgba(245,158,11,0.12); color: {AMBER}; }}
.sig-caution {{ background: rgba(239,68,68,0.12); color: {RED}; }}
.sig .dot {{
    width: 6px; height: 6px;
    border-radius: 50%;
    display: inline-block;
}}
.sig-buy .dot {{ background: {GREEN}; }}
.sig-watch .dot {{ background: {AMBER}; }}
.sig-caution .dot {{ background: {RED}; }}

/* ── Section ── */
.sec-head {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 36px 0 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid {BORDER};
}}
.sec-num {{
    width: 32px; height: 32px;
    display: flex; align-items: center; justify-content: center;
    border-radius: 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    font-weight: 700;
    flex-shrink: 0;
}}
.sec-title {{ font-size: 1.2rem; font-weight: 700; }}

/* ── Step Plan ── */
.step-plan {{
    display: flex;
    flex-direction: column;
    gap: 0;
    margin: 12px 0 20px;
}}
.step-item {{
    display: flex;
    gap: 16px;
    position: relative;
    padding-bottom: 20px;
}}
.step-item:last-child {{ padding-bottom: 0; }}
.step-line {{
    display: flex;
    flex-direction: column;
    align-items: center;
    flex-shrink: 0;
    width: 32px;
}}
.step-dot {{
    width: 14px; height: 14px;
    border-radius: 50%;
    border: 2px solid {BORDER};
    background: {SURFACE};
    z-index: 1;
    flex-shrink: 0;
}}
.step-dot.active {{ border-color: {GREEN}; background: rgba(16,185,129,0.2); }}
.step-dot.stop {{ border-color: {RED}; background: rgba(239,68,68,0.2); }}
.step-dot.wait {{ border-color: {AMBER}; background: rgba(245,158,11,0.2); }}
.step-connector {{
    width: 2px;
    flex: 1;
    background: {BORDER};
    min-height: 20px;
}}
.step-content {{
    flex: 1;
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 14px 18px;
}}
.step-content .head {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 6px;
    flex-wrap: wrap;
}}
.step-content .phase-name {{
    font-weight: 700;
    font-size: 0.92rem;
}}
.step-content .phase-tag {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    padding: 2px 10px;
    border-radius: 6px;
    font-weight: 600;
}}
.step-content .phase-tag.buy {{ background: rgba(16,185,129,0.1); color: {GREEN}; }}
.step-content .phase-tag.stop {{ background: rgba(239,68,68,0.1); color: {RED}; }}
.step-content .phase-tag.wait {{ background: rgba(245,158,11,0.1); color: {AMBER}; }}
.step-content .trigger {{
    font-size: 0.82rem;
    color: {TEXT_DIM};
    line-height: 1.6;
}}
.step-content .price-target {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.15rem;
    font-weight: 700;
}}

/* ── Ticker Section Header ── */
.ticker-section {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 20px 24px;
    margin-top: 28px;
    margin-bottom: 12px;
}}
.ticker-section .top-row {{
    display: flex;
    align-items: center;
    gap: 14px;
    flex-wrap: wrap;
}}
.ticker-section .tk {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.4rem;
    font-weight: 800;
}}
.ticker-section .nm {{ color: {TEXT_DIM}; font-size: 0.9rem; }}
.ticker-section .budget-tag {{
    margin-left: auto;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    color: {TEXT_DIM};
    background: {SURFACE2};
    padding: 4px 14px;
    border-radius: 8px;
}}
.ticker-section .metrics-row {{
    display: flex;
    gap: 16px;
    margin-top: 16px;
    flex-wrap: wrap;
}}
.ticker-section .m-item {{
    background: {SURFACE2};
    border-radius: 8px;
    padding: 10px 16px;
    text-align: center;
    min-width: 90px;
    flex: 1;
}}
.ticker-section .m-item .mv {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.1rem;
    font-weight: 600;
}}
.ticker-section .m-item .ml {{
    font-size: 0.62rem;
    color: {TEXT_DIM};
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 2px;
}}

/* ── Responsive ── */
@media (max-width: 768px) {{
    .hero-bar {{ flex-direction: column; text-align: center; }}
    .scan-grid {{ grid-template-columns: 1fr 1fr; }}
    .ticker-section .metrics-row {{ gap: 8px; }}
    .ticker-section .m-item {{ min-width: 70px; padding: 8px 10px; }}
}}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Core Functions (same logic, cleaner)
# ─────────────────────────────────────────────

@st.cache_data(ttl=300)
def fetch_stock_data(ticker: str, period: str = "1y") -> pd.DataFrame:
    try:
        df = yf.Ticker(ticker).history(period=period)
    except Exception:
        return pd.DataFrame()
    if df.empty or len(df) < 20:
        return pd.DataFrame()

    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA50"] = df["Close"].rolling(50).mean()
    df["MA200"] = df["Close"].rolling(200).mean()

    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    ema12 = df["Close"].ewm(span=12).mean()
    ema26 = df["Close"].ewm(span=26).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_Signal"] = df["MACD"].ewm(span=9).mean()
    df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]

    df["BB_Mid"] = df["Close"].rolling(20).mean()
    bb_std = df["Close"].rolling(20).std()
    df["BB_Upper"] = df["BB_Mid"] + 2 * bb_std
    df["BB_Lower"] = df["BB_Mid"] - 2 * bb_std
    df["Vol_MA20"] = df["Volume"].rolling(20).mean()
    return df


@st.cache_data(ttl=600)
def fetch_stock_info(ticker: str) -> dict:
    try:
        return yf.Ticker(ticker).info
    except Exception:
        return {}


def fetch_all(tickers, period):
    results = {}
    with ThreadPoolExecutor(max_workers=min(len(tickers), 6)) as ex:
        fd = {ex.submit(fetch_stock_data, t, period): t for t in tickers}
        fi = {ex.submit(fetch_stock_info, t): t for t in tickers}
        for f in as_completed(fd):
            t = fd[f]
            try: results.setdefault(t, {})["data"] = f.result()
            except: results.setdefault(t, {})["data"] = pd.DataFrame()
        for f in as_completed(fi):
            t = fi[f]
            try: results.setdefault(t, {})["info"] = f.result()
            except: results.setdefault(t, {})["info"] = {}
    return results


def calc_pullback(df):
    if df.empty or len(df) < 20: return {}
    high_price = df["High"].max()
    high_date = df["High"].idxmax()
    cur = df["Close"].iloc[-1]
    low = df["Low"].min()
    pb = (cur - high_price) / high_price * 100

    def s(col):
        v = df[col].iloc[-1] if col in df.columns else None
        return v if v is not None and not pd.isna(v) else None

    vol = df["Volume"].iloc[-1]
    avg_vol = s("Vol_MA20") or vol
    return {
        "cur": cur, "high": high_price, "high_date": high_date, "low": low,
        "pb": pb, "ma20": s("MA20"), "ma50": s("MA50"), "ma200": s("MA200"),
        "rsi": s("RSI"), "macd": s("MACD"), "macd_sig": s("MACD_Signal"),
        "vol_ratio": vol / avg_vol if avg_vol > 0 else 1.0, "avg_vol": avg_vol,
    }


def ma_dist(price, ma):
    return (price - ma) / ma * 100 if ma and ma > 0 else None


def get_signal(pb, rsi):
    p = abs(pb)
    if p >= 20 and rsi and rsi < 35: return "超賣 — 強烈關注", "sig-buy"
    elif p >= 10 and rsi and rsi < 45: return "分批布局機會", "sig-buy"
    elif p >= 10: return "觀察中", "sig-watch"
    elif p >= 5: return "初步回檔", "sig-watch"
    else: return "未明顯回檔", "sig-caution"


def fmt(v, spec=".1f", fallback="—"):
    return f"{v:{spec}}" if v is not None else fallback


def gen_plan(m, budget):
    price, high, pb_abs, ma200 = m["cur"], m["high"], abs(m["pb"]), m.get("ma200")
    phases = []

    if pb_abs < 5:
        phases.append({"ph": "觀望", "trig": f"僅回檔 {pb_abs:.1f}%，等 ≥10%", "pt": price*0.90, "pct": 0, "why": "回檔不足", "type": "wait"})
        phases.append({"ph": "第一批", "trig": f"跌至 ${price*0.90:.2f}", "pt": price*0.90, "pct": 30, "why": "回檔達有意義幅度", "type": "buy"})
        phases.append({"ph": "第二批", "trig": f"跌至 ${price*0.85:.2f}", "pt": price*0.85, "pct": 30, "why": "更深修正", "type": "buy"})
        phases.append({"ph": "第三批", "trig": "確認反彈 + 站上 20MA", "pt": price*0.88, "pct": 40, "why": "趨勢反轉確認", "type": "buy"})
    elif pb_abs < 15:
        phases.append({"ph": "第一批", "trig": f"現價 ${price:.2f} 附近企穩", "pt": price, "pct": 30, "why": f"已修正 {pb_abs:.1f}%", "type": "buy"})
        phases.append({"ph": "第二批", "trig": f"再跌至 ${price*0.95:.2f}", "pt": price*0.95, "pct": 30, "why": "攤低成本", "type": "buy"})
        phases.append({"ph": "第三批", "trig": f"反彈站穩 ${price*1.05:.2f}", "pt": price*1.05, "pct": 40, "why": "趨勢反轉確認", "type": "buy"})
    elif pb_abs < 30:
        phases.append({"ph": "第一批", "trig": f"現價 ${price:.2f}（回檔 {pb_abs:.1f}%）", "pt": price, "pct": 35, "why": "估值壓縮明顯", "type": "buy"})
        phases.append({"ph": "第二批", "trig": f"下探 ${price*0.93:.2f}", "pt": price*0.93, "pct": 35, "why": "恐慌賣盤買點", "type": "buy"})
        phases.append({"ph": "第三批", "trig": f"突破 ${price*1.08:.2f}", "pt": price*1.08, "pct": 30, "why": "底部確認", "type": "buy"})
    else:
        phases.append({"ph": "⚠️ 深度修正", "trig": f"下跌 {pb_abs:.1f}%，先確認基本面", "pt": price, "pct": 0, "why": "須排除 value trap", "type": "wait"})
        phases.append({"ph": "第一批", "trig": f"確認非基本面問題，${price:.2f} 試探", "pt": price, "pct": 20, "why": "輕倉試探", "type": "buy"})
        phases.append({"ph": "第二批", "trig": "止穩訊號（量縮 / RSI 背離）", "pt": price*0.95, "pct": 30, "why": "底部訊號", "type": "buy"})
        phases.append({"ph": "第三批", "trig": "站回 50MA 上方", "pt": m["ma50"] if m["ma50"] else price*1.1, "pct": 50, "why": "趨勢修復", "type": "buy"})

    stop_p = min(price * 0.92, ma200 * 0.97) if ma200 and ma200 > 0 else price * 0.90
    phases.append({"ph": "停損", "trig": f"跌破 ${stop_p:.2f}（{((stop_p/price-1)*100):.1f}%）", "pt": stop_p, "pct": -100, "why": "紀律停損，保護本金", "type": "stop"})

    for p in phases:
        if p["pct"] > 0:
            p["dollar"] = budget * p["pct"] / 100
            p["shares"] = int(p["dollar"] / p["pt"]) if p["pt"] > 0 else 0
        else:
            p["dollar"] = 0
            p["shares"] = 0
    return phases


def calc_weights(metrics):
    scores = {}
    for t, m in metrics.items():
        p = abs(m["pb"])
        r = m["rsi"] if m["rsi"] else 50
        scores[t] = max(p * 0.6 + max(0, 50 - r) * 0.4, 1)
    total = sum(scores.values())
    return {t: s / total for t, s in scores.items()}


# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ 設定")

    # Quick presets
    st.markdown("##### 快速組合")
    preset_cols = st.columns(2)
    with preset_cols[0]:
        if st.button("Mag 7", use_container_width=True):
            st.session_state["ticker_input"] = "AAPL, MSFT, GOOG, AMZN, NVDA, META, TSLA"
        if st.button("半導體", use_container_width=True):
            st.session_state["ticker_input"] = "NVDA, AMD, AVGO, TSM, QCOM, INTC"
    with preset_cols[1]:
        if st.button("AI 概念", use_container_width=True):
            st.session_state["ticker_input"] = "NVDA, PLTR, MSFT, GOOG, META, CRM, SNOW"
        if st.button("電動車", use_container_width=True):
            st.session_state["ticker_input"] = "TSLA, RIVN, NIO, LI, XPEV, LCID"

    st.markdown("---")

    default_val = st.session_state.get("ticker_input", "GOOG, NVDA, TSLA, PLTR, AAPL")
    ticker_input = st.text_input(
        "🔍 輸入股票代號（逗號分隔，最多 10 檔）",
        value=default_val,
        placeholder="GOOG, NVDA, TSLA...",
    )

    lookback = st.selectbox("📅 回顧期間", ["6mo", "1y", "2y"], index=1,
        format_func=lambda x: {"6mo": "6 個月", "1y": "1 年", "2y": "2 年"}[x])

    budget = st.number_input("💰 總預算 (USD)", min_value=1000, max_value=10_000_000, value=100_000, step=5000)

    alloc_mode = st.radio("📊 分配模式", ["smart", "equal"],
        format_func=lambda x: {"smart": "🧠 智能（跌越深分越多）", "equal": "⚖️ 等額"}[x])

    st.markdown("---")
    st.caption("⚠️ 僅供研究參考，不構成投資建議。")


# ─────────────────────────────────────────────
# Parse & Fetch
# ─────────────────────────────────────────────
raw = [t.strip().upper() for t in ticker_input.replace("，", ",").replace(" ", ",").split(",") if t.strip()]
seen = set()
tickers = []
for t in raw:
    if t and t not in seen:
        seen.add(t)
        tickers.append(t)
tickers = tickers[:10]

if not tickers:
    st.warning("請輸入至少一個股票代號。")
    st.stop()

with st.spinner(f"載入 {len(tickers)} 檔數據中..."):
    raw_data = fetch_all(tickers, lookback)

all_data, all_m, all_info, failed = {}, {}, {}, []
for t in tickers:
    r = raw_data.get(t, {})
    df = r.get("data", pd.DataFrame())
    info = r.get("info", {})
    if df.empty:
        failed.append(t); continue
    m = calc_pullback(df)
    if not m:
        failed.append(t); continue
    all_data[t] = df; all_m[t] = m; all_info[t] = info

if failed:
    st.warning(f"無法取得：{', '.join(failed)}")

valid = [t for t in tickers if t in all_m]
if not valid:
    st.error("所有標的無法取得數據，請確認代號。")
    st.stop()

sorted_t = sorted(valid, key=lambda t: all_m[t]["pb"])
weights = calc_weights(all_m) if alloc_mode == "smart" else {t: 1/len(valid) for t in valid}

# ─────────────────────────────────────────────
# HERO BAR
# ─────────────────────────────────────────────
avg_pb = np.mean([all_m[t]["pb"] for t in valid])
avg_rsi = np.mean([all_m[t]["rsi"] for t in valid if all_m[t]["rsi"]])
deepest_t = sorted_t[0]
deepest_pb = all_m[deepest_t]["pb"]

# --- 這裡開始覆蓋 ---
# 先把回顧期間轉換成中文，避免在 HTML 裡面寫複雜邏輯
period_names = {"6mo": "6個月", "1y": "1年", "2y": "2年"}
display_period = period_names.get(lookback, lookback)

st.markdown(f"""
<div class="hero-bar">
    <div class="hero-left">
        <h1>📉 多標的回檔分析</h1>
        <div class="sub">{len(valid)} 檔標標的 · {display_period} 回顧 · {datetime.now().strftime("%Y.%m.%d")}</div>
    </div>
    <div class="hero-stats">
        <div class="hero-stat">
            <div class="val" style="color:{RED};">{avg_pb:.1f}%</div>
            <div class="lbl">平均回檔</div>
        </div>
        <div class="hero-stat">
            <div class="val" style="color:{AMBER};">{avg_rsi:.0f}</div>
            <div class="lbl">平均 RSI</div>
        </div>
        <div class="hero-stat">
            <div class="val" style="color:{get_color(valid.index(deepest_t))};">{deepest_t}</div>
            <div class="lbl">跌最深</div>
        </div>
        <div class="hero-stat">
            <div class="val" style="color:{BLUE};">${budget:,.0f}</div>
            <div class="lbl">總預算</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
# --- 覆蓋到這裡結束 ---

# ─────────────────────────────────────────────
# QUICK SCAN CARDS
# ─────────────────────────────────────────────
cards_html = '<div class="scan-grid">'
for i, t in enumerate(sorted_t):
    m = all_m[t]
    info = all_info.get(t, {})
    name = info.get("shortName", t)
    color = get_color(valid.index(t))
    sig_text, sig_class = get_signal(m["pb"], m["rsi"])
    rsi_str = fmt(m["rsi"], ".0f")
    pe = info.get("trailingPE")
    pe_str = fmt(pe, ".0f") if pe else "—"
    ma200_d = ma_dist(m["cur"], m["ma200"])
    ma200_str = f'{ma200_d:+.1f}%' if ma200_d is not None else "—"

    cards_html += f'''
    <div class="scan-card">
        <div class="accent-bar" style="background:{color};"></div>
        <div style="display:flex;justify-content:space-between;align-items:start;">
            <div>
                <div class="ticker" style="color:{color};">{t}</div>
                <div class="name">{name}</div>
            </div>
            <div class="sig {sig_class}"><span class="dot"></span>{sig_text}</div>
        </div>
        <div class="price-row">
            <span class="price">${m["cur"]:.2f}</span>
            <span class="change" style="color:{RED};">{m["pb"]:.1f}%</span>
        </div>
        <div class="mini-stats">
            <div class="mini-stat"><div class="v" style="color:{AMBER};">{rsi_str}</div><div class="l">RSI</div></div>
            <div class="mini-stat"><div class="v">{ma200_str}</div><div class="l">vs 200MA</div></div>
            <div class="mini-stat"><div class="v">{m["vol_ratio"]:.1f}x</div><div class="l">量比</div></div>
            <div class="mini-stat"><div class="v">{pe_str}</div><div class="l">P/E</div></div>
        </div>
    </div>'''
cards_html += '</div>'
st.markdown(cards_html, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SEC 1: PULLBACK RANKING CHART
# ─────────────────────────────────────────────
st.markdown(f'<div class="sec-head"><div class="sec-num" style="background:rgba(239,68,68,0.12);color:{RED};">01</div><div class="sec-title">回檔幅度排名</div></div>', unsafe_allow_html=True)

rank_fig = go.Figure()
for i, t in enumerate(reversed(sorted_t)):
    m = all_m[t]
    color = get_color(valid.index(t))
    rank_fig.add_trace(go.Bar(
        y=[t], x=[abs(m["pb"])],
        orientation="h", name=t,
        marker=dict(color=color, cornerradius=4),
        text=[f'{m["pb"]:.1f}%'],
        textposition="outside",
        textfont=dict(family="JetBrains Mono", size=12, color=TEXT),
        hovertemplate=f'{t}: 回檔 %{{x:.1f}}%<br>現價 ${m["cur"]:.2f}<br>高點 ${m["high"]:.2f}<extra></extra>',
    ))

rank_fig.update_layout(
    height=max(180, len(valid) * 50),
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="JetBrains Mono, Noto Sans TC", size=12),
    showlegend=False,
    margin=dict(l=60, r=80, t=10, b=10),
    xaxis=dict(title="回檔幅度 (%)", gridcolor=BORDER, zeroline=False),
    yaxis=dict(gridcolor="rgba(0,0,0,0)"),
    bargap=0.3,
)
st.plotly_chart(rank_fig, use_container_width=True)


# ─────────────────────────────────────────────
# SEC 2: RADAR + COMPARISON
# ─────────────────────────────────────────────
st.markdown(f'<div class="sec-head"><div class="sec-num" style="background:rgba(59,130,246,0.12);color:{BLUE};">02</div><div class="sec-title">多維度技術指標對比</div></div>', unsafe_allow_html=True)

col_radar, col_table = st.columns([1, 1])

with col_radar:
    # Radar chart
    categories = ["回檔深度", "RSI 吸引力", "量能活躍度", "均線支撐", "估值合理度"]
    radar_fig = go.Figure()

    for i, t in enumerate(sorted_t[:6]):  # max 6 on radar for readability
        m = all_m[t]
        info = all_info.get(t, {})
        
        # --- 這裡開始置換 (確保數值都在 0-100 之間) ---
        # 1. 回檔深度：40% 為滿分
        pb_score = min(max(abs(m["pb"]) / 40 * 100, 0), 100)
        
        # 2. RSI 吸引力：RSI 越低分數越高
        rsi_val = m.get("rsi") or 50
        rsi_score = min(max((70 - rsi_val) / 40 * 100, 0), 100)
        
        # 3. 量能活躍度：2倍均量為滿分
        vol_score = min(max(m["vol_ratio"] / 2 * 100, 0), 100)
        
        # 4. 均線支撐：站穩 MA200 以上 0-25% 區間
        ma200_d = ma_dist(m["cur"], m["ma200"]) or 0
        ma_score = min(max(50 + ma200_d * 2, 0), 100)
        
        # 5. 估值合理度：P/E 越低分數越高
        pe = info.get("forwardPE") or info.get("trailingPE") or 30
        pe_score = min(max(100 - pe * 1.5, 0), 100)

        values = [pb_score, rsi_score, vol_score, ma_score, pe_score]
        # --- 置換到此結束 ---

        values = [pb_score, rsi_score, vol_score, ma_score, pe_score]
        color = get_color(valid.index(t))

        # 定義透明度顏色 (把原本會報錯的那行換成下面這串)
        rgba_color = color.replace('#', '')
        r, g, b = int(rgba_color[:2], 16), int(rgba_color[2:4], 16), int(rgba_color[4:6], 16)
        
        radar_fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            name=t,
            line=dict(color=color, width=2),
            fill="toself",
            fillcolor=f"rgba({r}, {g}, {b}, 0.15)",  # 強制轉成標準 rgba 格式
        ))

    radar_fig.update_layout(
        height=380,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Noto Sans TC, sans-serif", size=11),
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100], gridcolor=BORDER, linecolor=BORDER),
            angularaxis=dict(gridcolor=BORDER, linecolor=BORDER),
        ),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(size=10)),
        margin=dict(l=40, r=40, t=20, b=60),
    )
    st.plotly_chart(radar_fig, use_container_width=True)

with col_table:
    rows = []
    for t in sorted_t:
        m = all_m[t]
        info = all_info.get(t, {})
        ma20_d = ma_dist(m["cur"], m["ma20"])
        ma50_d = ma_dist(m["cur"], m["ma50"])
        ma200_d = ma_dist(m["cur"], m["ma200"])
        macd_s = "🟢 多" if m["macd"] and m["macd_sig"] and m["macd"] > m["macd_sig"] else "🔴 空"
        rows.append({
            "標的": t,
            "現價": f'${m["cur"]:.2f}',
            "回檔": f'{m["pb"]:.1f}%',
            "RSI": fmt(m["rsi"]),
            "MACD": macd_s,
            "vs MA50": f'{ma50_d:+.1f}%' if ma50_d is not None else "—",
            "vs MA200": f'{ma200_d:+.1f}%' if ma200_d is not None else "—",
            "量比": f'{m["vol_ratio"]:.1f}x',
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=380)


# Normalized price chart
st.markdown("##### 📈 相對表現對比（基期 = 100）")
norm_fig = go.Figure()
for t in sorted_t:
    df = all_data[t]
    base = df["Close"].iloc[0]
    norm_fig.add_trace(go.Scatter(
        x=df.index, y=df["Close"] / base * 100, name=t,
        line=dict(color=get_color(valid.index(t)), width=2),
    ))
norm_fig.update_layout(
    height=340, template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="JetBrains Mono", size=11),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
    margin=dict(l=40, r=20, t=10, b=30),
    xaxis=dict(gridcolor=BORDER), yaxis=dict(gridcolor=BORDER, title=""),
    hovermode="x unified",
)
st.plotly_chart(norm_fig, use_container_width=True)


# ─────────────────────────────────────────────
# SEC 3: ALLOCATION
# ─────────────────────────────────────────────
st.markdown(f'<div class="sec-head"><div class="sec-num" style="background:rgba(139,92,246,0.12);color:{PURPLE};">03</div><div class="sec-title">資金分配建議（${budget:,.0f}）</div></div>', unsafe_allow_html=True)

alloc_col1, alloc_col2 = st.columns([1, 1.2])

with alloc_col1:
    # Donut chart
    donut_fig = go.Figure(go.Pie(
        labels=[t for t in sorted_t],
        values=[weights[t] * budget for t in sorted_t],
        hole=0.55,
        marker=dict(colors=[get_color(valid.index(t)) for t in sorted_t]),
        textinfo="label+percent",
        textfont=dict(family="JetBrains Mono", size=11),
        hovertemplate='%{label}<br>$%{value:,.0f}<br>%{percent}<extra></extra>',
    ))
    donut_fig.update_layout(
        height=340,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Noto Sans TC", size=11),
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        annotations=[dict(text=f"${budget:,.0f}", x=0.5, y=0.5, font=dict(size=16, family="JetBrains Mono", color=TEXT_DIM), showarrow=False)],
    )
    st.plotly_chart(donut_fig, use_container_width=True)

with alloc_col2:
    alloc_rows = []
    for t in sorted_t:
        w = weights[t]
        d = budget * w
        m = all_m[t]
        alloc_rows.append({
            "標的": t,
            "比例": f"{w*100:.1f}%",
            "金額": f"${d:,.0f}",
            "可買股數": int(d / m["cur"]),
            "回檔": f'{m["pb"]:.1f}%',
            "RSI": fmt(m["rsi"]),
        })
    st.dataframe(pd.DataFrame(alloc_rows), use_container_width=True, hide_index=True, height=340)

mode_label = "智能分配：回檔越深 + RSI 越低 → 分配越多" if alloc_mode == "smart" else "等額分配：每檔平均分配"
st.caption(f"📊 {mode_label}")


# ─────────────────────────────────────────────
# SEC 4: PER-TICKER PLANS
# ─────────────────────────────────────────────
st.markdown(f'<div class="sec-head"><div class="sec-num" style="background:rgba(16,185,129,0.12);color:{GREEN};">04</div><div class="sec-title">各標的分段買進計畫</div></div>', unsafe_allow_html=True)

for idx, t in enumerate(sorted_t):
    # --- 這裡就是你要找的起點，請確保這幾行都在 for 迴圈裡面 ---
    m = all_m[t]
    info = all_info.get(t, {})
    df = all_data[t]
    color = get_color(valid.index(t))
    w = weights[t]
    tb = budget * w  # 💰 分配預算：這行絕對不能少
    name = info.get("shortName", t)
    sig_text, sig_class = get_signal(m["pb"], m["rsi"])
    
    # 數據處理與顯示邏輯
    rsi_val = m.get("rsi")
    rsi_display = f"{rsi_val:.1f}" if rsi_val is not None else "—"
    ma200_d = ma_dist(m["cur"], m["ma200"])
    ma200_str = f'{ma200_d:+.1f}%' if ma200_d is not None else "—"
    ma200_color = GREEN if ma200_d and ma200_d > 0 else RED
    vol_color = RED if m["vol_ratio"] > 1.5 else (AMBER if m["vol_ratio"] > 1.2 else GREEN)
    rsi_color = GREEN if rsi_val and rsi_val < 35 else (RED if rsi_val and rsi_val > 65 else AMBER)
    pe = info.get("trailingPE")
    pe_str = f'{pe:.1f}' if pe else "—"

    # 繪製深藍色數據卡片
    st.markdown(f"""
    <div class="ticker-section">
        <div class="top-row">
            <span class="tk" style="color:{color};">{t}</span>
            <span class="nm">{name}</span>
            <span class="sig {sig_class}"><span class="dot"></span>{sig_text}</span>
            <span class="budget-tag">💰 ${tb:,.0f}（{w*100:.1f}%）</span>
        </div>
        <div class="metrics-row">
            <div class="m-item"><div class="mv" style="color:{BLUE};">${m["cur"]:.2f}</div><div class="ml">現價</div></div>
            <div class="m-item"><div class="mv" style="color:{RED};">{m["pb"]:.1f}%</div><div class="ml">回檔</div></div>
            <div class="m-item"><div class="mv" style="color:{rsi_color};">{rsi_display}</div><div class="ml">RSI</div></div>
            <div class="m-item"><div class="mv" style="color:{ma200_color};">{ma200_str}</div><div class="ml">vs 200MA</div></div>
            <div class="m-item"><div class="mv" style="color:{vol_color};">{m["vol_ratio"]:.2f}x</div><div class="ml">量比</div></div>
            <div class="m-item"><div class="mv">{pe_str}</div><div class="ml">P/E</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SEC 5: MASTER TABLE
# ─────────────────────────────────────────────
st.markdown(f'<div class="sec-head"><div class="sec-num" style="background:rgba(245,158,11,0.12);color:{AMBER};">05</div><div class="sec-title">總覽摘要表</div></div>', unsafe_allow_html=True)

master = []
for t in sorted_t:
    m = all_m[t]
    info = all_info.get(t, {})
    w = weights[t]
    sig_text, _ = get_signal(m["pb"], m["rsi"])
    plan = gen_plan(m, budget * w)
    entries = [p for p in plan if p["pct"] > 0]
    first_e = entries[0]["pt"] if entries else m["cur"]
    stops = [p for p in plan if p["pct"] == -100]
    stop_p = stops[0]["pt"] if stops else m["cur"] * 0.9

    master.append({
        "標的": t,
        "公司": info.get("shortName", t)[:18],
        "現價": f'${m["cur"]:.2f}',
        "回檔": f'{m["pb"]:.1f}%',
        "RSI": fmt(m["rsi"]),
        "MACD": "🟢" if m["macd"] and m["macd_sig"] and m["macd"] > m["macd_sig"] else "🔴",
        "訊號": sig_text,
        "分配": f'${budget*w:,.0f}',
        "首批進場": f'${first_e:.2f}',
        "停損": f'${stop_p:.2f}',
    })

st.dataframe(pd.DataFrame(master), use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────
with st.expander("⚠️ 風險提示"):
    st.markdown("""
    1. **本工具僅供研究參考，不構成任何投資建議。**
    2. 技術分析無法預測突發事件（財報爆雷、地緣衝突等）。
    3. 分段買進計畫基於歷史價格模式，實際執行需依市場情況調整。
    4. 停損紀律至關重要 — 寧可小虧出場。
    5. 建議搭配基本面分析，確認回檔原因。
    6. 過去表現不代表未來結果。
    """)

st.caption(f"📊 Yahoo Finance · {', '.join(valid)} · {datetime.now().strftime('%Y-%m-%d %H:%M')} · 不構成投資建議")