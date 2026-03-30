"""
📉 美股回檔分析 & 分段買進建議器 v4.0

📱 行動裝置全面優化版

使用方式:
1. pip install streamlit yfinance plotly pandas numpy
2. streamlit run usstock.py
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
    page_title="美股回檔分析器",
    page_icon="📉",
    layout="wide",
    initial_sidebar_state="collapsed",  # 手機預設收起側邊欄
)

# ─────────────────────────────────────────────
# Password Gate
# ─────────────────────────────────────────────

APP_PASSWORD = "paige2026"  # ← 改成你的密碼

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if st.session_state.authenticated:
        return True

    st.markdown("""
    <div style="display:flex;justify-content:center;align-items:center;min-height:50vh;">
        <div style="text-align:center;">
            <div style="font-size:3rem;margin-bottom:12px;">🔒</div>
            <div style="font-size:1.1rem;font-weight:600;margin-bottom:20px;">美股回檔分析器</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        pwd = st.text_input("請輸入密碼", type="password", key="pwd_input")
        if st.button("登入", use_container_width=True):
            if pwd == APP_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("密碼錯誤")
    return False

if not check_password():
    st.stop()

# ─────────────────────────────────────────────
# Colors
# ─────────────────────────────────────────────

COLORS = ["#76b900","#2d6cdf","#e31937","#f59e0b","#8b5cf6","#06b6d4","#ec4899","#14b8a6","#f97316","#6366f1"]
S, S2, BD, TD = "#111827", "#1a2332", "#1f2e40", "#8b9bb4"
GR, RD, AM, BL, PR = "#10b981", "#ef4444", "#f59e0b", "#3b82f6", "#8b5cf6"

def gc(i): return COLORS[i % len(COLORS)]

# ─────────────────────────────────────────────
# Mobile-first CSS
# ─────────────────────────────────────────────

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&family=JetBrains+Mono:wght@400;600;700&display=swap');

[data-testid="stAppViewContainer"] {{ font-family: 'Noto Sans TC', -apple-system, sans-serif; }}
[data-testid="stSidebar"] {{ background: {S}; }}

/* 手機上縮小整體 padding */
.block-container {{ padding: 1rem 0.8rem !important; max-width: 100% !important; }}
@media (min-width: 768px) {{ .block-container {{ padding: 2rem 1rem !important; }} }}

.mono {{ font-family: 'JetBrains Mono', monospace; }}

/* ── Hero ── */
.hero {{
    background: linear-gradient(135deg, {S} 0%, {S2} 100%);
    border: 1px solid {BD};
    border-radius: 14px;
    padding: 16px 18px;
    margin-bottom: 20px;
}}
.hero h1 {{
    font-size: 1.2rem; font-weight: 800; margin: 0 0 4px;
    background: linear-gradient(135deg, #e2e8f0, #8b9bb4);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}}
.hero .sub {{ font-size: 0.75rem; color: {TD}; }}
.hero-stats {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    margin-top: 12px;
}}
.hero-stat {{ text-align: center; }}
.hero-stat .val {{ font-family: 'JetBrains Mono', monospace; font-size: 1.15rem; font-weight: 700; }}
.hero-stat .lbl {{ font-size: 0.6rem; color: {TD}; text-transform: uppercase; letter-spacing: 0.3px; }}
@media (min-width: 768px) {{
    .hero {{ padding: 24px 28px; }}
    .hero h1 {{ font-size: 1.5rem; }}
    .hero-stat .val {{ font-size: 1.4rem; }}
}}

/* ── Scan Cards ── */
.scan-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-bottom: 24px;
}}
@media (min-width: 768px) {{ .scan-grid {{ grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }} }}
.scan-card {{
    background: {S}; border: 1px solid {BD}; border-radius: 12px;
    padding: 14px; position: relative; overflow: hidden;
}}
.scan-card .bar {{ position: absolute; top:0; left:0; right:0; height: 3px; }}
.scan-card .tk {{ font-family:'JetBrains Mono',monospace; font-size:1rem; font-weight:700; margin-top:3px; }}
.scan-card .nm {{ font-size:0.65rem; color:{TD}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; margin-bottom:6px; }}
.scan-card .pr {{ display:flex; align-items:baseline; gap:6px; margin-bottom:4px; }}
.scan-card .pr .p {{ font-family:'JetBrains Mono',monospace; font-size:1.15rem; font-weight:600; }}
.scan-card .pr .c {{ font-family:'JetBrains Mono',monospace; font-size:0.75rem; font-weight:600; }}
.scan-card .ms {{ display:grid; grid-template-columns:1fr 1fr; gap:4px; margin-top:8px; padding-top:8px; border-top:1px solid {BD}; }}
.scan-card .ms .mi .v {{ font-family:'JetBrains Mono',monospace; font-size:0.75rem; font-weight:600; }}
.scan-card .ms .mi .l {{ font-size:0.55rem; color:{TD}; text-transform:uppercase; }}

/* ── Signal ── */
.sig {{ display:inline-flex; align-items:center; gap:4px; padding:2px 8px; border-radius:5px; font-size:0.65rem; font-weight:600; }}
.sig-buy {{ background:rgba(16,185,129,0.12); color:{GR}; }}
.sig-watch {{ background:rgba(245,158,11,0.12); color:{AM}; }}
.sig-caution {{ background:rgba(239,68,68,0.12); color:{RD}; }}
.sig .dot {{ width:5px; height:5px; border-radius:50%; display:inline-block; }}
.sig-buy .dot {{ background:{GR}; }} .sig-watch .dot {{ background:{AM}; }} .sig-caution .dot {{ background:{RD}; }}

/* ── Section Head ── */
.sh {{ display:flex; align-items:center; gap:10px; margin:28px 0 14px; padding-bottom:10px; border-bottom:1px solid {BD}; }}
.sh .n {{ width:28px;height:28px;display:flex;align-items:center;justify-content:center;border-radius:7px;font-family:'JetBrains Mono',monospace;font-size:0.75rem;font-weight:700;flex-shrink:0; }}
.sh .t {{ font-size:1.05rem; font-weight:700; }}
@media (min-width:768px) {{ .sh .t {{ font-size: 1.2rem; }} }}

