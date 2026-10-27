# Note

## Cần làm

### Kiểm tra chất lượng (tiếp)
- [ ] `area`, `kitchen_area` bất thường; `kitchen_area >= area`
- [ ] `level > levels`
- [ ] `building_type` trong 0–5, `object_type` chỉ 1/11
- [ ] Tách `price = 0` và `price < 0`

### 02_cleaning
- [ ] Bỏ dòng trùng
- [ ] Xử lý `price` lỗi, `area`/`kitchen_area` ngoại lai, `rooms = -2`
- [ ] `price` (**phương án chính**): lọc ngoại lai bằng IQR k = 3 trên log(price), giữ khoảng 130.103 – 72.060.321 rúp (loại 0,22%); ngưỡng tính trên tập train
- [ ] `price` (đối chiếu): cắt 0,1% ở mỗi đầu, giữ khoảng P0.1 – P99.9 (hiện là 210.000 – 86.640.285 rúp, loại khoảng 0,2%)
- [ ] Xử lý cụm 2.088 tin ở vịnh Neva
- [ ] Quyết định giữ/bỏ 23.769 tin ngoài biên
- [ ] Lưu parquet

### 03_eda
- [ ] Thống kê mô tả trên dữ liệu sạch
- [ ] Bản đồ giá / giá mỗi m² theo vùng

### 04_feature_engineering
- [ ] `is_studio` (thay `rooms = -1`)
- [ ] `level / levels`, tầng 1, tầng cao nhất
- [ ] `kitchen_area / area`
- [ ] Năm, tháng từ `date`
- [ ] `months_since_start`: tính từ đầu dữ liệu, mốc cố định 2018-02-01 (02/2018 = 0), dùng cùng mốc cho train và test; giữ cả các tháng 02–08/2018
- [ ] `region` → StringIndexer + OneHot
- [ ] `price_per_m2 = price / area`: dùng cho EDA, cắt ngoại lai hoặc làm biến mục tiêu thay thế; không dùng làm đặc trưng đầu vào khi dự đoán `price` (rò rỉ mục tiêu)
- [ ] `is_moscow_or_spb`: 1 nếu thuộc thành phố Moscow hoặc Saint Petersburg (không gồm hai tỉnh xung quanh); không dùng chung với `region` one-hot trong mô hình tuyến tính (đa cộng tuyến hoàn hảo)

### 05_modeling
- [ ] So sánh mô hình tuyến tính và mô hình cây
- [ ] Ablation: có / không `region`
- [ ] Feature importance
- [ ] Khả năng mở rộng (thời gian chạy theo kích thước dữ liệu)

### Báo cáo
- [ ] Ghi giả định đơn vị m²
- [ ] Ghi ranh giới bản đồ dùng (Natural Earth, Crimea tính theo thực tế quản lý)
- [ ] Ghi tên vùng suy từ tọa độ, không phải bảng mã chính thức
