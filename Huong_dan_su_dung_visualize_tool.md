
# 🌍 Công cụ Trực quan hóa Dữ liệu Môi trường

Ứng dụng Streamlit cho phép phân tích và hiển thị dữ liệu **LST**, **NDVI**, và **TVDI** theo thời gian và phường.  
Hỗ trợ người dùng xem, so sánh và đánh giá mức độ nóng, xanh, khô hạn của từng khu vực.

---

## 🧠 Mục tiêu
- Hiển thị mối tương quan giữa **LST** (nhiệt độ bề mặt), **NDVI** (thảm thực vật) và **TVDI** (chỉ số khô hạn).  
- Hỗ trợ nhà nghiên cứu, chuyên viên GIS, và cơ quan quản lý môi trường theo dõi biến động khí hậu đô thị.

---

## 🧩 Cấu trúc dữ liệu đầu vào

File dữ liệu phải chứa **ít nhất các cột sau** (không phân biệt hoa thường):

| Cột        | Ý nghĩa |
|-------------|----------|
| `POINT_X`   | Kinh độ |
| `POINT_Y`   | Vĩ độ |
| `WARD`      | Tên phường |
| `DATE`      | Ngày đo (định dạng dd/mm/yyyy hoặc yyyy-mm-dd) |
| `LST`       | Nhiệt độ bề mặt (°C) |
| `NDVI`      | Chỉ số thảm thực vật |
| `TVDI`      | Chỉ số khô hạn |

Nếu thiếu cột nào, ứng dụng sẽ báo lỗi ngay.

---

## ⚙️ Cài đặt môi trường

### 1️⃣ Cài Python
Phiên bản **>= 3.9**. Tải từ [python.org/downloads](https://www.python.org/downloads/).

### 2️⃣ Tạo môi trường ảo
```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate  # macOS / Linux
```

### 3️⃣ Cài các thư viện cần thiết
```bash
pip install streamlit pandas matplotlib seaborn plotly numpy openpyxl
```

---

## 🚀 Cách chạy ứng dụng

Trong thư mục chứa file `visualize_tool.py`, chạy:
```bash
streamlit run visualize_tool.py
```

Sau đó mở trình duyệt và truy cập địa chỉ:
```
http://localhost:8501
```

---

## 🧭 Hướng dẫn sử dụng

### 📤 Bước 1: Tải dữ liệu
- Nhấn **“📤 Bước 1: Tải file dữ liệu”**
- Chọn file `.xlsx`, `.xlsm`, hoặc `.csv`
- Nếu hợp lệ, ứng dụng sẽ báo:  
  > “✅ Đã tải X dòng dữ liệu”

---

### 📅 Bước 2: Chọn khoảng ngày
- Chọn **Ngày Bắt đầu** và **Ngày Kết thúc** trong thanh bên trái.  
- Nếu nhập sai thứ tự ngày, ứng dụng sẽ tự đảo lại.

---

### 🏙️ Bước 3: Chọn Phường (WARD)
- Chọn một hoặc nhiều phường trong danh sách.
- Muốn xóa hết và trở về 1 phường mặc định → bấm:  
  > 🧹 **Xóa hết & Chọn lại 1 phường**

---

### 📊 Bước 4: Chọn loại biểu đồ

| Biểu đồ | Mô tả |
|----------|--------|
| Scatter: LST vs NDVI | Quan hệ giữa nhiệt độ và thảm thực vật |
| Boxplot: Phân bố LST theo Phường | So sánh nhiệt độ giữa các phường |
| Combined: LST, NDVI, TVDI theo Phường | Kết hợp cột và đường |
| Linear Regression: LST vs NDVI | Hồi quy tuyến tính |
| Scatter: TVDI vs LST | Quan hệ giữa khô hạn và nhiệt độ |
| Heatmap: LST trung bình theo Phường và Ngày | Bản đồ nhiệt |
| Pairplot: Tương quan đa biến | Mối tương quan giữa LST, NDVI, TVDI |

---

### 🎨 Bước 5: Nhấn “Vẽ biểu đồ”
Ứng dụng hiển thị:
- Số lượng điểm dữ liệu lọc được  
- Biểu đồ tương tác (Plotly) hoặc tĩnh (Matplotlib/Seaborn)

---

## 🧰 Xử lý lỗi thường gặp

| Lỗi | Nguyên nhân | Cách khắc phục |
|------|--------------|----------------|
| `st.session_state cannot be modified...` | Streamlit reload trong lúc cập nhật widget | F5 để tải lại trang |
| `Duplicate button ID` | Nút bị trùng `key` | Giữ `key="clear_wards_btn"` duy nhất |
| `Missing file .png` | File tạm bị mất khi reload | Không ảnh hưởng, chỉ là cảnh báo rác |

---

## 💡 Gợi ý mở rộng
- Thêm **nút tải biểu đồ PNG** (`st.download_button`)  
- Thêm **tùy chọn theme/màu sắc**  
- Tích hợp thêm chỉ số khí hậu khác (độ ẩm, lượng mưa, v.v.)  
- Cho phép xuất **báo cáo PDF** từ các biểu đồ

---

## 👨‍💻 Tác giả
Phát triển bởi nhóm nghiên cứu môi trường — Python & Streamlit.

---

## 📜 Giấy phép
MIT License — Tự do sử dụng, sửa đổi và phân phối.
