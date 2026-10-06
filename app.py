import io
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ==============================================================================
# KONFIGURASI HALAMAN STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="Fraud & Surveillance Analytics - Merchant Transaksi 24 Jam",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (CSS)
st.markdown("""
<style>
    .main-header {
        font-size: 26px;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 4px;
    }
    .sub-header {
        font-size: 14px;
        color: #64748B;
        margin-bottom: 20px;
    }
    .kpi-card {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border-left: 5px solid #3B82F6;
        margin-bottom: 12px;
    }
    .kpi-title {
        font-size: 13px;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-value {
        font-size: 24px;
        font-weight: 700;
        color: #0F172A;
        margin-top: 4px;
    }
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================
def format_rupiah(val):
    """Format angka ke format mata uang Rupiah"""
    try:
        return f"Rp {val:,.0f}".replace(",", ".")
    except:
        return "Rp 0"

def clean_and_prepare_data(raw_df):
    """Membersihkan dan menstandarisasi data transaksi harian 24 jam"""
    df = raw_df.copy()
    
    # 1. Pastikan kolom string
    if 'AccountNumber' in df.columns:
        df['AccountNumber'] = df['AccountNumber'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    if 'CustomerName' in df.columns:
        df['CustomerName'] = df['CustomerName'].astype(str).str.strip()
    if 'TransactionDate' in df.columns:
        df['TransactionDate'] = pd.to_datetime(df['TransactionDate'], errors='coerce').dt.strftime('%Y-%m-%d')
        
    # 2. Format kolom 'Waktu' dari angka 0..23 atau teks menjadi '00:00'..'23:00'
    if 'Waktu' in df.columns:
        df['Waktu'] = df['Waktu'].astype(str).str.replace(':00', '', regex=False).str.strip()
        df['Waktu'] = df['Waktu'].str.zfill(2) + ':00'
        
    # 3. Konversi nilai numerik
    for col in ['TotalFrequency', 'TotalTransaction']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    return df

def generate_sample_data():
    """Membuat data dummy transaksi 24 jam untuk testing/demo"""
    dates = pd.date_range(start='2026-10-01', periods=3, freq='D').strftime('%Y-%m-%d').tolist()
    accounts = [
        ("10530180527", "PT MITRA PEDAGANG INDONESIA"),
        ("10530190112", "WARUNG OLYMPUS MAXX"),
        ("10530177890", "KEDAI MAKMUR SEJAHTERA"),
        ("10530122345", "TOKO ZEUS JOKI"),
        ("10530199887", "CV BERKAH CIPTA ABADI"),
        ("10530144556", "REPAINT NO SHIT STORE"),
        ("10530133441", "MCD TEST STORE 1"),
        ("10530166778", "PT CYBER SMART NETWORK"),
        ("10530155667", "GROSIR KENCANA ELEKTRONIK"),
        ("10530188990", "ANGKRINGAN MALAM JOSS"),
        ("10530111223", "WARUNG KOPI NIKMAT"),
        ("10530144778", "SUMBER REJEKI ABADI")
    ]
    
    rows = []
    trx_id = 1
    for date in dates:
        for acc, cust in accounts:
            for hour in range(24):
                waktu_str = f"{str(hour).zfill(2)}:00"
                # Buat pola acak transaksi
                is_active = np.random.choice([0, 1], p=[0.2, 0.8])
                if is_active:
                    freq = int(np.random.randint(1, 150))
                    # Simulasikan nominal
                    base_nominal = np.random.choice([25000, 50000, 100000, 500000, 1500000])
                    nominal = freq * base_nominal + np.random.randint(1000, 50000)
                else:
                    freq = 0
                    nominal = 0
                
                rows.append({
                    "ID": trx_id,
                    "TransactionDate": date,
                    "Apl": "QRIS",
                    "AccountNumber": acc,
                    "CustomerName": cust,
                    "Waktu": waktu_str,
                    "TotalFrequency": freq,
                    "TotalTransaction": nominal,
                    "LastUpdated": f"{date} 23:59:59"
                })
                trx_id += 1
                
    return pd.DataFrame(rows)

# ==============================================================================
# SIDEBAR: PENGATURAN & UPLOAD DATA
# ==============================================================================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/shield-check--v1.png", width=64)
    st.title("Fraud Surveillance")
    st.markdown("---")
    
    st.subheader("📁 Sumber Data")
    uploaded_file = st.file_uploader(
        "Unggah File Transaksi (CSV / Excel)", 
        type=["csv", "xlsx", "xls"],
        help="Upload file yang memiliki kolom: TransactionDate, AccountNumber, CustomerName, Waktu, TotalFrequency, TotalTransaction"
    )
    
    use_sample = st.checkbox("Gunakan Data Demo / Simulasi", value=(uploaded_file is None))
    
    df_raw = None
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_raw = pd.read_csv(uploaded_file)
            else:
                df_raw = pd.read_excel(uploaded_file)
            st.success(f"File '{uploaded_file.name}' berhasil dimuat!")
        except Exception as e:
            st.error(f"Gagal membaca file: {e}")
    elif use_sample:
        df_raw = generate_sample_data()
        st.info("Menggunakan data simulasi transaksi 24 jam.")
        
    st.markdown("---")

# Cek ketersediaan data
if df_raw is None or df_raw.empty:
    st.warning("Silakan unggah file transaksi atau centang 'Gunakan Data Demo' pada sidebar.")
    st.stop()

# Bersihkan dan persiapkan data
df = clean_and_prepare_data(df_raw)

# Validasi kolom wajib
required_cols = ['TransactionDate', 'AccountNumber', 'CustomerName', 'Waktu', 'TotalFrequency', 'TotalTransaction']
missing_cols = [c for c in required_cols if c not in df.columns]
if missing_cols:
    st.error(f"Kolom wajib tidak lengkap dalam file: {missing_cols}")
    st.stop()

# ==============================================================================
# SIDEBAR: FILTER DATA
# ==============================================================================
with st.sidebar:
    st.subheader("🔍 Filter Analisis")
    
    # Filter 1: Tanggal
    available_dates = sorted(df['TransactionDate'].dropna().unique().tolist())
    selected_dates = st.multiselect(
        "📅 Pilih Tanggal Transaksi:",
        options=available_dates,
        default=available_dates[:1] if len(available_dates) > 0 else []
    )
    
    # Filter 2: No. Rekening (AccountNumber) — cascading setelah filter tanggal
    df_filtered_date = df[df['TransactionDate'].isin(selected_dates)] if selected_dates else df
    available_accounts = sorted(df_filtered_date['AccountNumber'].unique().tolist())
    
    select_all_accounts = st.checkbox("Pilih Semua No. Rekening", value=True, key="chk_acc")
    if select_all_accounts:
        selected_accounts = available_accounts
    else:
        selected_accounts = st.multiselect(
            "🏦 Pilih No. Rekening:",
            options=available_accounts,
            default=available_accounts[:5] if len(available_accounts) >= 5 else available_accounts
        )

    # Filter 3: Nama Customer (CustomerName) — cascading setelah filter rekening
    df_filtered_acc = df_filtered_date[df_filtered_date['AccountNumber'].isin(selected_accounts)] if selected_accounts else df_filtered_date
    available_customers = sorted(df_filtered_acc['CustomerName'].unique().tolist())
    
    select_all_customers = st.checkbox("Pilih Semua Nama Customer", value=True, key="chk_cust")
    if select_all_customers:
        selected_customers = available_customers
    else:
        selected_customers = st.multiselect(
            "👤 Pilih Nama Customer:",
            options=available_customers,
            default=available_customers[:5] if len(available_customers) >= 5 else available_customers
        )
        
    st.markdown("---")
    top_n_chart = st.slider("Jumlah Top Merchant di Line Chart:", min_value=5, max_value=30, value=10)

# Terapkan Filter (Cascading: Tanggal -> No. Rekening -> Nama Customer)
mask = (
    (df['TransactionDate'].isin(selected_dates if selected_dates else available_dates)) &
    (df['AccountNumber'].isin(selected_accounts if selected_accounts else available_accounts)) &
    (df['CustomerName'].isin(selected_customers if selected_customers else available_customers))
)
df_filtered = df[mask].copy()

# ==============================================================================
# HEADER UTAMA
# ==============================================================================
st.markdown('<div class="main-header">🛡️ Surveillance & Fraud Analytics - Debit Transaksi 24 Jam</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Monitoring anomali frekuensi (#) dan volume nominal (IDR) per jam pada rekening merchant</div>', unsafe_allow_html=True)

# ==============================================================================
# 1. SCORECARD KPI (ATAS)
# ==============================================================================
col1, col2, col3, col4 = st.columns(4)

total_customer = df_filtered['CustomerName'].nunique()
total_account = df_filtered['AccountNumber'].nunique()
total_frequency = df_filtered['TotalFrequency'].sum()
total_nominal = df_filtered['TotalTransaction'].sum()

with col1:
    st.markdown(f"""
    <div class="kpi-card" style="border-left-color: #3B82F6;">
        <div class="kpi-title">Total Customer</div>
        <div class="kpi-value">{total_customer:,}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card" style="border-left-color: #10B981;">
        <div class="kpi-title">Total No. Rekening</div>
        <div class="kpi-value">{total_account:,}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card" style="border-left-color: #F59E0B;">
        <div class="kpi-title">Total Frekuensi (#)</div>
        <div class="kpi-value">{int(total_frequency):,}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-card" style="border-left-color: #8B5CF6;">
        <div class="kpi-title">Total Nominal (IDR)</div>
        <div class="kpi-value">{format_rupiah(total_nominal)}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==============================================================================
# 2. LINE CHART PERGERAKAN TRANSAKSI 24 JAM (TENGAH)
# ==============================================================================
st.subheader(f"📈 Tren Pergerakan Transaksi 24 Jam (Top {top_n_chart} Merchant)")

# Kontrol Pilihan Metrik Chart
metric_choice = st.radio(
    "Pilih Metrik Visualisasi:",
    options=["Nominal Transaksi (IDR)", "Jumlah Frekuensi (#)"],
    horizontal=True
)

# Tentukan Top N Merchant berdasarkan Total Nominal
top_merchants_list = (
    df_filtered.groupby('CustomerName')['TotalTransaction']
    .sum()
    .nlargest(top_n_chart)
    .index
    .tolist()
)

df_top = df_filtered[df_filtered['CustomerName'].isin(top_merchants_list)].copy()

# Buat list jam lengkap 00:00 .. 23:00 untuk kontinuitas chart
all_hours = [f"{str(h).zfill(2)}:00" for h in range(24)]

# Agregasi data untuk chart
if metric_choice == "Nominal Transaksi (IDR)":
    chart_data = (
        df_top.groupby(['Waktu', 'CustomerName'])['TotalTransaction']
        .sum()
        .reset_index()
    )
    y_axis_col = 'TotalTransaction'
    y_title = 'Nominal Transaksi (Rp)'
else:
    chart_data = (
        df_top.groupby(['Waktu', 'CustomerName'])['TotalFrequency']
        .sum()
        .reset_index()
    )
    y_axis_col = 'TotalFrequency'
    y_title = 'Frekuensi Transaksi (#)'

# Plot menggunakan Plotly Express
if not chart_data.empty:
    fig = px.line(
        chart_data,
        x='Waktu',
        y=y_axis_col,
        color='CustomerName',
        markers=True,
        title=f"Distribusi {metric_choice} dari Jam 00:00 s.d. 23:00",
        labels={'Waktu': 'Jam Transaksi (24 Jam)', y_axis_col: y_title, 'CustomerName': 'Merchant'}
    )
    
    fig.update_layout(
        xaxis=dict(
            categoryorder='array',
            categoryarray=all_hours,
            tickmode='linear',
            dtick=1,
            gridcolor='#E2E8F0'
        ),
        yaxis=dict(gridcolor='#E2E8F0'),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.35,
            xanchor="center",
            x=0.5
        ),
        height=480,
        margin=dict(l=20, r=20, t=50, b=80),
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Tidak ada data untuk ditampilkan pada grafik.")

st.markdown("<br>", unsafe_allow_html=True)

# ==============================================================================
# 3. PEMROSESAN & TAMPILAN TABEL DETAIL BERTINGKAT (MULTIINDEX)
# ==============================================================================
st.subheader("📋 Rincian Transaksi Per Jam (MultiIndex Pivot)")

# A. Pivot Dataframe per Jam
df_pivot_hours = df_filtered.pivot_table(
    index=['TransactionDate', 'AccountNumber', 'CustomerName'],
    columns='Waktu',
    values=['TotalFrequency', 'TotalTransaction'],
    aggfunc='sum',
    fill_value=0
)

# B. Hitung Grand Total
df_grand_total = df_filtered.groupby(['TransactionDate', 'AccountNumber', 'CustomerName']).agg(
    TotalFrequency=('TotalFrequency', 'sum'),
    TotalTransaction=('TotalTransaction', 'sum')
)

# C. Swap level MultiIndex kolom jam agar 'Jam' di atas dan '#' / 'IDR' di bawah
if not df_pivot_hours.empty:
    df_pivot_hours = df_pivot_hours.swaplevel(0, 1, axis=1)
    df_pivot_hours = df_pivot_hours.sort_index(axis=1, level=0)
    df_pivot_hours = df_pivot_hours.rename(columns={'TotalFrequency': '#', 'TotalTransaction': 'IDR'})
    
    # Buat MultiIndex untuk Grand Total agar bisa digabungkan
    df_grand_total.columns = pd.MultiIndex.from_tuples([('GRAND TOTAL', '#'), ('GRAND TOTAL', 'IDR')])
    
    # Gabungkan Grand Total di sebelah kiri, diikuti oleh kolom jam 00:00 .. 23:00
    df_final_pivot = pd.concat([df_grand_total, df_pivot_hours], axis=1).fillna(0)
else:
    df_final_pivot = pd.DataFrame()

# Tampilkan Tabel di Streamlit
if not df_final_pivot.empty:
    # Reset index agar tampil sebagai kolom biasa yang bersih
    df_display = df_final_pivot.reset_index()
    
    st.dataframe(
        df_final_pivot,
        use_container_width=True,
        height=450
    )
    
    # ==========================================================================
    # 4. FITUR DOWNLOAD EXCEL
    # ==========================================================================
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df_final_pivot.to_excel(writer, sheet_name='Pivot_24_Jam')
    excel_data = excel_buffer.getvalue()
    
    st.download_button(
        label="📥 Download Tabel Detail (Excel .xlsx)",
        data=excel_data,
        file_name=f"Surveillance_Transaksi_24Jam_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Tidak ada data tabel untuk filter yang dipilih.")
