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

# ==========================================
# 2. ASSET UNIVERSE & DATA FEEDS
# ==========================================
ASSET_UNIVERSE = {
    'Crypto (Binance)': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'LINK/USDT', 'DOGE/USDT', 'AVAX/USDT', 'MATIC/USDT'],
    'US Stocks (Yahoo)': ['AAPL', 'TSLA', 'NVDA', 'AMZN', 'META', 'MSFT', 'AMD'],
    'Forex (Yahoo)': ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X'],
    'Commodities (Yahoo)': ['GC=F', 'CL=F', 'SI=F'] 
}

# Inisialisasi Binance via CCXT
binance = ccxt.binance()

# ==========================================
# 3. DATA FETCHING ENGINES
# ==========================================
def fetch_binance_data(symbol, days=90):
    """Fetch real-time OHLCV from Binance"""
    try:
        since = binance.milliseconds() - (days * 24 * 60 * 60 * 1000)
        ohlcv = binance.fetch_ohlcv(symbol, '1d', since)
        
        df = pd.DataFrame(ohlcv, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
        df.set_index('Timestamp', inplace=True)
        return df
    except Exception as e:
        return None

def fetch_yahoo_data(symbol, days=90):
    """Fetch OHLCV from Yahoo Finance"""
    try:
        df = yf.download(symbol, period=f"{days}d", interval='1d', progress=False)
        return df
    except Exception as e:
        return None

# ==========================================
# 4. MACRO LOGIC GATE (MODUL C SIMULASI)
# ==========================================
def check_macro_gate(symbol, current_price, df):
    """
    Simulasi Modul C: On-Chain Macro Validation.
    Di live trading, fungsi ini nge-fetch API CryptoQuant (NUPL, SOPR, dll).
    Untuk prototype ini, kita pakai proxy: Harga turun > 40% dari ATH 1 tahun = Bear Market.
    """
    # Jika bukan crypto, macro gate dinonaktifkan (Return True)
    if '/USDT' not in symbol and '-' not in symbol and '=' not in symbol:
        # Untuk saham, kita cek apakah sedang koreksi > 20% dari high 1 tahun
        high_1y = df['High'].rolling(252).max().iloc[-1] if len(df) > 252 else df['High'].max()
        if current_price < (high_1y * 0.80):
            return True # Bear market saam
        return False
    
    # Proxy Crypto: Koreksi > 40% dari High 90 hari (Simulasi Bear/Capitulation)
    high_90d = df['High'].rolling(90).max().iloc[-1] if len(df) > 90 else df['High'].max()
    if current_price < (high_90d * 0.60):
        return True # Simulasi NUPL Extreme Fear / SOPR < 1
    return False

# ==========================================
# 5. SCANNER LOGIC (VECTORIZED)
# ==========================================
def scan_asset(ticker, market_type, anchor_window, front_run_pct, min_front_runs, lookback_days):
    
    days_to_fetch = anchor_window + lookback_days + 20
    
    # 1. Fetch Data
    if 'Binance' in market_type:
        df = fetch_binance_data(ticker, days_to_fetch)
    else:
        df = fetch_yahoo_data(ticker, days_to_fetch)
        
    if df is None or len(df) < anchor_window + 10:
        return None
        
    df.dropna(inplace=True)
    
    # 2. Cari Anchor (Swing Low absolut dari window tertentu, skip hari ini)
    anchor_low = df['Low'].iloc[-(anchor_window+1):-1].min()
    if pd.isna(anchor_low) or anchor_low == 0:
        return None
        
    # 3. Hitung Front-Run
    lower_bound = anchor_low * 0.995
    upper_bound = anchor_low * (1 + (front_run_pct / 100))
    
    df['Is_Front_Run'] = ((df['Low'] <= upper_bound) & 
                          (df['Low'] >= lower_bound) & 
                          (df['Close'] > anchor_low))
    
    front_run_count = df['Is_Front_Run'].iloc[-lookback_days:].sum()
    
    # 4. Deteksi Scam Wick & Incubation
    last_row = df.iloc[-1]
    scam_wick_reclaim = (last_row['Low'] < anchor_low) and (last_row['Close'] > anchor_low)
    incubation = (last_row['Low'] <= upper_bound) and (last_row['Close'] > anchor_low) and not scam_wick_reclaim
    
    # 5. Cek Macro Gate (Hanya aktif jika dicentang di UI)
    macro_valid = True
    if use_macro_gate:
        macro_valid = check_macro_gate(ticker, last_row['Close'], df)
        
    # 6. Status Determination
    status = 'NEUTRAL'
    if scam_wick_reclaim and front_run_count >= min_front_runs:
        status = '🚀 TRIGGERED' if macro_valid else '🚀 TRIGGERED (Macro Gate OFF)'
    elif incubation and front_run_count >= (min_front_runs - 1):
        status = '⏳ INCUBATION' if macro_valid else '⏳ INCUBATION (Macro Gate OFF)'
    elif front_run_count >= (min_front_runs - 2):
        status = '👀 WATCHING'
        
    if status != 'NEUTRAL':
        return {
            'Ticker': ticker,
            'Market': market_type.split(' ')[0],
            'Status': status,
            'Anchor Price': round(anchor_low, 4),
            'Front-Runs': int(front_run_count),
            'Last Close': round(last_row['Close'], 4),
            'Distance to Anchor (%)': round(((last_row['Close'] - anchor_low) / anchor_low) * 100, 2),
            'Macro Valid': '✅' if macro_valid else '❌'
        }

# ==========================================
# 6. STREAMLIT UI LAYOUT
# ==========================================
st.title("🚀 KillaXBT Institutional Scanner")
st.markdown("Mencari pola **Liquidity Sweep & Front-Running** (Binance Real-time & Yahoo Finance).")

# Sidebar
st.sidebar.header("⚙️ Scanner Configuration")

selected_markets = st.sidebar.multiselect(
    "Pilih Market:",
    options=list(ASSET_UNIVERSE.keys()),
    default=['Crypto (Binance)']
)

use_macro_gate = st.sidebar.checkbox("Aktifkan Macro Gate (On-Chain Simulation)", value=True)
st.sidebar.caption("Jika aktif, sistem hanya akan menampilkan setup TRIGGERED/INCUBATION jika aset sedang dalam fase Bear/Capitulation (Koreksi > 40% dari ATH).")

st.sidebar.subheader("Parameter Setup")
anchor_window = st.sidebar.slider("Anchor Window (Hari)", min_value=20, max_value=100, value=50, step=5)
min_front_runs = st.sidebar.slider("Minimal Front-Run Count", min_value=3, max_value=8, value=5, step=1)
front_run_pct = st.sidebar.slider("Jarak Front-Run dari Anchor (%)", min_value=0.5, max_value=5.0, value=1.5, step=0.1)
lookback_days = st.sidebar.slider("Lookback Window (Hari)", min_value=10, max_value=60, value=30, step=5)

custom_tickers = st.sidebar.text_input("Tambah ticker manual (Pisahkan dengan koma)", "")
st.sidebar.caption("Crypto: pakai format BTC/USDT. Saham: AAPL. Forex: EURUSD=X")

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
            # Asumsi custom ticker adalah crypto jika ada /USDT, selain itu Yahoo
            if '/USDT' in t or '-USD' in t:
                market_map[t] = 'Crypto (Binance)' if '/USDT' in t else 'Crypto (Yahoo)'
            else:
                market_map[t] = 'US Stocks (Yahoo)'
                
    tickers_to_scan = list(set(tickers_to_scan))
    
    if not tickers_to_scan:
        st.warning("Silakan pilih minimal 1 market atau input ticker manual.")
    else:
        st.write(f"### Memindai {len(tickers_to_scan)} aset...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        
        for i, ticker in enumerate(tickers_to_scan):
            market_type = market_map.get(ticker, "Unknown")
            status_text.text(f"Scanning {ticker} via {market_type}... ({i+1}/{len(tickers_to_scan)})")
            
            res = scan_asset(ticker, market_type, anchor_window, front_run_pct, min_front_runs, lookback_days)
            if res:
                results.append(res)
                
            progress_bar.progress((i + 1) / len(tickers_to_scan))
            time.sleep(0.05) # Hindari rate limit
            
        progress_bar.empty()
        status_text.empty()
        
        # ==========================================
        # 8. DISPLAY RESULTS
        # ==========================================
        if not results:
            st.info("Tidak ada setup yang terbentuk saat ini. Coba ubah parameter atau market.")
        else:
            df_results = pd.DataFrame(results)
            
            # Urutkan
            status_order = {'🚀 TRIGGERED': 1, '🚀 TRIGGERED (Macro Gate OFF)': 1, '⏳ INCUBATION': 2, '⏳ INCUBATION (Macro Gate OFF)': 2, '👀 WATCHING': 3}
            df_results['Sort_Order'] = df_results['Status'].map(status_order)
            df_results = df_results.sort_values(['Sort_Order', 'Macro Valid'], ascending=[True, False]).drop('Sort_Order', axis=1).reset_index(drop=True)
            
            st.success(f"Ditemukan {len(df_results)} potensi setup!")
            
            # Styling
            def highlight_status(val):
                if 'TRIGGERED' in val:
                    return 'background-color: #ff4b4b; color: white; font-weight: bold'
                elif 'INCUBATION' in val:
                    return 'background-color: #ffa621; color: black'
                elif 'WATCHING' in val:
                    return 'background-color: #21b353; color: white'
                return ''
                
            st.dataframe(
                df_results.style.map(highlight_status, subset=['Status']),
                use_container_width=True,
                hide_index=True
            )
            
            # Execution Insights
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
    
    with st.expander("ℹ️ Tentang Sistem"):
        st.markdown("""
        **KillaXBT Scanner V2** menggabungkan 3 modul utama:
        1. **Data Feed:** Crypto diambil real-time dari Binance API. Saham/Forex dari Yahoo Finance.
        2. **Price Action:** Mendeteksi akumulasi likuiditas (5-6 Front-Run) dan Scam Wick Reclaim.
        3. **Macro Gate:** Memvalidasi apakah aset sedang berada di fase kapitulasi (Bear Market) sebelum mengizinkan eksekusi grid.
        """)