import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import numpy as np
import io
import os

# --- 1. CẤU HÌNH TRANG VÀ TIÊU ĐỀ ---
st.set_page_config(
    page_title="Phân tích LST, NDVI, TVDI",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🌡️ Công cụ Trực quan hóa Dữ liệu Môi trường")
st.markdown(
    "Sử dụng **LST** (Land Surface Temperature), **NDVI** (Normalized Difference Vegetation Index) và **TVDI** (Temperature Vegetation Dryness Index) để phân tích.")


# --- 2. TẢI VÀ XỬ LÝ DỮ LIỆU BAN ĐẦU ---

# Hàm đọc và chuẩn hóa dữ liệu
@st.cache_data
def load_and_preprocess_data(uploaded_file):
    """Đọc, chuẩn hóa, và tính toán các giá trị trung bình."""
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
            missing_cols = [col for col in required_cols if col not in df.columns]
            st.error(f"File thiếu các cột bắt buộc sau: {', '.join(missing_cols)}")
            return None

        # Xử lý định dạng ngày tháng dd/mm/yyyy bằng dayfirst=True
        df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce', dayfirst=True)
        df.dropna(subset=['DATE', 'LST', 'NDVI', 'TVDI', 'WARD'], inplace=True)

        df['MONTH'] = df['DATE'].dt.month

        return df

    except Exception as e:
        st.error(f"Lỗi khi xử lý file: {e}")
        return None


# Hàm tạo tên file cho biểu đồ
def generate_filename(chart_name, selected_wards, selected_months):
    ward_str = "_".join(selected_wards)[:30].replace(' ', '-')
    month_str = "_".join(map(str, selected_months))
    chart_abbr = chart_name.split(':')[0].replace(' ', '_').replace('/', '').replace(',', '')
    return f"{chart_abbr}_W{ward_str}_M{month_str}.png"


# Nút tải file
uploaded_file = st.file_uploader(
    "📤 **Bước 1: Tải file dữ liệu (.xlsm, .xlsx, .csv)**",
    type=["xlsm", "xlsx", "csv"],
    help="File phải có các cột: POINT_X, POINT_Y, WARD, DATE, LST, NDVI, TVDI. Định dạng ngày tháng phải là dd/mm/yyyy."
)

if uploaded_file:
    df_raw = load_and_preprocess_data(uploaded_file)

    if df_raw is not None and not df_raw.empty:
        st.success(f"Tải thành công! Tổng số dòng: {len(df_raw)}")

        # --- 3. BẢNG ĐIỀU KHIỂN (SIDEBAR) ---
        st.sidebar.header("⚙️ Bộ lọc Dữ liệu")

        all_months = sorted(df_raw['MONTH'].unique())
        all_wards = sorted(df_raw['WARD'].unique())

        selected_months = st.sidebar.multiselect(
            "**Bước 2: Chọn Tháng**",
            options=all_months,
            default=all_months,
            format_func=lambda x: f"Tháng {x}"
        )

        selected_wards = st.sidebar.multiselect(
            "**Bước 3: Chọn Quận/Phường (WARD)**",
            options=all_wards,
            default=all_wards
        )

        chart_options = {
            "Scatter: LST vs NDVI": "scatter_lst_ndvi",
            "Boxplot: Phân bố LST theo Ward": "boxplot_lst_ward",
            "Heatmap: Tương quan LST/NDVI/TVDI": "heatmap_corr",
            "Combined: LST, NDVI, TVDI theo Ward (Bar & Line)": "combined_chart",
            "Linear Regression: LST vs NDVI": "regplot_lst_ndvi",
            "Scatter: TVDI vs LST": "scatter_tvdi_lst"
        }

        st.sidebar.header("📊 Loại Biểu đồ")
        chart_choice_name = st.sidebar.selectbox(
            "**Bước 4: Chọn Biểu đồ để vẽ**",
            options=list(chart_options.keys())
        )
        chart_choice_key = chart_options[chart_choice_name]

        # Nút vẽ biểu đồ
        if st.sidebar.button("🎨 **Vẽ Biểu đồ**"):

            # --- 4. ÁP DỤNG BỘ LỌC ---
            df_filtered = df_raw[
                (df_raw['MONTH'].isin(selected_months)) &
                (df_raw['WARD'].isin(selected_wards))
                ]

            if df_filtered.empty:
                st.error("Không có dữ liệu nào khớp với bộ lọc đã chọn.")
            else:

                # --- SỬA LỖI TÊN BIỂU ĐỒ DÀI VÀ THÔNG TIN BỘ LỌC ---
                base_title = chart_choice_name.split(':')[0]

                st.subheader(f"Biểu đồ: {base_title}")
                st.info(
                    f"Dữ liệu được lọc: {len(df_filtered)} điểm. (Ward: {', '.join(selected_wards)}, Tháng: {', '.join(map(str, selected_months))})")

                avg_by_ward = df_filtered.groupby('WARD')[['LST', 'NDVI', 'TVDI']].mean().reset_index()

                # --- 5. VẼ BIỂU ĐỒ VÀ XỬ LÝ TẢI XUỐNG ---

                plot_data = None
                mime_type = "image/png"

                if chart_choice_key == "scatter_lst_ndvi":
                    fig = px.scatter(
                        df_filtered, x="NDVI", y="LST", color="WARD",
                        title=f"1️⃣ {base_title} theo Ward",
                        hover_data={'DATE': True, 'POINT_X': True, 'POINT_Y': True}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    # FIX: Bỏ fig.to_image() để tránh lỗi Kaleido trên Streamlit Cloud
                    st.markdown("**(💡 Di chuột lên góc trên phải biểu đồ để tải ảnh PNG)**")

                elif chart_choice_key == "boxplot_lst_ward":
                    lst_mean_filtered = df_filtered.groupby('WARD')['LST'].mean().sort_values(ascending=False).head(
                        6).index
                    df_sample = df_filtered[df_filtered['WARD'].isin(lst_mean_filtered)]

                    if df_sample.empty:
                        st.warning("Không đủ dữ liệu để vẽ Boxplot cho 6 Ward có LST cao nhất.")
                    else:
                        fig = px.box(
                            df_sample, x="WARD", y="LST", color="WARD",
                            title=f"2️⃣ Phân bố LST của 6 Ward có LST TB cao nhất",
                            height=600
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        # FIX: Bỏ fig.to_image()
                        st.markdown("**(💡 Di chuột lên góc trên phải biểu đồ để tải ảnh PNG)**")

                elif chart_choice_key == "heatmap_corr":
                    corr = df_filtered[['LST', 'NDVI', 'TVDI']].corr()
                    fig = px.imshow(
                        corr, text_auto=True, aspect="auto",
                        color_continuous_scale='RdBu_r',
                        title=f"3️⃣ Ma trận Tương quan LST, NDVI, TVDI"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    # FIX: Bỏ fig.to_image()
                    st.markdown("**(💡 Di chuột lên góc trên phải biểu đồ để tải ảnh PNG)**")

                elif chart_choice_key == "combined_chart":
                    if avg_by_ward.empty:
                        st.warning("Không đủ dữ liệu trung bình để vẽ Combined Chart.")
                    else:
                        # Biểu đồ Matplotlib (sử dụng st.download_button)
                        mpl_fig, ax1 = plt.subplots(figsize=(10, 6))

                        color_bar = '#3b82f6'
                        color_line1 = '#ef4444'
                        color_line2 = '#22c55e'

                        ax1.bar(avg_by_ward['WARD'], avg_by_ward['LST'], color=color_bar, alpha=0.7,
                                label='Mean LST (°C)')
                        ax1.set_xlabel("Ward")
                        ax1.set_ylabel("Mean LST (°C)", color=color_bar)
                        ax1.tick_params(axis='y', labelcolor=color_bar)
                        ax1.tick_params(axis='x', rotation=45)

                        ax2 = ax1.twinx()
                        ax2.plot(avg_by_ward['WARD'], avg_by_ward['NDVI'], color=color_line1, marker='o', linewidth=2,
                                 label='Mean NDVI')
                        ax2.plot(avg_by_ward['WARD'], avg_by_ward['TVDI'], color=color_line2, marker='s', linewidth=2,
                                 linestyle='--', label='Mean TVDI')
                        ax2.set_ylabel("NDVI / TVDI", color='black')
                        ax2.tick_params(axis='y', labelcolor='black')

                        lines1, labels1 = ax1.get_legend_handles_labels()
                        lines2, labels2 = ax2.get_legend_handles_labels()
                        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
                        ax1.set_title(f"4️⃣ {base_title} theo Ward")

                        plt.tight_layout()
                        st.pyplot(mpl_fig)

                        # Xuất ảnh ra buffer để tải xuống
                        buf = io.BytesIO()
                        mpl_fig.savefig(buf, format="png", dpi=300)
                        plt.close(mpl_fig)

                        plot_data = buf.getvalue() # Chỉ gán plot_data cho Matplotlib

                elif chart_choice_key == "regplot_lst_ndvi":
                    fig = px.scatter(
                        df_filtered, x="NDVI", y="LST",
                        trendline="ols", color="WARD",
                        title=f"5️⃣ {base_title}: LST vs NDVI",
                        hover_data={'DATE': True}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    # FIX: Bỏ fig.to_image()
                    st.markdown("**(💡 Di chuột lên góc trên phải biểu đồ để tải ảnh PNG)**")

                elif chart_choice_key == "scatter_tvdi_lst":
                    fig = px.scatter(
                        df_filtered, x="TVDI", y="LST", color="WARD",
                        title=f"6️⃣ {base_title} theo Ward",
                        hover_data={'DATE': True, 'POINT_X': True, 'POINT_Y': True}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    # FIX: Bỏ fig.to_image()
                    st.markdown("**(💡 Di chuột lên góc trên phải biểu đồ để tải ảnh PNG)**")

                # --- NÚT TẢI XUỐNG CHUNG (CHỈ DÙNG CHO MATPLOTLIB) ---
                if plot_data is not None:
                    # Nút này chỉ xuất hiện khi Combined Chart (Matplotlib) được chọn
                    st.download_button(
                        label="📥 Tải xuống Biểu đồ (PNG)",
                        data=plot_data,
                        file_name=generate_filename(chart_choice_name, selected_wards, selected_months),
                        mime=mime_type
                    )


    elif uploaded_file and (df_raw is None or df_raw.empty):
        st.warning("Vui lòng tải lên một file hợp lệ và đảm bảo file không trống.")

else:
    st.info("💡 Bắt đầu bằng cách tải lên file dữ liệu (.xlsm, .xlsx, hoặc .csv) của bạn.")