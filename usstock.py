"""
📉 美股回檔分析 & 分段買進建議器 v4.0
==========================================
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
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Core Functions
# ─────────────────────────────────────────────

@st.cache_data(ttl=300)
def fetch_data(ticker, period="1y"):
    try: df = yf.Ticker(ticker).history(period=period)
    except: return pd.DataFrame()
    if df.empty or len(df) < 20: return pd.DataFrame()
    df["MA20"]=df["Close"].rolling(20).mean(); df["MA50"]=df["Close"].rolling(50).mean(); df["MA200"]=df["Close"].rolling(200).mean()
    d=df["Close"].diff(); g=d.where(d>0,0).rolling(14).mean(); l=(-d.where(d<0,0)).rolling(14).mean(); rs=g/l; df["RSI"]=100-(100/(1+rs))
    e12=df["Close"].ewm(span=12).mean(); e26=df["Close"].ewm(span=26).mean(); df["MACD"]=e12-e26; df["MACD_Signal"]=df["MACD"].ewm(span=9).mean()
    df["Vol_MA20"]=df["Volume"].rolling(20).mean()
    return df

@st.cache_data(ttl=600)
def fetch_info(ticker):
    try: return yf.Ticker(ticker).info
    except: return {}

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

def calc_pb(df):
    if df.empty or len(df)<20: return {}
    hi=df["High"].max(); hd=df["High"].idxmax(); cur=df["Close"].iloc[-1]; lo=df["Low"].min()
    def s(c):
        v=df[c].iloc[-1] if c in df.columns else None
        return v if v is not None and not pd.isna(v) else None
    vol=df["Volume"].iloc[-1]; av=s("Vol_MA20") or vol
    return {"cur":cur,"high":hi,"high_date":hd,"low":lo,"pb":(cur-hi)/hi*100,"ma20":s("MA20"),"ma50":s("MA50"),"ma200":s("MA200"),"rsi":s("RSI"),"macd":s("MACD"),"macd_sig":s("MACD_Signal"),"vol_ratio":vol/av if av>0 else 1.0}

def mad(p,ma): return (p-ma)/ma*100 if ma and ma>0 else None
def fmt(v,sp=".1f",fb="—"): return f"{v:{sp}}" if v is not None else fb

def get_sig(pb,rsi):
    p=abs(pb)
    if p>=20 and rsi and rsi<35: return "超賣 — 強烈關注","sig-buy"
    elif p>=10 and rsi and rsi<45: return "分批布局","sig-buy"
    elif p>=10: return "觀察中","sig-watch"
    elif p>=5: return "初步回檔","sig-watch"
    else: return "未明顯回檔","sig-caution"

def gen_plan(m, budget):
    p,hi,pb,ma200=m["cur"],m["high"],abs(m["pb"]),m.get("ma200")
    phases=[]
    if pb<5:
        phases+=[{"ph":"觀望","trig":f"僅回檔 {pb:.1f}%，等 ≥10%","pt":p*0.90,"pct":0,"why":"回檔不足","tp":"wait"},
                 {"ph":"第一批","trig":f"跌至 ${p*0.90:.2f}","pt":p*0.90,"pct":30,"why":"回檔達有意義幅度","tp":"buy"},
                 {"ph":"第二批","trig":f"跌至 ${p*0.85:.2f}","pt":p*0.85,"pct":30,"why":"更深修正","tp":"buy"},
                 {"ph":"第三批","trig":"確認反彈 + 站上 20MA","pt":p*0.88,"pct":40,"why":"趨勢反轉確認","tp":"buy"}]
    elif pb<15:
        phases+=[{"ph":"第一批","trig":f"現價 ${p:.2f} 企穩","pt":p,"pct":30,"why":f"已修正 {pb:.1f}%","tp":"buy"},
                 {"ph":"第二批","trig":f"再跌至 ${p*0.95:.2f}","pt":p*0.95,"pct":30,"why":"攤低成本","tp":"buy"},
                 {"ph":"第三批","trig":f"反彈站穩 ${p*1.05:.2f}","pt":p*1.05,"pct":40,"why":"趨勢反轉確認","tp":"buy"}]
    elif pb<30:
        phases+=[{"ph":"第一批","trig":f"現價 ${p:.2f}（回檔 {pb:.1f}%）","pt":p,"pct":35,"why":"估值壓縮明顯","tp":"buy"},
                 {"ph":"第二批","trig":f"下探 ${p*0.93:.2f}","pt":p*0.93,"pct":35,"why":"恐慌賣盤買點","tp":"buy"},
                 {"ph":"第三批","trig":f"突破 ${p*1.08:.2f}","pt":p*1.08,"pct":30,"why":"底部確認","tp":"buy"}]
    else:
        phases+=[{"ph":"⚠️ 深度修正","trig":f"下跌 {pb:.1f}%，先確認基本面","pt":p,"pct":0,"why":"須排除 value trap","tp":"wait"},
                 {"ph":"第一批","trig":f"確認非基本面問題，${p:.2f} 試探","pt":p,"pct":20,"why":"輕倉試探","tp":"buy"},
                 {"ph":"第二批","trig":"止穩訊號（量縮/RSI背離）","pt":p*0.95,"pct":30,"why":"底部訊號","tp":"buy"},
                 {"ph":"第三批","trig":"站回 50MA 上方","pt":m["ma50"] if m["ma50"] else p*1.1,"pct":50,"why":"趨勢修復","tp":"buy"}]
    sp=min(p*0.92,ma200*0.97) if ma200 and ma200>0 else p*0.90
    phases.append({"ph":"停損","trig":f"跌破 ${sp:.2f}（{((sp/p-1)*100):.1f}%）","pt":sp,"pct":-100,"why":"紀律停損，保護本金","tp":"stop"})
    for x in phases:
        if x["pct"]>0: x["dollar"]=budget*x["pct"]/100; x["shares"]=int(x["dollar"]/x["pt"]) if x["pt"]>0 else 0
        else: x["dollar"]=0; x["shares"]=0
    return phases

def calc_w(metrics):
    sc={}
    for t,m in metrics.items():
        sc[t]=max(abs(m["pb"])*0.6+max(0,50-(m["rsi"] or 50))*0.4,1)
    tot=sum(sc.values())
    return {t:s/tot for t,s in sc.items()}


# ─────────────────────────────────────────────
# Controls (主頁面頂部，手機友善)
# ─────────────────────────────────────────────

# 快速組合按鈕
qc = st.columns(4)
with qc[0]:
    if st.button("Mag 7", use_container_width=True): st.session_state["ti"]="AAPL,MSFT,GOOG,AMZN,NVDA,META,TSLA"
with qc[1]:
    if st.button("半導體", use_container_width=True): st.session_state["ti"]="NVDA,AMD,AVGO,TSM,QCOM,INTC"
with qc[2]:
    if st.button("AI 概念", use_container_width=True): st.session_state["ti"]="NVDA,PLTR,MSFT,GOOG,META,CRM"
with qc[3]:
    if st.button("電動車", use_container_width=True): st.session_state["ti"]="TSLA,RIVN,NIO,LI,XPEV,LCID"

# 輸入列
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
    if t and t not in seen: seen.add(t); tickers.append(t)
tickers=tickers[:10]

if not tickers: st.warning("請輸入至少一個股票代號。"); st.stop()

with st.spinner(f"載入 {len(tickers)} 檔..."):
    rd=fetch_all(tickers,lk)

all_d,all_m,all_i,fail={},{},{},[]
for t in tickers:
    r=rd.get(t,{}); df=r.get("data",pd.DataFrame()); inf=r.get("info",{})
    if df.empty: fail.append(t); continue
    m=calc_pb(df)
    if not m: fail.append(t); continue
    all_d[t]=df; all_m[t]=m; all_i[t]=inf

if fail: st.warning(f"無法取得：{', '.join(fail)}")
vt=[t for t in tickers if t in all_m]
if not vt: st.error("所有標的無法取得數據。"); st.stop()

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

    # Step plan
    plan=gen_plan(m,tb)
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
    mt.append({"標的":t,"公司":inf.get("shortName",t)[:15],"現價":f'${m["cur"]:.2f}',"回檔":f'{m["pb"]:.1f}%',
        "RSI":fmt(m["rsi"]),"MACD":"🟢" if m["macd"] and m["macd_sig"] and m["macd"]>m["macd_sig"] else "🔴",
        "訊號":stx2,"分配":f'${bg*w:,.0f}',"首批進場":f'${fe:.2f}',"停損":f'${spp:.2f}'})
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
