import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import seaborn as sns
import numpy as np
import io
from datetime import date, timedelta

# --- 1. CẤU HÌNH TRANG VÀ TIÊU ĐỀ ---
st.set_page_config(
    page_title="Phân tích LST, NDVI, TVDI",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Công cụ Trực quan hóa Dữ liệu Môi trường")
st.markdown(
    "Phân tích **LST** (Nhiệt độ bề mặt - °C), **NDVI** (Chỉ số thảm thực vật) và **TVDI** (Chỉ số khô hạn)."
)

# --- 2. TẢI VÀ XỬ LÝ DỮ LIỆU ---
@st.cache_data
def load_and_preprocess_data(uploaded_file):
    try:
        if uploaded_file.name.endswith(('.xls', '.xlsx', '.xlsm')):
            df = pd.read_excel(uploaded_file)
        elif uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, encoding='utf-8')
        else:
            st.error("Chỉ hỗ trợ file Excel (.xlsx, .xlsm, .xls) hoặc CSV (.csv).")
            return None

        df.columns = df.columns.str.strip().str.upper()
        required_cols = ['POINT_X', 'POINT_Y', 'WARD', 'DATE', 'LST', 'NDVI', 'TVDI']
        if not all(col in df.columns for col in required_cols):
            missing = [c for c in required_cols if c not in df.columns]
            st.error(f"Thiếu cột bắt buộc: {', '.join(missing)}")
            return None

        df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce', dayfirst=True)
        df.dropna(subset=['DATE', 'LST', 'NDVI', 'TVDI', 'WARD'], inplace=True)
        return df
    except Exception as e:
        st.error(f"Lỗi xử lý file: {e}")
        return None


# --- 3. HÀM TẠO TÊN FILE ---
def generate_filename(chart_name, wards, start, end):
    ward_count = len(wards)
    if ward_count == len(st.session_state.all_wards):
        ward_abbr = "ALL"
    elif ward_count > 1:
        ward_abbr = f"{wards[0]}..._{ward_count}W"
    else:
        ward_abbr = wards[0]
    date_str = f"{start.strftime('%Y%m%d')}_{end.strftime('%Y%m%d')}"
    chart_abbr = chart_name.split(':')[0].split(' ')[0]
    return f"{chart_abbr}_{ward_abbr}_D{date_str}.png"


# --- 4. GIAO DIỆN NGƯỜI DÙNG ---
uploaded_file = st.file_uploader(
    "📤 Bước 1: Tải file dữ liệu (.xlsm, .xlsx, .csv)",
    type=["xlsm", "xlsx", "csv"]
)

