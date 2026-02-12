import streamlit as st
import pandas as pd
import base64
from datetime import datetime, date
import streamlit.components.v1 as components

# --- IMPORT MODULE ---
try:
    from market_data import BondowosoMarketData
except ImportError:
    st.error("❌ 'market_data.py' not found.")
    st.stop()

st.set_page_config(page_title="Bondowoso Market Generator", page_icon="🥦", layout="wide")

# --- 1. HTML GENERATOR ---
def generate_html(df, col_prev, col_curr):
    
    # Validation
    if col_prev not in df.columns or col_curr not in df.columns:
        return f"<h3 style='color:red; text-align:center;'>Error: Kolom {col_prev} atau {col_curr} tidak ditemukan.</h3>"

    def fmt_date(d):
        try: return datetime.strptime(d, "%Y-%m-%d").strftime("%d %b")
        except: return d
        
    d_curr_txt = fmt_date(col_curr)
    d_prev_txt = fmt_date(col_prev)

    cards_html = ""
    
    for index, row in df.iterrows():
        name = row['Variant Name']
        
        try:
            p_curr = int(row[col_curr]) if pd.notna(row[col_curr]) else 0
            p_prev = int(row[col_prev]) if pd.notna(row[col_prev]) else 0
        except:
            p_curr, p_prev = 0, 0

        diff = p_curr - p_prev
        
        if diff > 0:
            trend_bg = "#ff5252" # Red
            trend_arrow = "▲"
            trend_txt = f"+ Rp {diff:,.0f}"
        elif diff < 0:
            trend_bg = "#4caf50" # Green
            trend_arrow = "▼"
            trend_txt = f"- Rp {abs(diff):,.0f}"
        else:
            trend_bg = "#5c6bc0" # Soft Blue
            trend_arrow = "-"
            trend_txt = "Stabil"

        cards_html += f"""
        <div class="card">
            <div class="card-header">{name}</div>
            <div class="card-body">
                <div class="price-area">
                    <div class="price-pill neutral">
                        <span class="date-tag">{d_prev_txt}</span>
                        <span class="price-tag small">Rp {p_prev:,.0f}</span>
                    </div>
                    
                    <div class="price-pill dynamic" style="background-color: {trend_bg};">
                        <span class="date-tag">{d_curr_txt.upper()}</span>
                        <span class="price-tag">Rp {p_curr:,.0f}</span>
                        <div class="trend-indicator">
                            {trend_arrow} {trend_txt}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@500;700&display=swap');
            body {{ font-family: 'Poppins', sans-serif; background-color: #f0f2f5; padding: 20px; text-align: center; }}
            .container {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; max-width: 1200px; margin: 0 auto; }}
            
            .card {{ 
                background-color: #283593; 
                border-radius: 25px; 
                padding: 15px; 
                box-shadow: 0 4px 15px rgba(0,0,0,0.2); 
                display: flex; 
                flex-direction: column; 
                height: 140px; 
            }}
            .card-header {{ 
                color: white; 
                font-weight: 700; 
                font-size: 16px; 
                margin-bottom: 15px; 
                height: 40px; 
                display: flex; 
                align-items: center; 
                justify-content: center; 
                line-height: 1.2; 
                overflow: hidden; 
            }}
            .card-body {{ 
                display: flex; 
                flex: 1; 
                justify-content: center; 
                align-items: center; 
            }}
            .price-area {{ 
                width: 100%;
                display: flex; 
                flex-direction: column; 
                align-items: center;
                gap: 10px; 
                justify-content: center; 
            }}
            .price-pill {{ 
                border-radius: 12px; 
                padding: 8px 15px; 
                display: flex; 
                justify-content: space-between; 
                align-items: center; 
                box-shadow: 0 2px 5px rgba(0,0,0,0.2); 
                width: 100%;
                box-sizing: border-box;
            }}
            .price-pill.neutral {{ background-color: rgba(255,255,255,0.2); }}
            
            .date-tag {{ font-size: 11px; color: rgba(255,255,255,0.8); text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }}
            .price-tag {{ font-size: 17.5px; font-weight: 700; color: white; }}
            .price-tag.small {{ font-size: 20px; color: rgba(255,255,255,0.9); }}
            
            .trend-indicator {{ 
                font-size: 11px; 
                font-weight: 700; 
                color: rgba(0,0,0,0.4); 
                background-color: rgba(255,255,255,0.9);
                padding: 2px 6px;
                border-radius: 4px;
                margin-left: 10px;
                display: inline-block;
            }}
        </style>
    </head>
    <body>
        <h1 style="color:#283593">Harga Pangan Kabupaten Bondowoso</h1>
        <p style="color:#666">Periode {d_prev_txt} - {d_curr_txt} {col_curr[:4]}</p>
        <div class="container">
            {cards_html}
        </div>
    </body>
    </html>
    """

