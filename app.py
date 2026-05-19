import streamlit as st
import yfinance as yf
import vectorbt as vbt
import pandas as pd

# Sayfa Ayarları
st.set_page_config(page_title="Finansal Asistan", layout="wide")

# Sol Menü (Sidebar)
st.sidebar.header("Ayarlar")
symbol = st.sidebar.text_input("Sembol (Örn: BTC-USD, AAPL)", "BTC-USD")
start_date = st.sidebar.date_input("Başlangıç Tarihi", pd.to_datetime("2020-01-01"))
end_date = st.sidebar.date_input("Bitiş Tarihi", pd.to_datetime("today"))
fast_window = st.sidebar.slider("Kısa SMA", 1, 50, 20)
slow_window = st.sidebar.slider("Uzun SMA", 20, 200, 50)

st.title(f"{symbol} - Algoritmik Backtest Asistanı")
st.warning("⚠️ YASAL UYARI: Bu platformdaki sonuçlar sadece geçmiş veri testidir. Kesinlikle yatırım tavsiyesi değildir.")

try:
    # 1. Piyasadan Veriyi Çek
    data = yf.Ticker(symbol).history(start=start_date, end=end_date)

    if data.empty:
        st.error("Veri çekilemedi. Sembolü veya tarihleri kontrol et.")
    else:
        price = data['Close']

        # 2. Hareketli Ortalamaları Hesapla
        fast_ma = vbt.MA.run(price, window=fast_window)
        slow_ma = vbt.MA.run(price, window=slow_window)

        # 3. Kesişimlere Göre Al-Sat Sinyallerini Üret
        entries = fast_ma.ma_crossed_above(slow_ma)
        exits = fast_ma.ma_crossed_below(slow_ma)

        # 4. Portföyü Simüle Et
        portfolio = vbt.Portfolio.from_signals(price, entries, exits, init_cash=10000)

        # --- Asistanın Durum Özeti ---
        st.markdown("---")
        st.subheader("🤖 Asistanın Durum Özeti")

        last_entry_date = entries[entries == True].index[-1] if not entries[entries == True].empty else None
        last_exit_date = exits[exits == True].index[-1] if not exits[exits == True].empty else None

        if last_entry_date and last_exit_date:
            if last_entry_date > last_exit_date:
                st.success(f"🟢 **GÜNCEL DURUM: İÇERİDEYİZ!** \n\nAlgoritma en son **{last_entry_date.strftime('%d-%m-%Y')}** tarihinde fiyat ortalamayı kırınca **GİRİŞ (AL)** emri vermiş. Yükseliş trendi devam ediyor, şu an varlığı elimizde tutuyoruz.")
            else:
                st.error(f"🔴 **GÜNCEL DURUM: NAKİTTEYİZ (DIŞARIDAYIZ)!** \n\nAlgoritma en son **{last_exit_date.strftime('%d-%m-%Y')}** tarihinde fiyat ortalamanın altına düşünce **ÇIKIŞ (SAT)** emri vermiş. Şu an tehlike var, paranı nakitte koruyorsun.")
        else:
            st.info("🟡 Yeterli veri yok veya henüz net bir kesişim sinyali oluşmamış.")

        st.markdown("---")

        # --- Gündelik Vur-Kaç (Scalping) Asistanı ---
        st.subheader("📊 Gündelik Vur-Kaç (Scalping) Asistanı")

        now = pd.Timestamp.now()
        if now.hour < 9 or now.hour >= 24:
            st.info("😴 Gündelik asistan mesai saatleri (09:00 - 00:00) dışında dinleniyor.")
        else:
            latest_price = price.iloc[-1]
            entry_level = latest_price * 0.99  # 1% below current price
            take_profit = entry_level * 1.015  # 1.5% above entry
            stop_loss = entry_level * 0.995  # 0.5% below entry

            # Display levels side‑by‑side using metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Giriş Seviyesi", f"${entry_level:.2f}")
            col2.metric("Kar Al (TP)", f"${take_profit:.2f}")
            col3.metric("Zarar Kes (SL)", f"${stop_loss:.2f}")

            # Position size calculator for $30 profit target (1.5% TP)
            profit_per_dollar = 0.015  # 1.5% of invested capital
            required_capital = 30 / profit_per_dollar
            st.success(f"🎯 Günlük 30$ kar hedefine ulaşmak için bu işleme ${required_capital:,.2f} tutarında bir bakiye ile girmelisiniz.")

            # RSI calculation (14‑period)
            delta = price.diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            avg_gain = gain.rolling(window=14, min_periods=14).mean()
            avg_loss = loss.rolling(window=14, min_periods=14).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            last_rsi = rsi.iloc[-1]

            if last_rsi < 30:
                st.warning("⚠️ Piyasa aşırı satımda (Şelale), işlemi alırken dikkatli ol!")
            elif last_rsi > 70:
                st.warning("⚠️ Piyasa aşırı şişmiş, bu seviyeden long girmek riskli!")
            else:
                st.success("✅ Piyasa volatilitesi normal, emirler girilebilir.")

        st.markdown("---")

        # 5. Metrikleri Ekrana Bas
        col1, col2, col3 = st.columns(3)
        col1.metric("Toplam Getiri", f"% {portfolio.total_return() * 100:.2f}")
        win_rate = portfolio.trades.win_rate() * 100 if portfolio.trades.count() > 0 else 0
        col2.metric("Kazanma Oranı", f"% {win_rate:.2f}")
        col3.metric("Maksimum Düşüş", f"% {portfolio.max_drawdown() * 100:.2f}")

        # 6. İnteraktif Grafiği Çiz
        st.subheader("Sermaye Eğrisi (Equity Curve)")
        st.plotly_chart(portfolio.plot(), use_container_width=True)

except Exception as e:
    st.error(f"Sistemsel bir hata oluştu: {e}")