if uploaded_file:
    df_raw = load_and_preprocess_data(uploaded_file)
    if df_raw is not None and not df_raw.empty:
        st.success(f"Đã tải {len(df_raw)} dòng dữ liệu.")
        min_date, max_date = df_raw['DATE'].min().date(), df_raw['DATE'].max().date()
        st.session_state.all_wards = sorted(df_raw['WARD'].unique())

        # --- SIDEBAR ---
        st.sidebar.header("⚙️ Bộ lọc Dữ liệu")
        st.sidebar.markdown("**Bước 2: Chọn Khoảng Ngày**")

        start_date = st.sidebar.date_input(
            "Ngày Bắt đầu",
            value=min_date,
            min_value=min_date,
            max_value=max_date
        )
        end_date = st.sidebar.date_input(
            "Ngày Kết thúc",
            value=max_date,
            min_value=min_date,
            max_value=max_date
        )

        if start_date > end_date:
            st.sidebar.error("Ngày Bắt đầu phải nhỏ hơn hoặc bằng Ngày Kết thúc.")
            start_date, end_date = end_date, start_date

        # --- CHỌN PHƯỜNG CÓ NÚT XÓA ---
        st.sidebar.markdown("**Bước 3: Chọn Phường (WARD)**")

        # Nếu chưa có trong session_state, khởi tạo mặc định
        if "selected_wards" not in st.session_state:
            st.session_state.selected_wards = st.session_state.all_wards.copy()


        # Hàm callback để reset danh sách chọn
        def reset_wards():
            if st.session_state.all_wards:
                st.session_state.selected_wards = [st.session_state.all_wards[0]]


        # Nút xóa hết — có key riêng để tránh trùng ID
        st.sidebar.button("🧹 Xóa hết & Chọn lại 1 phường", key="clear_wards_btn", on_click=reset_wards)

        # Widget multiselect — lấy dữ liệu từ session_state
        selected_wards = st.sidebar.multiselect(
            "Chọn Phường hiển thị",
            options=st.session_state.all_wards,
            default=st.session_state.selected_wards,
            key="selected_wards"
        )

        chart_options = {
            "Scatter: LST vs NDVI": "scatter_lst_ndvi",
            "Boxplot: Phân bố LST theo Phường": "boxplot_lst_ward",
            "Combined: LST, NDVI, TVDI theo Phường": "combined_chart",
            "Linear Regression: LST vs NDVI": "regplot_lst_ndvi",
            "Scatter: TVDI vs LST": "scatter_tvdi_lst",
            "Heatmap: LST trung bình theo Phường và Ngày": "heatmap_lst_ward_date",
            "Pairplot: Tương quan đa biến": "pairplot_variables"
        }

        st.sidebar.header("📊 Loại biểu đồ")
        chart_choice_name = st.sidebar.selectbox("Chọn loại biểu đồ", options=list(chart_options.keys()))
        chart_choice_key = chart_options[chart_choice_name]

        # --- XỬ LÝ VẼ ---
        if st.sidebar.button("Vẽ biểu đồ"):
            df_filtered = df_raw[
                (df_raw['DATE'] >= pd.to_datetime(start_date))
                & (df_raw['DATE'] <= pd.to_datetime(end_date))
                & (df_raw['WARD'].isin(selected_wards))
            ]

            if df_filtered.empty:
                st.error("Không có dữ liệu khớp với bộ lọc.")
            else:
                st.subheader(f"Biểu đồ: {chart_choice_name}")
                st.info(f"{len(df_filtered)} điểm dữ liệu, từ {start_date.strftime('%d/%m/%Y')} đến {end_date.strftime('%d/%m/%Y')}.")

                plot_data = None

                # --- 1. SCATTER ---
                if chart_choice_key == "scatter_lst_ndvi":
                    fig = px.scatter(
                        df_filtered, x="NDVI", y="LST", color="WARD",
                        title="Quan hệ LST - NDVI theo Phường",
                        labels={"NDVI": "NDVI", "LST": "LST (°C)"}
                    )
                    fig.update_layout(font=dict(size=16))
                    st.plotly_chart(fig, use_container_width=True)

                # --- 2. BOX PLOT ---
                elif chart_choice_key == "boxplot_lst_ward":
                    lst_top = df_filtered.groupby('WARD')['LST'].mean().sort_values(ascending=False).head(6).index
                    df_sample = df_filtered[df_filtered['WARD'].isin(lst_top)]
                    fig = px.box(
                        df_sample, x="WARD", y="LST", color="WARD",
                        title="Phân bố LST của 6 phường có nhiệt độ cao nhất",
                        labels={"WARD": "Phường", "LST": "LST (°C)"}
                    )
                    fig.update_layout(font=dict(size=16))
                    st.plotly_chart(fig, use_container_width=True)

                # --- 3. COMBINED ---
                elif chart_choice_key == "combined_chart":
                    avg_by_ward = df_filtered.groupby('WARD')[['LST', 'NDVI', 'TVDI']].mean().reset_index()
                    fig, ax1 = plt.subplots(figsize=(10, 6))
                    ax1.bar(avg_by_ward['WARD'], avg_by_ward['LST'], color='tab:blue', alpha=0.7, label='LST (°C)')
                    ax1.set_xlabel("Phường")
                    ax1.set_ylabel("LST (°C)", color='tab:blue')
                    ax2 = ax1.twinx()
                    ax2.plot(avg_by_ward['WARD'], avg_by_ward['NDVI'], color='tab:red', marker='o', label='NDVI')
                    ax2.plot(avg_by_ward['WARD'], avg_by_ward['TVDI'], color='tab:green', marker='s', linestyle='--', label='TVDI')
                    ax1.tick_params(axis='x', rotation=45)
                    ax1.legend(loc='upper left')
                    ax2.legend(loc='upper right')
                    st.pyplot(fig)

                # --- 4. LINEAR REGRESSION ---
                elif chart_choice_key == "regplot_lst_ndvi":
                    plt.figure(figsize=(8, 6))
                    sns.kdeplot(
                        data=df_filtered, x="NDVI", y="LST", fill=True, cmap="coolwarm", thresh=0.05, alpha=0.6
                    )
                    sns.regplot(
                        data=df_filtered, x="NDVI", y="LST", scatter_kws={'alpha': 0.4, 's': 30}, line_kws={'color': 'black'}
                    )
                    plt.title("Quan hệ hồi quy giữa NDVI và LST", fontsize=16)
                    plt.xlabel("NDVI")
                    plt.ylabel("LST (°C)")
                    st.pyplot(plt.gcf())

                # --- 5. SCATTER TVDI - LST ---
                elif chart_choice_key == "scatter_tvdi_lst":
                    fig = px.scatter(
                        df_filtered, x="TVDI", y="LST", color="WARD",
                        title="TVDI vs LST theo Phường",
                        labels={"TVDI": "TVDI", "LST": "LST (°C)"}
                    )
                    st.plotly_chart(fig, use_container_width=True)

                # --- 6. HEATMAP ---
                elif chart_choice_key == "heatmap_lst_ward_date":
                    df_heat = df_filtered.copy()
                    df_heat['DATE'] = df_heat['DATE'].dt.strftime('%Y-%m-%d')
                    pivot = df_heat.pivot_table(values='LST', index='WARD', columns='DATE', aggfunc='mean')
                    fig, ax = plt.subplots(figsize=(12, 6))
                    sns.heatmap(pivot, cmap='coolwarm', cbar_kws={'label': 'LST (°C)'}, ax=ax)
                    ax.set_title("Nhiệt độ bề mặt trung bình (LST) theo Phường và Ngày", fontsize=16)
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()
                    st.pyplot(fig)

                # --- 7. PAIRPLOT ---
                elif chart_choice_key == "pairplot_variables":
                    df_pair = df_filtered[['LST', 'NDVI', 'TVDI', 'WARD']].copy()
                    fig = sns.pairplot(df_pair, hue="WARD", diag_kind="kde", corner=True)
                    fig.fig.suptitle("Mối tương quan đa biến (LST, NDVI, TVDI)", y=1.02, fontsize=16)
                    st.pyplot(fig)
    else:
        st.warning("File không hợp lệ hoặc trống.")
else:
    st.info("💡 Hãy tải lên file dữ liệu (.xlsm, .xlsx, hoặc .csv).")