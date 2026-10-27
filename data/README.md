# data: Russia Real Estate 2018–2021

Folder chứa bộ dữ liệu lớn dùng cho tiểu luận: các tin đăng bán căn hộ trên những trang bất động sản phổ biến ở Nga.

## Cấu trúc thư mục

| Đường dẫn | Nội dung | Tạo bởi |
|---|---|---|
| `raw/russia-real-estate.csv` | Dữ liệu gốc từ Kaggle (tên gốc `all_v2.csv`) | Tải về |
| `raw/russia-real-estate-2021/input_data.csv` | Bộ [Russia Real Estate 2021](https://www.kaggle.com/datasets/mrdaniilak/russia-real-estate-2021) (cùng tác giả, 11.358.150 dòng, phân cách `;`, cấu trúc cột khác bộ gốc) | Tải về |
| `raw/russia-real-estate-2021/russia-real-estate-2021-after-2021-05-01.csv` | Các dòng của bộ 2021 có ngày sau 2021-05-01 (7.800.008 dòng), dùng làm tập test | Lọc theo ngày, giữ nguyên nội dung |
| `raw/region_names.csv` | Mã `region` → tên vùng, tọa độ xuất hiện nhiều nhất, thủ phủ và tọa độ thủ phủ | `region_lookup.py` |
| `clean.parquet` | Dữ liệu đã làm sạch và bổ sung cột | `notebooks/01_load_and_quality_check.ipynb` |
| `train.parquet`, `test.parquet` | Tập train (từ `clean.parquet`) và tập test (bộ 2021 sau 2021-05-01) đã đổi cùng cấu trúc, cắt ngoại lai `price` theo ngưỡng của train và thêm đặc trưng | `notebooks/03_preprocessing.ipynb` |
| `train_model.parquet`, `test_model.parquet` | Dữ liệu đưa vào mô hình: `price` và 16 đặc trưng; `building_type` mã hóa one-hot (bỏ Panel làm tham chiếu), Unknown ở tập test được điền bằng mode của tập train theo nhóm | `notebooks/03_preprocessing.ipynb` (mục 8) |

Thứ tự chạy khi tạo lại từ đầu: `python region_lookup.py`, sau đó notebook 01 (notebook cần `region_names.csv`), rồi notebook 03.

Các mục bên dưới mô tả file gốc `raw/russia-real-estate.csv`.

## Thông tin nhanh

| Mục | Giá trị |
|---|---|
| Nội dung | Mỗi dòng là một tin đăng bán căn hộ |
| Số dòng | 5.477.006 |
| Số cột | 13 |
| Khóa chính | Không có cột định danh; có 1.523 dòng trùng hoàn toàn |
| Khoảng thời gian | 19/02/2018 đến 01/05/2021 (theo `date`) |

## Nguồn dữ liệu

[Kaggle: Russia Real Estate 2018-2021 (mrdaniilak)](https://www.kaggle.com/datasets/mrdaniilak/russia-real-estate-20182021), tác giả Daniilak, phiên bản 3 ngày 14/05/2021, giấy phép GNU AGPL 3.0.

## Ý nghĩa các cột

Không cột nào có giá trị thiếu. Cột "Giá trị thực tế" thống kê trực tiếp từ file.

| Nhóm | Cột | Kiểu | Giá trị thực tế | Ghi chú |
|---|---|---|---|---|
| Giá | `price` | số nguyên | trung vị 2.990.000; 1% đến 99%: 750.000 đến 24.100.000 | Giá bán, đơn vị rúp |
| Thời gian | `date` | chuỗi | 2018-02-19 đến 2021-05-01 | Ngày đăng tin, định dạng `YYYY-MM-DD` |
| | `time` | chuỗi | 86.400 giá trị | Giờ đăng tin `HH:MM:SS`, không ghi múi giờ |
| Vị trí | `geo_lat`, `geo_lon` | số thực | vĩ độ 41,5 đến 72,0; kinh độ 19,9 đến 162,5 | Tọa độ; tất cả nằm trong khung tọa độ của nước Nga |
| | `region` | số nguyên | 84 mã, từ 3 đến 61.888 | Mã vùng **không theo** số hiệu chính thức 1–85 (ví dụ tọa độ trung vị của mã `2661` ở Saint Petersburg, của mã `9654` ở Novosibirsk) |
| Tòa nhà | `building_type` | số nguyên | 0 đến 5 | Loại tường. Theo Kaggle: 0 khác, 1 panel, 2 bê tông liền khối, 3 gạch, 4 block, 5 gỗ |
| | `levels` | số nguyên | 1 đến 39 | Tổng số tầng của tòa nhà |
| | `object_type` | số nguyên | `1` (3.863.809), `11` (1.613.197) | Loại thị trường: nhà đã qua sử dụng hoặc nhà mới xây |
| Căn hộ | `level` | số nguyên | 1 đến 39 | Tầng của căn hộ |
| | `rooms` | số nguyên | -2, -1, 1 đến 10 | Số phòng ở; `-1` là căn hộ studio, `-2` (343 dòng) không được mô tả |
| | `area` | số thực | trung vị 48 m²; 1% đến 99%: 19,8 đến 138,2 m² | Tổng diện tích |
| | `kitchen_area` | số thực | 0,01 đến 9.999 m² | Diện tích bếp |

## Phân bố theo năm

| Năm | Số tin |
|---|---|
| 2018 (từ 19/02) | 871.581 |
| 2019 | 2.234.260 |
| 2020 | 1.804.057 |
| 2021 (đến 01/05) | 567.108 |

## Giấy phép và trích dẫn

Dữ liệu dùng giấy phép GNU AGPL 3.0. Khi trích dẫn trong tiểu luận, ghi rõ nguồn Kaggle ở trên, tác giả Daniilak và ngày tải.