/* ── Ticker Block ── */
.tb {{
    background:{S}; border:1px solid {BD}; border-radius:12px;
    padding:14px 16px; margin-top:20px; margin-bottom:10px;
}}
.tb .tr {{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; }}
.tb .tk {{ font-family:'JetBrains Mono',monospace; font-size:1.2rem; font-weight:800; }}
.tb .nm {{ color:{TD}; font-size:0.82rem; }}
.tb .bt {{ margin-left:auto; font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:{TD}; background:{S2}; padding:3px 10px; border-radius:6px; }}
.tb .mr {{
    display:grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 6px;
    margin-top: 12px;
}}
@media (min-width:768px) {{ .tb .mr {{ grid-template-columns: repeat(6, 1fr); }} }}
.tb .mi {{ background:{S2}; border-radius:7px; padding:8px 6px; text-align:center; }}
.tb .mi .v {{ font-family:'JetBrains Mono',monospace; font-size:0.92rem; font-weight:600; }}
.tb .mi .l {{ font-size:0.55rem; color:{TD}; text-transform:uppercase; letter-spacing:0.3px; margin-top:1px; }}

/* ── Step Plan ── */
.sp {{ display:flex; flex-direction:column; margin:10px 0 16px; }}
.si {{ display:flex; gap:10px; padding-bottom:14px; }}
.si:last-child {{ padding-bottom:0; }}
.sl {{ display:flex; flex-direction:column; align-items:center; flex-shrink:0; width:24px; }}
.sd {{ width:12px;height:12px;border-radius:50%;border:2px solid {BD};background:{S};z-index:1;flex-shrink:0; }}
.sd.buy {{ border-color:{GR};background:rgba(16,185,129,0.2); }}
.sd.stop {{ border-color:{RD};background:rgba(239,68,68,0.2); }}
.sd.wait {{ border-color:{AM};background:rgba(245,158,11,0.2); }}
.sc {{ width:2px;flex:1;background:{BD};min-height:14px; }}
.sx {{
    flex:1;background:{S};border:1px solid {BD};border-radius:9px;padding:10px 14px;
}}
.sx .hd {{ display:flex;align-items:center;justify-content:space-between;gap:6px;margin-bottom:4px;flex-wrap:wrap; }}
.sx .pn {{ font-weight:700;font-size:0.85rem; }}
.sx .pt {{ font-family:'JetBrains Mono',monospace;font-size:0.7rem;padding:2px 8px;border-radius:5px;font-weight:600; }}
.sx .pt.buy {{ background:rgba(16,185,129,0.1);color:{GR}; }}
.sx .pt.stop {{ background:rgba(239,68,68,0.1);color:{RD}; }}
.sx .pt.wait {{ background:rgba(245,158,11,0.1);color:{AM}; }}
.sx .tg {{ font-size:0.78rem;color:{TD};line-height:1.5; }}
.sx .pp {{ font-family:'JetBrains Mono',monospace;font-size:1rem;font-weight:700; }}
.sx .wh {{ font-size:0.68rem;color:#6b7280;margin-top:3px; }}

/* ── Multi-Timeframe ── */
.mtf-grid {{
    display: grid;
    grid-template-columns: 1fr;
    gap: 6px;
    margin: 8px 0 12px;
}}
.mtf-row {{
    display: grid;
    grid-template-columns: 70px 1fr 1fr 1fr 1fr;
    gap: 4px;
    align-items: center;
    background: {S2};
    border-radius: 8px;
    padding: 8px 10px;
}}
.mtf-row.hdr {{
    background: transparent;
    padding: 4px 10px;
}}
.mtf-row .tf-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    font-weight: 600;
}}
.mtf-row .tf-val {{
    font-size: 0.75rem;
    text-align: center;
}}
.mtf-row .tf-hdr {{
    font-size: 0.6rem;
    color: {TD};
    text-transform: uppercase;
    text-align: center;
    letter-spacing: 0.3px;
}}
.mtf-verdict {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 8px;
    font-size: 0.82rem;
    font-weight: 600;
    margin: 8px 0 4px;
}}
.mtf-verdict.bullish {{ background: rgba(16,185,129,0.1); color: {GR}; }}
.mtf-verdict.bearish {{ background: rgba(239,68,68,0.1); color: {RD}; }}
.mtf-verdict.mixed {{ background: rgba(245,158,11,0.1); color: {AM}; }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Core Functions
# ─────────────────────────────────────────────

@st.cache_data(ttl=300)
def fetch_data(ticker, period="1y"):
    try: 
        df = yf.Ticker(ticker).history(period=period)
    except: 
        return pd.DataFrame()
    
    if df.empty or len(df) < 20: 
        return pd.DataFrame()
        
    df["MA20"]=df["Close"].rolling(20).mean(); df["MA50"]=df["Close"].rolling(50).mean(); df["MA200"]=df["Close"].rolling(200).mean()
    d=df["Close"].diff(); g=d.where(d>0,0).rolling(14).mean(); l=(-d.where(d<0,0)).rolling(14).mean(); rs=g/l; df["RSI"]=100-(100/(1+rs))
    e12=df["Close"].ewm(span=12).mean(); e26=df["Close"].ewm(span=26).mean(); df["MACD"]=e12-e26; df["MACD_Signal"]=df["MACD"].ewm(span=9).mean()
    df["Vol_MA20"]=df["Volume"].rolling(20).mean()
    
    # Bollinger Bands
    bb_std=df["Close"].rolling(20).std()
    df["BB_Upper"]=df["MA20"]+2*bb_std; df["BB_Lower"]=df["MA20"]-2*bb_std
    
    # ATR (14)
    tr=pd.concat([df["High"]-df["Low"],(df["High"]-df["Close"].shift()).abs(),(df["Low"]-df["Close"].shift()).abs()],axis=1).max(axis=1)
    df["ATR14"]=tr.rolling(14).mean()
    return df

@st.cache_data(ttl=600)
def fetch_info(ticker):
    try: 
        return yf.Ticker(ticker).info
    except: 
        return {}

def fetch_all(tickers, period):
    res = {}
    with ThreadPoolExecutor(max_workers=min(len(tickers),6)) as ex:
        fd={ex.submit(fetch_data,t,period):t for t in tickers}
        fi={ex.submit(fetch_info,t):t for t in tickers}
        
        for f in as_completed(fd):
            t=fd[f]
            try: res.setdefault(t,{})["data"]=f.result()
            except: res.setdefault(t,{})["data"]=pd.DataFrame()
            
        for f in as_completed(fi):
            t=fi[f]
            try: res.setdefault(t,{})["info"]=f.result()
            except: res.setdefault(t,{})["info"]={}
    return res

# ── Multi-timeframe data ──

@st.cache_data(ttl=300)
def fetch_weekly(ticker):
    """Fetch weekly data for multi-timeframe analysis."""
    try:
        df = yf.Ticker(ticker).history(period="2y", interval="1wk")
    except: 
        return pd.DataFrame()
    if df.empty or len(df) < 10: 
        return pd.DataFrame()
    df["MA10"]=df["Close"].rolling(10).mean()  # ~50 day
    df["MA40"]=df["Close"].rolling(40).mean()  # ~200 day
    d=df["Close"].diff(); g=d.where(d>0,0).rolling(14).mean(); l=(-d.where(d<0,0)).rolling(14).mean(); rs=g/l; df["RSI"]=100-(100/(1+rs))
    e12=df["Close"].ewm(span=12).mean(); e26=df["Close"].ewm(span=26).mean(); df["MACD"]=e12-e26; df["MACD_Signal"]=df["MACD"].ewm(span=9).mean()
    return df

@st.cache_data(ttl=300)
def fetch_monthly(ticker):
    """Fetch monthly data for multi-timeframe analysis."""
    try:
        df = yf.Ticker(ticker).history(period="5y", interval="1mo")
    except: 
        return pd.DataFrame()
    if df.empty or len(df) < 6: 
        return pd.DataFrame()
    df["MA6"]=df["Close"].rolling(6).mean()   # ~6 month
    df["MA12"]=df["Close"].rolling(12).mean()  # ~1 year
    d=df["Close"].diff(); g=d.where(d>0,0).rolling(14).mean(); l=(-d.where(d<0,0)).rolling(14).mean(); rs=g/l; df["RSI"]=100-(100/(1+rs))
    e12=df["Close"].ewm(span=12).mean(); e26=df["Close"].ewm(span=26).mean(); df["MACD"]=e12-e26; df["MACD_Signal"]=df["MACD"].ewm(span=9).mean()
    return df

def calc_tf_signal(df, tf_label):
    """Calculate trend signal for a given timeframe's dataframe."""
    if df.empty or len(df) < 5:
        return {"tf": tf_label, "trend": "—", "rsi": None, "macd": "—", "ma_status": "—"}

    cur = df["Close"].iloc[-1]
    rsi_val = df["RSI"].iloc[-1] if "RSI" in df.columns and not pd.isna(df["RSI"].iloc[-1]) else None

    # MACD
    macd_ok = False
    if "MACD" in df.columns and "MACD_Signal" in df.columns:
        mv = df["MACD"].iloc[-1]; sv = df["MACD_Signal"].iloc[-1]
        if not pd.isna(mv) and not pd.isna(sv):
            macd_ok = mv > sv
    macd_str = "🟢 多" if macd_ok else "🔴 空"

    # MA trend
    ma_cols = [c for c in df.columns if c.startswith("MA")]
    ma_status = "—"
    if len(ma_cols) >= 2:
        short_ma = df[ma_cols[0]].iloc[-1]
        long_ma = df[ma_cols[1]].iloc[-1]
        if not pd.isna(short_ma) and not pd.isna(long_ma):
            if short_ma > long_ma:
                ma_status = "🟢 短均>長均"
            else:
                ma_status = "🔴 短均<長均"

    # Overall trend
    bullish = 0
    if macd_ok: bullish += 1
    if rsi_val and rsi_val > 50: bullish += 1
    if ma_status.startswith("🟢"): bullish += 1

    if bullish >= 2:
        trend = "🟢 偏多"
    elif bullish == 0:
        trend = "🔴 偏空"
    else:
        trend = "🟡 中性"

    return {
        "tf": tf_label,
        "trend": trend,
        "rsi": rsi_val,
        "macd": macd_str,
        "ma_status": ma_status,
        "close": cur,
    }

def calc_pb(df):
    if df.empty or len(df)<20: return {}
    hi=df["High"].max(); hd=df["High"].idxmax(); cur=df["Close"].iloc[-1]; lo=df["Low"].min()
    def s(c):
        v=df[c].iloc[-1] if c in df.columns else None
        return v if v is not None and not pd.isna(v) else None
    
    vol=df["Volume"].iloc[-1]; av=s("Vol_MA20") or vol

    # Find recent swing lows (local minima in last 60 bars)
    swing_lows = []
    lookback = min(60, len(df)-2)
    close_vals = df["Close"].values
    for i in range(len(df)-lookback, len(df)-1):
        if i > 0 and i < len(df)-1:
            if close_vals[i] < close_vals[i-1] and close_vals[i] < close_vals[i+1]:
                swing_lows.append(close_vals[i])
    # Keep unique levels rounded to avoid duplicates
    swing_lows = sorted(set(round(x, 2) for x in swing_lows))
    # Filter only those below current price
    support_lows = [x for x in swing_lows if x < cur]

    return {
        "cur":cur, "high":hi, "high_date":hd, "low":lo,
        "pb":(cur-hi)/hi*100,
        "ma20":s("MA20"), "ma50":s("MA50"), "ma200":s("MA200"),
        "rsi":s("RSI"), "macd":s("MACD"), "macd_sig":s("MACD_Signal"),
        "vol_ratio":vol/av if av>0 else 1.0,
        "bb_lower":s("BB_Lower"), "bb_upper":s("BB_Upper"),
        "atr":s("ATR14"),
        "support_lows": support_lows[-3:] if support_lows else [],  # nearest 3 swing lows
    }

def mad(p,ma): return (p-ma)/ma*100 if ma and ma>0 else None
def fmt(v,sp=".1f",fb="—"): return f"{v:{sp}}" if v is not None else fb

def get_sig(pb,rsi):
    p=abs(pb)
    if p>=20 and rsi and rsi<35: return "超賣 — 強烈關注","sig-buy"
    elif p>=10 and rsi and rsi<45: return "分批布局","sig-buy"
    elif p>=10: return "觀察中","sig-watch"
    elif p>=5: return "初步回檔","sig-watch"
    else: return "未明顯回檔","sig-caution"

def gen_plan(m, budget, tf_verdict=None):
    """
    多因子分段買進策略引擎 v2 — 均衡型
    """
    p = m["cur"]
    hi = m["high"]
    pb = abs(m["pb"])
    ma20 = m.get("ma20")
    ma50 = m.get("ma50")
    ma200 = m.get("ma200")
    rsi = m.get("rsi") or 50
    bb_lower = m.get("bb_lower")
    atr = m.get("atr") or (p * 0.02)  # fallback ~2%
    vol_ratio = m.get("vol_ratio", 1.0)
    swing_lows = m.get("support_lows", [])

    # FACTOR 1: 支撐位排序（由高到低）
    supports = []
    if ma20 and ma20 < p:
        supports.append(("20日均線", round(ma20, 2)))
    if ma50 and ma50 < p:
        supports.append(("50日均線", round(ma50, 2)))
    if ma200 and ma200 < p:
        supports.append(("200日均線", round(ma200, 2)))
    if bb_lower and bb_lower < p:
        supports.append(("布林下軌", round(bb_lower, 2)))
    for i, sl in enumerate(reversed(swing_lows)):
        if sl < p:
            supports.append((f"前波低點", round(sl, 2)))

    # Deduplicate by proximity (within 1.5% = same level)
    unique_supports = []
    for name, price in sorted(supports, key=lambda x: -x[1]):  # high to low
        if not unique_supports or abs(price - unique_supports[-1][1]) / unique_supports[-1][1] > 0.015:
            unique_supports.append((name, price))

    # FACTOR 2: RSI → 倉位權重調節
    if rsi < 25:
        rsi_boost = 1.4   # 極度超賣，首批大幅加碼
    elif rsi < 30:
        rsi_boost = 1.25  # 超賣
    elif rsi < 40:
        rsi_boost = 1.1   # 偏弱
    elif rsi < 50:
        rsi_boost = 1.0   # 中性
    else:
        rsi_boost = 0.8   # 未超賣，減少首批

    # FACTOR 3: 多週期共振 → 積極度
    if tf_verdict == "bullish":
        aggression = 1.2   # 多頭共振，更積極
    elif tf_verdict == "bearish":
        aggression = 0.7   # 空頭共振，更保守
    else:
        aggression = 1.0   # 混合或未知

    # FACTOR 4: 成交量異常 → 觸發訊號
    vol_signal = ""
    if vol_ratio > 2.0:
        vol_signal = "⚡ 量能爆發（>2x均量），可能接近轉折"
    elif vol_ratio > 1.5:
        vol_signal = "📈 量能放大（>1.5x均量），關注止穩訊號"

    # BUILD PLAN — 基於支撐位生成進場階段
    phases = []

    if pb < 3:
        # 幾乎沒回檔
        phases.append({"ph": "觀望", "trig": f"僅回檔 {pb:.1f}%，尚無明顯進場機會",
            "pt": p, "pct": 0, "why": "回檔幅度不足，風險報酬比不佳", "tp": "wait"})
        # 給出預設的等待價位
        wait_p = unique_supports[0][1] if unique_supports else p * 0.93
        wait_name = unique_supports[0][0] if unique_supports else "預估支撐"
        phases.append({"ph": "等待進場", "trig": f"等待回落至 {wait_name} ${wait_p:.2f}",
            "pt": wait_p, "pct": 0, "why": f"距離最近支撐 {wait_name} 還有 {((p-wait_p)/p*100):.1f}% 空間", "tp": "wait"})

    elif len(unique_supports) >= 2:
        # 有足夠支撐位 → 基於實際支撐位分批
        base_alloc = [30, 30, 40]
        
        adj_alloc = [min(45, base_alloc[0] * rsi_boost), 0, 0]
        adj_alloc[1] = base_alloc[1]
        adj_alloc[2] = 100 - adj_alloc[0] - adj_alloc[1]
        
        adj_alloc = [round(a * aggression) for a in adj_alloc]
        total_a = sum(adj_alloc)
        adj_alloc = [round(a / total_a * 100) for a in adj_alloc]
        adj_alloc[2] = 100 - adj_alloc[0] - adj_alloc[1]
        
        s1_name, s1_price = unique_supports[0]
        dist_to_s1 = (p - s1_price) / p * 100
        
        if dist_to_s1 < 2:
            trig1 = f"現價 ${p:.2f} 已接近{s1_name} ${s1_price:.2f}，可建立初始倉位"
            pt1 = p
        else:
            trig1 = f"回落至{s1_name}附近 ${s1_price:.2f}（距現價 {dist_to_s1:.1f}%）"
            pt1 = s1_price
        
        why1 = f"RSI {rsi:.0f}" + ("，超賣區加碼" if rsi < 30 else "")
        if vol_signal:
            why1 += f" · {vol_signal}"
        
        phases.append({"ph": "第一批", "trig": trig1, "pt": pt1,
            "pct": adj_alloc[0], "why": why1, "tp": "buy"})
        
        s2_name, s2_price = unique_supports[1]
        phases.append({"ph": "第二批", "trig": f"下探{s2_name}附近 ${s2_price:.2f}",
            "pt": s2_price, "pct": adj_alloc[1],
            "why": f"攤低成本至更強支撐位", "tp": "buy"})
        
        if len(unique_supports) >= 3 and aggression < 1.0:
            s3_name, s3_price = unique_supports[2]
            phases.append({"ph": "第三批", "trig": f"若再跌至{s3_name} ${s3_price:.2f}",
                "pt": s3_price, "pct": adj_alloc[2],
                "why": "深度支撐，最後一批防守倉", "tp": "buy"})
        else:
            confirm_p = round(pt1 + atr * 1.5, 2) if atr else round(p * 1.05, 2)
            trend_label = "多週期共振向上，積極加碼" if tf_verdict == "bullish" else "突破短期壓力確認反轉"
            phases.append({"ph": "第三批", "trig": f"反彈突破 ${confirm_p:.2f}（ATR確認）",
                "pt": confirm_p, "pct": adj_alloc[2],
                "why": trend_label, "tp": "buy"})

    else:
        step = atr * 1.5 if atr else p * 0.05
        
        adj_pct1 = min(40, round(30 * rsi_boost * aggression))
        adj_pct2 = 30
        adj_pct3 = 100 - adj_pct1 - adj_pct2
        
        phases.append({"ph": "第一批", "trig": f"現價 ${p:.2f} 附近企穩",
            "pt": p, "pct": adj_pct1,
            "why": f"RSI {rsi:.0f}，回檔 {pb:.1f}%" + (f" · {vol_signal}" if vol_signal else ""),
            "tp": "buy"})
        phases.append({"ph": "第二批", "trig": f"再跌 1.5×ATR 至 ${p-step:.2f}",
            "pt": round(p - step, 2), "pct": adj_pct2,
            "why": "基於波動率的動態間距", "tp": "buy"})
        
        if aggression >= 1.0:
            phases.append({"ph": "第三批", "trig": f"反彈確認 ${p+step*0.8:.2f}",
                "pt": round(p + step * 0.8, 2), "pct": adj_pct3,
                "why": "趨勢反轉確認後補滿", "tp": "buy"})
        else:
            phases.append({"ph": "第三批", "trig": f"跌至 ${p-step*2:.2f} 深度承接",
                "pt": round(p - step * 2, 2), "pct": adj_pct3,
                "why": "空頭趨勢下的深度防守", "tp": "buy"})

    # STOP LOSS — 基於 ATR + 最近支撐
    stop_candidates = []
    if ma200 and ma200 > 0:
        stop_candidates.append(ma200 - atr)  
    if unique_supports:
        lowest_support = unique_supports[-1][1]
        stop_candidates.append(lowest_support - atr)  
    stop_candidates.append(p * 0.88)  

    stop_price = round(max(stop_candidates[0] if stop_candidates else p * 0.90, p * 0.85), 2)
    stop_pct = (stop_price / p - 1) * 100

    stop_why = "200MA 下方 1×ATR" if ma200 and stop_price > (ma200 - atr * 1.5) else "最低支撐下方 1×ATR"
    phases.append({
        "ph": "停損", "trig": f"跌破 ${stop_price:.2f}（{stop_pct:.1f}%）",
        "pt": stop_price, "pct": -100,
        "why": f"{stop_why} · ATR=${atr:.2f}", "tp": "stop"
    })

    for x in phases:
        if x["pct"] > 0:
            x["dollar"] = budget * x["pct"] / 100
            x["shares"] = int(x["dollar"] / x["pt"]) if x["pt"] > 0 else 0
        else:
            x["dollar"] = 0
            x["shares"] = 0

    return phases

def calc_w(metrics):
    sc={}
    for t,m in metrics.items():
        sc[t]=max(abs(m["pb"])*0.6+max(0,50-(m["rsi"] or 50))*0.4,1)
    tot=sum(sc.values())
    return {t:s/tot for t,s in sc.items()}

# ─────────────────────────────────────────────
# Controls 
# ─────────────────────────────────────────────

qc = st.columns(4)
with qc[0]:
    if st.button("Mag 7", use_container_width=True): st.session_state["ti"]="AAPL,MSFT,GOOG,AMZN,NVDA,META,TSLA"
with qc[1]:
    if st.button("半導體", use_container_width=True): st.session_state["ti"]="NVDA,AMD,AVGO,TSM,QCOM,INTC"
with qc[2]:
    if st.button("AI 概念", use_container_width=True): st.session_state["ti"]="NVDA,PLTR,MSFT,GOOG,META,CRM"
with qc[3]:
    if st.button("電動車", use_container_width=True): st.session_state["ti"]="TSLA,RIVN,NIO,LI,XPEV,LCID"

c1, c2, c3, c4 = st.columns([3, 1, 1.2, 1])
with c1:
    ti = st.text_input("🔍 股票代號（逗號分隔，最多10檔）", value=st.session_state.get("ti","GOOG,NVDA,TSLA,PLTR,AAPL"), label_visibility="collapsed", placeholder="輸入代號，如 GOOG,NVDA,TSLA")
with c2:
    lk = st.selectbox("期間", ["6mo","1y","2y"], index=1, format_func=lambda x:{"6mo":"6個月","1y":"1年","2y":"2年"}[x], label_visibility="collapsed")
with c3:
    bg = st.number_input("預算", min_value=1000, max_value=10_000_000, value=100_000, step=5000, label_visibility="collapsed")
with c4:
    am = st.selectbox("分配", ["smart","equal"], format_func=lambda x:{"smart":"🧠 智能","equal":"⚖️ 等額"}[x], label_visibility="collapsed")

# ─────────────────────────────────────────────
# Parse & Fetch
# ─────────────────────────────────────────────

raw=[t.strip().upper() for t in ti.replace("，",",").replace(" ",",").split(",") if t.strip()]
seen=set(); tickers=[]
for t in raw:
    if t and t not in seen: 
        seen.add(t)
        tickers.append(t)
tickers=tickers[:10]

if not tickers: 
    st.warning("請輸入至少一個股票代號。")
    st.stop()

with st.spinner(f"載入 {len(tickers)} 檔..."):
    rd=fetch_all(tickers,lk)

all_d,all_m,all_i,fail={},{},{},[]
for t in tickers:
    r=rd.get(t,{})
    df=r.get("data",pd.DataFrame())
    inf=r.get("info",{})
    if df.empty: 
        fail.append(t)
        continue
    m=calc_pb(df)
    if not m: 
        fail.append(t)
        continue
    all_d[t]=df; all_m[t]=m; all_i[t]=inf

if fail: st.warning(f"無法取得：{', '.join(fail)}")
vt=[t for t in tickers if t in all_m]
if not vt: 
    st.error("所有標的無法取得數據。")
    st.stop()

st_t=sorted(vt,key=lambda t:all_m[t]["pb"])
wts=calc_w(all_m) if am=="smart" else {t:1/len(vt) for t in vt}

# ─────────────────────────────────────────────
# HERO
# ─────────────────────────────────────────────

apb=np.mean([all_m[t]["pb"] for t in vt])
arsi=np.mean([all_m[t]["rsi"] for t in vt if all_m[t]["rsi"]])
dt=st_t[0]

pn={"6mo":"6個月","1y":"1年","2y":"2年"}
st.markdown(f"""
<div class="hero">
    <h1>📉 多標的回檔分析</h1>
    <div class="sub">{len(vt)} 檔 · {pn.get(lk,lk)} · {datetime.now().strftime("%Y.%m.%d")}</div>
    <div class="hero-stats">
        <div class="hero-stat"><div class="val" style="color:{RD};">{apb:.1f}%</div><div class="lbl">平均回檔</div></div>
        <div class="hero-stat"><div class="val" style="color:{AM};">{arsi:.0f}</div><div class="lbl">平均RSI</div></div>
        <div class="hero-stat"><div class="val" style="color:{gc(vt.index(dt))};">{dt}</div><div class="lbl">跌最深</div></div>
        <div class="hero-stat"><div class="val" style="color:{BL};">${bg:,.0f}</div><div class="lbl">總預算</div></div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SCAN CARDS
# ─────────────────────────────────────────────

ch='<div class="scan-grid">'
for i,t in enumerate(st_t):
    m=all_m[t]; inf=all_i.get(t,{}); nm=inf.get("shortName",t); co=gc(vt.index(t))
    st_txt,st_cls=get_sig(m["pb"],m["rsi"])
    rs=fmt(m["rsi"],".0f"); pe=inf.get("trailingPE"); ps=fmt(pe,".0f") if pe else "—"
    md=mad(m["cur"],m["ma200"]); ms=f'{md:+.1f}%' if md is not None else "—"
    ch+=f'''<div class="scan-card"><div class="bar" style="background:{co};"></div>
    <div style="display:flex;justify-content:space-between;align-items:start;">
    <div><div class="tk" style="color:{co};">{t}</div><div class="nm">{nm}</div></div>
    <div class="sig {st_cls}"><span class="dot"></span>{st_txt}</div>
    </div>
    <div class="pr"><span class="p">${m["cur"]:.2f}</span><span class="c" style="color:{RD};">{m["pb"]:.1f}%</span></div>
    <div class="ms">
    <div class="mi"><div class="v" style="color:{AM};">{rs}</div><div class="l">RSI</div></div>
    <div class="mi"><div class="v">{ms}</div><div class="l">vs200MA</div></div>
    <div class="mi"><div class="v">{m["vol_ratio"]:.1f}x</div><div class="l">量比</div></div>
    <div class="mi"><div class="v">{ps}</div><div class="l">P/E</div></div>
    </div></div>'''
ch+='</div>'
st.markdown(ch, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SEC 1: RANKING
# ─────────────────────────────────────────────

st.markdown(f'<div class="sh"><div class="n" style="background:rgba(239,68,68,0.12);color:{RD};">01</div><div class="t">回檔幅度排名</div></div>', unsafe_allow_html=True)

rf=go.Figure()
for t in reversed(st_t):
    m=all_m[t]; co=gc(vt.index(t))
    rf.add_trace(go.Bar(y=[t],x=[abs(m["pb"])],orientation="h",marker=dict(color=co),
    text=[f'{m["pb"]:.1f}%'],textposition="outside",textfont=dict(family="JetBrains Mono",size=11,color="#e2e8f0"),
    hovertemplate=f'{t}: %{{x:.1f}}%<br>${m["cur"]:.2f}<extra></extra>',showlegend=False))
rf.update_layout(height=max(160,len(vt)*44),template="plotly_dark",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
font=dict(family="JetBrains Mono",size=11),margin=dict(l=50,r=60,t=5,b=5),
xaxis=dict(title="",gridcolor=BD,zeroline=False),yaxis=dict(gridcolor="rgba(0,0,0,0)"),bargap=0.3)
st.plotly_chart(rf, use_container_width=True)

# ─────────────────────────────────────────────
# SEC 2: COMPARISON
# ─────────────────────────────────────────────

st.markdown(f'<div class="sh"><div class="n" style="background:rgba(59,130,246,0.12);color:{BL};">02</div><div class="t">技術指標對比</div></div>', unsafe_allow_html=True)

# Radar chart
cats=["回檔深度","RSI吸引力","量能","均線支撐","估值"]
rdf=go.Figure()
for t in st_t[:6]:
    m=all_m[t]; inf=all_i.get(t,{})
    pbs=min(max(abs(m["pb"])/40*100,0),100)
    rss=min(max((70-(m["rsi"] or 50))/40*100,0),100)
    vs=min(max(m["vol_ratio"]/2*100,0),100)
    md2=mad(m["cur"],m["ma200"]) or 0; mas=min(max(50+md2*2,0),100)
    pe2=inf.get("forwardPE") or inf.get("trailingPE") or 30; pes=min(max(100-pe2*1.5,0),100)
    vals=[pbs,rss,vs,mas,pes]; co=gc(vt.index(t))
    hx=co.replace('#',''); r,g,b=int(hx[:2],16),int(hx[2:4],16),int(hx[4:6],16)
    rdf.add_trace(go.Scatterpolar(r=vals+[vals[0]],theta=cats+[cats[0]],name=t,line=dict(color=co,width=2),fill="toself",fillcolor=f"rgba({r},{g},{b},0.12)"))
rdf.update_layout(height=320,template="plotly_dark",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
font=dict(family="Noto Sans TC",size=10),
polar=dict(bgcolor="rgba(0,0,0,0)",radialaxis=dict(visible=True,range=[0,100],gridcolor=BD),angularaxis=dict(gridcolor=BD)),
legend=dict(orientation="h",yanchor="bottom",y=-0.2,xanchor="center",x=0.5,font=dict(size=9)),
margin=dict(l=30,r=30,t=15,b=50))
st.plotly_chart(rdf, use_container_width=True)

# Comparison table
rows=[]
for t in st_t:
    m=all_m[t]; inf=all_i.get(t,{})
    ma50d=mad(m["cur"],m["ma50"]); ma200d=mad(m["cur"],m["ma200"])
    mcd="🟢" if m["macd"] and m["macd_sig"] and m["macd"]>m["macd_sig"] else "🔴"
    rows.append({"標的":t,"現價":f'${m["cur"]:.2f}',"回檔":f'{m["pb"]:.1f}%',"RSI":fmt(m["rsi"]),"MACD":mcd,
    "vs50MA":f'{ma50d:+.1f}%' if ma50d is not None else "—","vs200MA":f'{ma200d:+.1f}%' if ma200d is not None else "—","量比":f'{m["vol_ratio"]:.1f}x'})
st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

# Normalized chart
st.markdown("##### 📈 相對表現（基期=100）")
nf=go.Figure()
for t in st_t:
    df=all_d[t]; base=df["Close"].iloc[0]
    nf.add_trace(go.Scatter(x=df.index,y=df["Close"]/base*100,name=t,line=dict(color=gc(vt.index(t)),width=2)))
nf.update_layout(height=300,template="plotly_dark",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
font=dict(family="JetBrains Mono",size=10),
legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1,font=dict(size=9)),
margin=dict(l=35,r=15,t=10,b=25),xaxis=dict(gridcolor=BD),yaxis=dict(gridcolor=BD),hovermode="x unified")
st.plotly_chart(nf, use_container_width=True)

# ─────────────────────────────────────────────
# SEC 3: ALLOCATION
# ─────────────────────────────────────────────

st.markdown(f'<div class="sh"><div class="n" style="background:rgba(139,92,246,0.12);color:{PR};">03</div><div class="t">資金分配（${bg:,.0f}）</div></div>', unsafe_allow_html=True)

# Donut
dnf=go.Figure(go.Pie(labels=st_t,values=[wts[t]*bg for t in st_t],hole=0.55,
marker=dict(colors=[gc(vt.index(t)) for t in st_t]),textinfo="label+percent",
textfont=dict(family="JetBrains Mono",size=10),hovertemplate='%{label}<br>$%{value:,.0f}<br>%{percent}<extra></extra>'))
dnf.update_layout(height=300,template="plotly_dark",paper_bgcolor="rgba(0,0,0,0)",
font=dict(family="Noto Sans TC",size=10),showlegend=False,margin=dict(l=5,r=5,t=5,b=5),
annotations=[dict(text=f"${bg:,.0f}",x=0.5,y=0.5,font=dict(size=14,family="JetBrains Mono",color=TD),showarrow=False)])
st.plotly_chart(dnf, use_container_width=True)

# Allocation table
ar=[]
for t in st_t:
    w=wts[t]; d=bg*w; m=all_m[t]
    ar.append({"標的":t,"比例":f"{w*100:.1f}%","金額":f"${d:,.0f}","可買股數":int(d/m["cur"]),"回檔":f'{m["pb"]:.1f}%',"RSI":fmt(m["rsi"])})
st.dataframe(pd.DataFrame(ar),use_container_width=True,hide_index=True)
ml="智能：跌越深+RSI越低→分越多" if am=="smart" else "等額：每檔平均"
st.caption(f"📊 {ml}")

# ─────────────────────────────────────────────
# SEC 4: PER-TICKER PLANS
# ─────────────────────────────────────────────

st.markdown(f'<div class="sh"><div class="n" style="background:rgba(16,185,129,0.12);color:{GR};">04</div><div class="t">分段買進計畫</div></div>', unsafe_allow_html=True)

for idx,t in enumerate(st_t):
    m=all_m[t]; inf=all_i.get(t,{}); df=all_d[t]; co=gc(vt.index(t))
    w=wts[t]; tb=bg*w; nm=inf.get("shortName",t)
    stx,scl=get_sig(m["pb"],m["rsi"])
    rv=m.get("rsi"); rd2=f"{rv:.1f}" if rv else "—"
    md3=mad(m["cur"],m["ma200"]); ms2=f'{md3:+.1f}%' if md3 is not None else "—"
    mc=GR if md3 and md3>0 else RD; vc=RD if m["vol_ratio"]>1.5 else (AM if m["vol_ratio"]>1.2 else GR)
    rc=GR if rv and rv<35 else (RD if rv and rv>65 else AM)
    pe=inf.get("trailingPE"); ps2=f'{pe:.1f}' if pe else "—"

    st.markdown(f"""
    <div class="tb">
        <div class="tr">
            <span class="tk" style="color:{co};">{t}</span>
            <span class="nm">{nm}</span>
            <span class="sig {scl}"><span class="dot"></span>{stx}</span>
            <span class="bt">💰 ${tb:,.0f}（{w*100:.1f}%）</span>
        </div>
        <div class="mr">
            <div class="mi"><div class="v" style="color:{BL};">${m["cur"]:.2f}</div><div class="l">現價</div></div>
            <div class="mi"><div class="v" style="color:{RD};">{m["pb"]:.1f}%</div><div class="l">回檔</div></div>
            <div class="mi"><div class="v" style="color:{rc};">{rd2}</div><div class="l">RSI</div></div>
            <div class="mi"><div class="v" style="color:{mc};">{ms2}</div><div class="l">vs200MA</div></div>
            <div class="mi"><div class="v" style="color:{vc};">{m["vol_ratio"]:.2f}x</div><div class="l">量比</div></div>
            <div class="mi"><div class="v">{ps2}</div><div class="l">P/E</div></div>
        </div>
    </div>""", unsafe_allow_html=True)

    # K-line chart
    with st.expander(f"📊 {t} K線圖", expanded=(idx==0)):
        kf=go.Figure()
        kf.add_trace(go.Candlestick(x=df.index,open=df["Open"],high=df["High"],low=df["Low"],close=df["Close"],
            increasing_fillcolor=GR,increasing_line_color=GR,decreasing_fillcolor=RD,decreasing_line_color=RD,name="K線"))
        for mc2,mcc,mn in [("MA20",AM,"20MA"),("MA50",BL,"50MA"),("MA200",RD,"200MA")]:
            if mc2 in df.columns: kf.add_trace(go.Scatter(x=df.index,y=df[mc2],name=mn,line=dict(color=mcc,width=1),opacity=0.8))
        kf.add_trace(go.Scatter(x=[m["high_date"]],y=[m["high"]],mode="markers+text",marker=dict(color=AM,size=8,symbol="triangle-down"),
            text=[f'${m["high"]:.0f}'],textposition="top center",textfont=dict(color=AM,size=8),showlegend=False))
        kf.update_layout(height=300,template="plotly_dark",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="JetBrains Mono",size=9),legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1,font=dict(size=8)),
            xaxis_rangeslider_visible=False,margin=dict(l=40,r=5,t=20,b=15),xaxis=dict(gridcolor=BD),yaxis=dict(gridcolor=BD))
        st.plotly_chart(kf, use_container_width=True)

    # ── Multi-Timeframe Analysis ──
    with st.expander(f"🔀 {t} 多週期趨勢分析（日/週/月）", expanded=(idx==0)):
        wk_df = fetch_weekly(t)
        mo_df = fetch_monthly(t)

        daily_sig = calc_tf_signal(df, "日線")
        weekly_sig = calc_tf_signal(wk_df, "週線")
        monthly_sig = calc_tf_signal(mo_df, "月線")
        tf_sigs = [daily_sig, weekly_sig, monthly_sig]

        mtf_html = '<div class="mtf-grid">'
        mtf_html += f'''<div class="mtf-row hdr">
            <div class="tf-hdr" style="text-align:left;">週期</div>
            <div class="tf-hdr">趨勢</div>
            <div class="tf-hdr">RSI</div>
            <div class="tf-hdr">MACD</div>
            <div class="tf-hdr">均線</div>
        </div>'''
        for sig in tf_sigs:
            rsi_s = f'{sig["rsi"]:.0f}' if sig["rsi"] else "—"
            mtf_html += f'''<div class="mtf-row">
                <div class="tf-label">{sig["tf"]}</div>
                <div class="tf-val">{sig["trend"]}</div>
                <div class="tf-val">{rsi_s}</div>
                <div class="tf-val">{sig["macd"]}</div>
                <div class="tf-val">{sig["ma_status"]}</div>
            </div>'''
        mtf_html += '</div>'
        st.markdown(mtf_html, unsafe_allow_html=True)

        bull_count = sum(1 for s in tf_sigs if "🟢" in s["trend"])
        bear_count = sum(1 for s in tf_sigs if "🔴" in s["trend"])
        if bull_count >= 2:
            verdict_cls = "bullish"
            verdict_txt = "多週期偏多 — 日/週/月線趨勢共振向上，回檔可視為布局機會"
        elif bear_count >= 2:
            verdict_cls = "bearish"
            verdict_txt = "多週期偏空 — 多數週期趨勢向下，建議等待更明確的止穩訊號"
        else:
            verdict_cls = "mixed"
            verdict_txt = "多空分歧 — 長短週期趨勢不一致，適合觀望或輕倉試探"
        st.markdown(f'<div class="mtf-verdict {verdict_cls}">{verdict_txt}</div>', unsafe_allow_html=True)

        has_wk = not wk_df.empty
        has_mo = not mo_df.empty
        n_rows = 1 + (1 if has_wk else 0) + (1 if has_mo else 0)
        subtitles = ["日線"]
        if has_wk: subtitles.append("週線")
        if has_mo: subtitles.append("月線")

        mtf_fig = make_subplots(rows=n_rows, cols=1, shared_xaxes=False, vertical_spacing=0.08,
                                subplot_titles=subtitles, row_heights=[1]*n_rows)

        mtf_fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
            increasing_fillcolor=GR, increasing_line_color=GR, decreasing_fillcolor=RD, decreasing_line_color=RD,
            name="日K", showlegend=False), row=1, col=1)
        for mac, mcc in [("MA20",AM),("MA50",BL),("MA200",RD)]:
            if mac in df.columns:
                mtf_fig.add_trace(go.Scatter(x=df.index, y=df[mac], line=dict(color=mcc, width=1), opacity=0.7,
                    name=mac, showlegend=(mac=="MA20")), row=1, col=1)

        r = 2
        if has_wk:
            mtf_fig.add_trace(go.Candlestick(x=wk_df.index, open=wk_df["Open"], high=wk_df["High"], low=wk_df["Low"], close=wk_df["Close"],
                increasing_fillcolor=GR, increasing_line_color=GR, decreasing_fillcolor=RD, decreasing_line_color=RD,
                name="週K", showlegend=False), row=r, col=1)
            for mac, mcc in [("MA10",AM),("MA40",RD)]:
                if mac in wk_df.columns:
                    mtf_fig.add_trace(go.Scatter(x=wk_df.index, y=wk_df[mac], line=dict(color=mcc, width=1), opacity=0.7,
                        showlegend=False), row=r, col=1)
            r += 1

        if has_mo:
            mtf_fig.add_trace(go.Candlestick(x=mo_df.index, open=mo_df["Open"], high=mo_df["High"], low=mo_df["Low"], close=mo_df["Close"],
                increasing_fillcolor=GR, increasing_line_color=GR, decreasing_fillcolor=RD, decreasing_line_color=RD,
                name="月K", showlegend=False), row=r, col=1)
            for mac, mcc in [("MA6",AM),("MA12",RD)]:
                if mac in mo_df.columns:
                    mtf_fig.add_trace(go.Scatter(x=mo_df.index, y=mo_df[mac], line=dict(color=mcc, width=1), opacity=0.7,
                        showlegend=False), row=r, col=1)

        chart_h = 220 * n_rows
        mtf_fig.update_layout(
            height=chart_h, template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="JetBrains Mono", size=9),
            margin=dict(l=40, r=5, t=30, b=15),
            showlegend=False,
        )
        for i in range(1, n_rows+1):
            mtf_fig.update_xaxes(gridcolor=BD, row=i, col=1, rangeslider_visible=False)
            mtf_fig.update_yaxes(gridcolor=BD, row=i, col=1)

        st.plotly_chart(mtf_fig, use_container_width=True)

    d_s = calc_tf_signal(df, "日")
    w_s = calc_tf_signal(fetch_weekly(t), "週")
    m_s = calc_tf_signal(fetch_monthly(t), "月")
    bc2 = sum(1 for s in [d_s, w_s, m_s] if "🟢" in s["trend"])
    brc = sum(1 for s in [d_s, w_s, m_s] if "🔴" in s["trend"])
    tfv = "bullish" if bc2 >= 2 else ("bearish" if brc >= 2 else "mixed")
    plan=gen_plan(m, tb, tf_verdict=tfv)
    
    shtml='<div class="sp">'
    for pi,px in enumerate(plan):
        last=pi==len(plan)-1
        if px["pct"]>0:
            tag=f'<span class="pt buy">{px["pct"]}% · ${px["dollar"]:,.0f} · ~{px["shares"]}股</span>'
            prh=f'<span class="pp" style="color:{GR};">${px["pt"]:.2f}</span>'
        elif px["pct"]==-100:
            tag=f'<span class="pt stop">全部出場</span>'
            prh=f'<span class="pp" style="color:{RD};">${px["pt"]:.2f}</span>'
        else:
            tag=f'<span class="pt wait">等待</span>'; prh=""
        shtml+=f'''<div class="si"><div class="sl"><div class="sd {px["tp"]}"></div>{"" if last else '<div class="sc"></div>'}</div>
        <div class="sx"><div class="hd"><div><span class="pn">{px["ph"]}</span> {tag}</div>{prh}</div>
        <div class="tg">{px["trig"]}</div><div class="wh">📌 {px["why"]}</div></div></div>'''
    shtml+='</div>'
    st.markdown(shtml, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SEC 5: MASTER TABLE
# ─────────────────────────────────────────────

st.markdown(f'<div class="sh"><div class="n" style="background:rgba(245,158,11,0.12);color:{AM};">05</div><div class="t">總覽摘要表</div></div>', unsafe_allow_html=True)

mt=[]
for t in st_t:
    m=all_m[t]; inf=all_i.get(t,{}); w=wts[t]
    stx2,_=get_sig(m["pb"],m["rsi"])
    plan=gen_plan(m,bg*w); ent=[p for p in plan if p["pct"]>0]; stp=[p for p in plan if p["pct"]==-100]
    fe=ent[0]["pt"] if ent else m["cur"]; spp=stp[0]["pt"] if stp else m["cur"]*0.9
    
    d_sig=calc_tf_signal(all_d[t],"日")
    w_sig=calc_tf_signal(fetch_weekly(t),"週")
    m_sig=calc_tf_signal(fetch_monthly(t),"月")
    bc=sum(1 for s in [d_sig,w_sig,m_sig] if "🟢" in s["trend"])
    brc3=sum(1 for s in [d_sig,w_sig,m_sig] if "🔴" in s["trend"])
    mtf_v="🟢 多" if bc>=2 else ("🔴 空" if brc3>=2 else "🟡 分歧")
    
    mt.append({"標的":t,"公司":inf.get("shortName",t)[:15],"現價":f'${m["cur"]:.2f}',"回檔":f'{m["pb"]:.1f}%',
    "RSI":fmt(m["rsi"]),"MACD":"🟢" if m["macd"] and m["macd_sig"] and m["macd"]>m["macd_sig"] else "🔴",
    "多週期":mtf_v,"訊號":stx2,"分配":f'${bg*w:,.0f}',"首批進場":f'${fe:.2f}',"停損":f'${spp:.2f}'})
st.dataframe(pd.DataFrame(mt),use_container_width=True,hide_index=True)

# ─────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────

with st.expander("⚠️ 風險提示"):
    st.markdown("""
    1. **僅供研究參考，不構成投資建議。**
    2. 技術分析無法預測突發事件。
    3. 停損紀律至關重要。
    4. 建議搭配基本面分析。
    5. 過去表現不代表未來結果。
    """)
st.caption(f"📊 Yahoo Finance · {', '.join(vt)} · {datetime.now().strftime('%Y-%m-%d %H:%M')} · 不構成投資建議")