# --- 2. SIDEBAR LOGIC ---
st.sidebar.header("⚙️ Pengaturan")

today = date.today()
default_start = today.replace(day=1) 
start_date = st.sidebar.date_input("Tanggal Awal", default_start)
end_date = st.sidebar.date_input("Tanggal Akhir", today)

# --- NEW: VALIDATE WEEKENDS (0=Mon, 5=Sat, 6=Sun) ---
if start_date.weekday() >= 5:
    st.sidebar.error("❌ Tanggal Awal jatuh pada Sabtu/Minggu (Data Kosong). Harap ganti tanggal.")
    st.stop()

if end_date.weekday() >= 5:
    st.sidebar.error("❌ Tanggal Akhir jatuh pada Sabtu/Minggu (Data Kosong). Harap ganti tanggal.")
    st.stop()

# WORKAROUND:
days_diff = (today - start_date).days + 1 
if days_diff < 2: days_diff = 2 

if st.sidebar.button("🔄 Refresh Data From API", type="primary"):
    with st.spinner(f"Fetching last {days_diff} days (to include {start_date})..."):
        market = BondowosoMarketData()
        df = market.get_data(days=days_diff, save_csv=False)
        st.session_state['data'] = df
        st.success("Data Updated!")

# --- 3. MAIN UI ---
st.title("🛒 Generator Harga Pasar")

if 'data' in st.session_state and st.session_state['data'] is not None:
    df_raw = st.session_state['data']
    
    st.subheader("📝 Pilih Komoditas")
    all_variants = df_raw['Variant Name'].unique().tolist()
    
    selected_variants = st.multiselect(
        "Centang komoditas:",
        options=all_variants,
        default=all_variants
    )
    
    if selected_variants:
        df = df_raw[df_raw['Variant Name'].isin(selected_variants)]
    else:
        st.warning("Silakan pilih minimal satu komoditas.")
        df = pd.DataFrame() 

    if not df.empty:
        available_dates = [c for c in df.columns if c not in ['Var ID', 'Variant Name']]
        available_dates.sort()
        
        target_curr = end_date.strftime("%Y-%m-%d")
        target_prev = start_date.strftime("%Y-%m-%d")
        
        if target_curr in available_dates and target_prev in available_dates:
            col_curr = target_curr
            col_prev = target_prev
            
            cols_to_show = ['Variant Name', col_prev, col_curr]
            st.subheader("📊 Data Table")
            st.dataframe(df[cols_to_show], use_container_width=True)
            
            html_code = generate_html(df, col_prev, col_curr)
            
            st.subheader("🎨 Visual Preview")
            components.html(html_code, height=800, scrolling=True)
            
            st.subheader("📥 Export")
            st.download_button(
                label="Download HTML File",
                data=html_code,
                file_name=f"Harga_Pasar_{target_prev}_to_{target_curr}.html",
                mime="text/html"
            )
        else:
            st.warning(f"⚠️ Data untuk tanggal {target_prev} atau {target_curr} tidak ditemukan dalam respon API.")
            st.write("Tanggal yang tersedia:", available_dates)
            st.info("Tips: Pastikan 'Tanggal Awal' tidak terlalu lampau dan data hari ini sudah terbit di Kemendag.")
else:
    st.info("👈 Select dates and click **Refresh Data From API** to start.")