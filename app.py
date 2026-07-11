import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import ccxt
import time
from datetime import datetime, timedelta

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="KillaXBT Institutional Scanner",
    page_icon="🚀",
    layout="wide"
)

# Inisialisasi Binance via CCXT
binance = ccxt.binance()

# ==========================================
# 2. DYNAMIC ASSET UNIVERSE (TOP 100 CRYPTO)
# ==========================================
@st.cache_data(ttl=3600) # Cache 1 jam biar gak spam API Binance
def get_top_crypto(limit=100):
    try:
        tickers = binance.fetch_tickers()
        usdt_pairs = {
            symbol: data.get('quoteVolume', 0) 
            for symbol, data in tickers.items() 
            if symbol.endswith('/USDT') and 'UP/USDT' not in symbol and 'DOWN/USDT' not in symbol 
            and 'BULL/USDT' not in symbol and 'BEAR/USDT' not in symbol
        }
        top_symbols = sorted(usdt_pairs, key=usdt_pairs.get, reverse=True)[:limit]
        return top_symbols
    except:
        return ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT']

# Daftar Forex & Commodities yang udah di-filter
FOREX_COMMODITIES = [
    'GC=F',   # XAUUSD (Gold)
    'SI=F',   # XAGUSD (Silver)
    'CL=F',   # USOIL (Crude Oil WTI)
    'USDJPY=X', # USDJPY
    'EURUSD=X', # EURUSD
    'GBPUSD=X', # GBPUSD
    'GBPJPY=X'  # GBPJPY
]

ASSET_UNIVERSE = {
    'Crypto Top 100 (Binance)': get_top_crypto(100),
    'Forex & Commodities (Yahoo)': FOREX_COMMODITIES
}

