import streamlit as st
import yfinance as yf
import pandas as pd

# Sayfa yapılandırması - Geniş mod ve temiz görünüm
st.set_page_config(page_title="Kripto Scalping Asistanı", layout="wide")

# Başlık
st.title("⚡ Kripto Vur-Kaç (Scalping) Asistanı")
st.write("Bu panel, 15 dakikalık anlık verilere göre agresif işlem seviyelerini doğrudan hesaplar.")

# Taranacak 10 majör parite
tickers = [
    "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD",
    "DOGE-USD", "ADA-USD", "AVAX-USD", "LINK-USD", "DOT-USD"
]

# Verileri çekme ve hesaplama fonksiyonu (1 dakikalık cache ile API'yi boğmamak için)
@st.cache_data(ttl=60)
def get_scalping_signals():
    data = []
    for ticker in tickers:
        try:
            # yfinance üzerinden son 1 günlük veriyi 15 dakikalık aralıklarla çek
            ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(period="1d", interval="15m")

            if df.empty:
                continue

            # En güncel mumun kapanış fiyatını al
            current_price = float(df['Close'].iloc[-1])

            # Matematiksel Strateji:
            # AL: Anlık fiyattan %0.2 aşağısı
            # TP: Giriş seviyesinden %0.6 yukarısı
            # SL: Giriş seviyesinden %0.3 aşağısı
            entry_price = current_price * 0.998
            take_profit = entry_price * 1.006
            stop_loss = entry_price * 0.997

            # Tabloya eklenecek satır
            data.append({
                "Sembol": ticker,
                "Güncel Fiyat": current_price,
                "🟢 Giriş Seviyesi (AL)": entry_price,
                "🎯 Kar Al (TP)": take_profit,
                "🔴 Zarar Kes (SL)": stop_loss
            })
        except Exception:
            # Olası bağlantı veya veri çekme hatalarını yoksay ve diğer coine geç
            continue
            
    return pd.DataFrame(data)

# Yükleniyor animasyonu ile fonksiyonu çalıştır
with st.spinner("Piyasalar taranıyor ve hedefler hesaplanıyor..."):
    df_signals = get_scalping_signals()

# Veri başarılı çekildiyse tabloyu formatla ve ekrana bas
if not df_signals.empty:
    formatted_df = df_signals.copy()
    
    # Formatlanacak sayısal sütunlar
    cols_to_format = ["Güncel Fiyat", "🟢 Giriş Seviyesi (AL)", "🎯 Kar Al (TP)", "🔴 Zarar Kes (SL)"]
    
    # Sütunları dolar işaretli ve 4 ondalıklı string'e çevir
    for col in cols_to_format:
        formatted_df[col] = formatted_df[col].apply(lambda x: f"${x:,.4f}")

    # Index (satır numaraları) kapalı şekilde, tam genişlikte tabloyu yansıt
    st.dataframe(formatted_df, use_container_width=True, hide_index=True)
else:
    st.error("Veri çekilemedi. Lütfen Yahoo Finance servisinin durumunu kontrol edin.")