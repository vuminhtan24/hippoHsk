# Chạy dữ liệu HSK với HippoRAG

Chạy các lệnh trong thư mục dự án. Dùng Python của `.venv` để tránh Python mặc định khác phiên bản.

## Kiểm tra tại máy

```powershell
.\.venv\Scripts\python.exe run_hsk.py --dry-run
```

Lệnh nạp `.env`, kiểm tra cấu hình và toàn bộ file JSONL ở cấp ngoài cùng, rồi dừng. Không gọi API, tải model hoặc tạo index. Không đọc thư mục `_review`. Khóa không được in ra màn hình. Biến môi trường đã đặt trong terminal được ưu tiên hơn `.env`.

## Thử lập chỉ mục 5 đoạn

```powershell
.\.venv\Scripts\python.exe run_hsk.py --index --file ngu-am-bai-08-bien-dieu.jsonl --limit 5
```

Lệnh này gọi API và có thể phát sinh phí. Index thử mặc định lưu tại `outputs/hsk-deepseek_sample_5`, tách khỏi index đầy đủ.

Với `deepseek-flash`, `deepseek-v4-flash` hoặc `deepseek-v4-pro` tại `api.deepseek.com`, script tự tắt thinking khi trích xuất. Không cần thêm biến `.env`. Tham số thinking được đưa vào khóa cache, nên kết quả cũ dùng thinking không bị nhầm với kết quả mới. Vector embedding đã lưu vẫn được tái sử dụng.

Nếu API trả nội dung rỗng, lớp Chat Completions thử lại tối đa hai lần, chờ 1 rồi 2 giây. Lỗi thiếu usage, refusal, content filter và tool calls không được thử lại theo cơ chế này. Token của mọi phản hồi rỗng được cộng vào thống kê; phản hồi rỗng không được lưu cache. Nếu vẫn lỗi, log hiển thị `finish_reason`, số token suy luận và số lượt gọi. Các lượt gọi lại có thể phát sinh phí.

Nếu lần lập chỉ mục đầu bị ngắt sau khi lưu vector nhưng chưa có graph, chạy lại cùng cấu hình và thêm `--rebuild-graph`:

```powershell
.\.venv\Scripts\python.exe run_hsk.py --index --limit 5 --rebuild-graph
```

Cờ này xây lại graph từ các embedding/OpenIE tương thích đã lưu; không xóa vector hay sửa dữ liệu đầu vào. Sau khi graph hoàn thành, những lần chạy tiếp không cần cờ này.

## Lập chỉ mục toàn bộ

```powershell
.\.venv\Scripts\python.exe run_hsk.py --index
```

Lệnh đọc tất cả 18 file JSONL trong `HIPPO_INPUT_DIR`. Các phần GF chưa đối soát đầy đủ vẫn tồn tại; xem báo cáo trong `hipporag_input/_review` trước khi chọn nhập toàn bộ. Có thể lặp `--file` để chỉ nhập các tài liệu đã chọn. `--workers` mặc định là 2.

## Cấu hình

Script dùng `LLM_MODEL_NAME`, `LLM_BASE_URL`, `LLM_API_KEY_ENV`, `EMBEDDING_MODEL_NAME`, `EMBEDDING_PROVIDER`, `EMBEDDING_BASE_URL`, `EMBEDDING_API_KEY_ENV`, `HIPPO_INPUT_DIR` và `HIPPO_SAVE_DIR` từ `.env`. Giá trị của hai biến `*_API_KEY_ENV` là tên biến chứa khóa, không phải khóa.

Giữ nguyên model, endpoint và thư mục lưu khi tiếp tục một index. Đổi cấu hình model cần thư mục index mới. Chạy lại với nội dung đã sửa không tự xóa passage cũ; cần quản lý xóa hoặc tạo index mới.

Mỗi dòng đầu vào phải có `content` không rỗng và `metadata` dạng object. Nếu nhiều dòng trùng văn bản hoàn toàn, script chỉ index một passage và giữ các hồ sơ nguồn trong `metadata.source_records` để tránh ghi đè metadata.