# ==========================================
# 3. DATA FETCHING ENGINES (FORCE LATEST)
# ==========================================
def fetch_binance_data(symbol, days=120):
    try:
        since = binance.milliseconds() - (days * 24 * 60 * 60 * 1000)
        ohlcv = binance.fetch_ohlcv(symbol, '1d', since)
        if not ohlcv: return None
        df = pd.DataFrame(ohlcv, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
        df.set_index('Timestamp', inplace=True)
        return df
    except:
        return None

def fetch_yahoo_data(symbol, days=120):
    try:
        # FORCE LATEST DATA: Pakai start dan end eksplisit sampai hari ini
        end_date = datetime.today() + timedelta(days=1)
        start_date = end_date - timedelta(days=days)
        
        df = yf.download(symbol, start=start_date, end=end_date, interval='1d', progress=False, auto_adjust=True)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return None

# ==========================================
# 4. MACRO LOGIC GATE (MODUL C SIMULASI)
# ==========================================
def check_macro_gate(symbol, current_price, df):
    if df.empty: return False
        
    if '/USDT' in symbol:
        if len(df) > 90:
            high_90d = df['High'].rolling(90).max().iloc[-1]
        else:
            high_90d = df['High'].max()
            
        if pd.isna(high_90d) or high_90d == 0: return False
        return current_price < (high_90d * 0.60)
    else:
        if len(df) > 90:
            high_90d = df['High'].rolling(90).max().iloc[-1]
        else:
            high_90d = df['High'].max()
            
        if pd.isna(high_90d) or high_90d == 0: return False
        return current_price < (high_90d * 0.85)

# ==========================================
# 5. SCANNER LOGIC (SAFE WRAPPER)
# ==========================================
def scan_asset(ticker, market_type, anchor_window, front_run_pct, min_front_runs, lookback_days):
    days_to_fetch = anchor_window + lookback_days + 20
    
    if 'Binance' in market_type:
        df = fetch_binance_data(ticker, days_to_fetch)
    else:
        df = fetch_yahoo_data(ticker, days_to_fetch)
        
    if df is None or len(df) < anchor_window + 10: return None
        
    df.dropna(inplace=True)
    if df.empty: return None
    
    if 'Low' not in df.columns or 'Close' not in df.columns: return None
        
    anchor_low = df['Low'].iloc[-(anchor_window+1):-1].min()
    if pd.isna(anchor_low) or anchor_low == 0: return None
        
    lower_bound = anchor_low * 0.995
    upper_bound = anchor_low * (1 + (front_run_pct / 100))
    
    df['Is_Front_Run'] = ((df['Low'] <= upper_bound) & 
                          (df['Low'] >= lower_bound) & 
                          (df['Close'] > anchor_low))
    
    front_run_count = df['Is_Front_Run'].iloc[-lookback_days:].sum()
    
    last_row = df.iloc[-1]
    last_low = last_row['Low']
    last_close = last_row['Close']
    
    if pd.isna(last_low) or pd.isna(last_close): return None
    
    scam_wick_reclaim = (last_low < anchor_low) and (last_close > anchor_low)
    incubation = (last_low <= upper_bound) and (last_close > anchor_low) and not scam_wick_reclaim
    
    macro_valid = True
    if use_macro_gate:
        macro_valid = check_macro_gate(ticker, last_close, df)
        
    status = 'NEUTRAL'
    if scam_wick_reclaim and front_run_count >= min_front_runs:
        status = '🚀 TRIGGERED' if macro_valid else '🚀 TRIGGERED (Macro OFF)'
    elif incubation and front_run_count >= (min_front_runs - 1):
        status = '⏳ INCUBATION' if macro_valid else '⏳ INCUBATION (Macro OFF)'
    elif front_run_count >= (min_front_runs - 2):
        status = '👀 WATCHING'
        
    if status != 'NEUTRAL':
        return {
            'Ticker': ticker,
            'Market': market_type.split(' ')[0],
            'Status': status,
            'Anchor Price': round(float(anchor_low), 6),
            'Front-Runs': int(front_run_count),
            'Last Close': round(float(last_close), 6),
            'Distance (%)': round(float(((last_close - anchor_low) / anchor_low) * 100), 2),
            'Macro Valid': '✅' if macro_valid else '❌'
        }
    return None

# ==========================================
# 6. STREAMLIT UI LAYOUT
# ==========================================
st.title("🚀 KillaXBT Institutional Scanner")
st.markdown("Mencari pola **Liquidity Sweep & Front-Running** (Top 100 Crypto Dynamic + Forex/Commodities).")

st.sidebar.header("⚙️ Scanner Configuration")

selected_markets = st.sidebar.multiselect(
    "Pilih Market:",
    options=list(ASSET_UNIVERSE.keys()),
    default=['Crypto Top 100 (Binance)']
)

use_macro_gate = st.sidebar.checkbox("Aktifkan Macro Gate (Bear Market Filter)", value=True)
st.sidebar.caption("Crypto: Koreksi > 40% dari ATH 90 hari. Forex/Comm: Koreksi > 15%.")

st.sidebar.subheader("Parameter Setup")
anchor_window = st.sidebar.slider("Anchor Window (Hari)", 20, 100, 50, step=5)
min_front_runs = st.sidebar.slider("Minimal Front-Run Count", 3, 8, 5, step=1)
front_run_pct = st.sidebar.slider("Jarak Front-Run dari Anchor (%)", 0.5, 5.0, 1.5, step=0.1)
lookback_days = st.sidebar.slider("Lookback Window (Hari)", 10, 60, 30, step=5)

custom_tickers = st.sidebar.text_input("Tambah ticker manual (Pisahkan dengan koma)", "")
st.sidebar.caption("Crypto: pakai format SOL/USDT. Forex: GBPUSD=X")

# ==========================================
# 7. EXECUTION & DATA PROCESSING
# ==========================================
if st.sidebar.button("Start Scanning", type="primary", use_container_width=True):
    
    tickers_to_scan = []
    market_map = {}
    
    for market in selected_markets:
        for ticker in ASSET_UNIVERSE[market]:
            tickers_to_scan.append(ticker)
            market_map[ticker] = market
            
    if custom_tickers:
        custom_list = [t.strip() for t in custom_tickers.split(',')]
        for t in custom_list:
            tickers_to_scan.append(t)
            if '/USDT' in t or '-USD' in t:
                market_map[t] = 'Crypto (Binance)' if '/USDT' in t else 'Crypto (Yahoo)'
            else:
                market_map[t] = 'Forex & Commodities (Yahoo)'
                
    tickers_to_scan = list(set(tickers_to_scan))
    
    if not tickers_to_scan:
        st.warning("Silakan pilih minimal 1 market atau input ticker manual.")
    else:
        # TANGGAL & JAM REAL-TIME SAAT SCAN DIJALANKAN
        scan_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        st.write(f"### Memindai {len(tickers_to_scan)} aset...")
        st.caption(f"⏱️ Scan executed at: {scan_time} | Data diambil real-time dari API Binance & Yahoo Finance.")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        error_count = 0
        
        for i, ticker in enumerate(tickers_to_scan):
            market_type = market_map.get(ticker, "Unknown")
            status_text.text(f"Scanning {ticker} via {market_type}... ({i+1}/{len(tickers_to_scan)})")
            
            try:
                res = scan_asset(ticker, market_type, anchor_window, front_run_pct, min_front_runs, lookback_days)
                if res:
                    results.append(res)
            except Exception:
                error_count += 1
                
            progress_bar.progress((i + 1) / len(tickers_to_scan))
            time.sleep(0.02) # Rate limit handler
            
        progress_bar.empty()
        status_text.empty()
        
        # ==========================================
        # 8. DISPLAY RESULTS
        # ==========================================
        if not results:
            st.info("Tidak ada setup yang terbentuk saat ini. Coba ubah parameter atau market.")
            if error_count > 0:
                st.warning(f"Catatan: {error_count} ticker dilewati karena error koneksi data.")
        else:
            df_results = pd.DataFrame(results)
            
            status_order = {'🚀 TRIGGERED': 1, '🚀 TRIGGERED (Macro OFF)': 1, '⏳ INCUBATION': 2, '⏳ INCUBATION (Macro OFF)': 2, '👀 WATCHING': 3}
            df_results['Sort_Order'] = df_results['Status'].map(status_order)
            df_results = df_results.sort_values(['Sort_Order', 'Macro Valid'], ascending=[True, False]).drop('Sort_Order', axis=1).reset_index(drop=True)
            
            st.success(f"Ditemukan {len(df_results)} potensi setup dari {len(tickers_to_scan)} aset!")
            if error_count > 0:
                st.caption(f"⚠️ {error_count} ticker dilewati karena error data API.")
            
            def highlight_status(val):
                if 'TRIGGERED' in val: return 'background-color: #ff4b4b; color: white; font-weight: bold'
                elif 'INCUBATION' in val: return 'background-color: #ffa621; color: black'
                elif 'WATCHING' in val: return 'background-color: #21b353; color: white'
                return ''
                
            st.dataframe(
                df_results.style.map(highlight_status, subset=['Status']),
                use_container_width=True,
                hide_index=True
            )
            
            st.divider()
            st.subheader("📖 Execution Insights")
            
            triggered = df_results[df_results['Status'].str.contains('TRIGGERED') & df_results['Macro Valid'].str.contains('✅')]
            
            if not triggered.empty:
                st.error(f"🚨 {len(triggered)} SETUP TERVERIFIKASI PENUH (Macro & Price Action Konfirmasi)")
                for idx, row in triggered.iterrows():
                    st.write(f"**{row['Ticker']}**: Siap eksekusi grid asimetris! Anchor: {row['Anchor Price']}")
            else:
                st.info("Tidak ada setup yang memenuhi syarat Macro Gate & Price Action secara bersamaan.")
                
else:
    st.info("👈 Atur parameter di sidebar dan klik **Start Scanning** untuk memulai.")