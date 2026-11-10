# Đầu vào văn bản cho HippoRAG

Mỗi file JSONL tương ứng một PDF nguồn. Mỗi dòng có `content` và `metadata`; UTF-8, Unicode NFC. Đây là dữ liệu đầu vào, chưa chạy OpenIE, embedding hoặc tạo index HippoRAG.

## Nguồn và cách xử lý

- Ngữ âm/Văn tự: dùng bản đọc ưu tiên đã có, không nhập OCR thô song song. Một passage theo trang để giữ ngữ cảnh. Hình giữ vị trí nguồn, không tự đoán ký hiệu hoặc điền bài tập.
- Bộ thủ: chuyển 214 hàng JSON đã đối chiếu thành đoạn mô tả; ký hiệu hàng chưa xác định vẫn giữ trạng thái cần xem ảnh.
- HSK 2025: 11.000 hàng từ vựng được chuyển thành câu có số mục, mặt chữ, pinyin, từ loại và nhãn cấp nguyên bản. Không tự giải nghĩa dấu ngoặc cấp độ hoặc bổ sung nghĩa Việt.
- HSK ngoài bảng từ vựng: giữ văn bản theo trang. Các bảng chủ đề/ngữ pháp cần đối chiếu ô gộp và phân cấp; chưa chuyển hoàn toàn thành câu theo từng ô.
- GF0025-2021: OCR cục bộ bằng RapidOCR; giữ chữ, dòng và tọa độ. Bản OCR này còn cần sửa dấu pinyin, thứ tự cột và lỗi nhận dạng. Không dùng nó như bản hiệu đính. Các block trong `_review/gf0025-2021/` dùng để đối chiếu lại ảnh PDF.

Metadata `document` và `source_image` tính từ thư mục input. `ocr_blocks_path` tính từ thư mục này. `qa_status`/`review_scope` ghi phạm vi chất lượng; số confidence OCR không chứng minh kiến thức đúng.

## Đọc vào API

```python
import json
from pathlib import Path
from hipporag import Chunk

input_dir = Path("hipporag_input")
docs = []
for path in sorted(input_dir.glob("*.jsonl")):
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            docs.append(Chunk(content=row["content"], metadata=row["metadata"]))

# Sau khi rà các mục cần kiểm tra và cấu hình model:
# hipporag.index(docs=docs)
```

Không nhập thư mục `_review` như passage. Không nhập cả hai bản đọc gốc và JSONL cho cùng một nguồn. Khi sửa tài liệu, cần xóa passage cũ hoặc tạo index mới để tránh giữ kiến thức cũ.

## Kiểm kê

| File | Trang nguồn | Passage |
| --- | ---: | ---: |
| ngu-am-bai-01-khai-quat.jsonl | 10 | 10 |
| ngu-am-bai-02-van-mau-va-thanh-dieu.jsonl | 9 | 9 |
| ngu-am-bai-03-thanh-mau.jsonl | 7 | 7 |
| ngu-am-bai-04-thanh-mau.jsonl | 7 | 7 |
| ngu-am-bai-05-cach-phat-am-van-mau-phuc.jsonl | 6 | 6 |
| ngu-am-bai-06-van-mau-mui.jsonl | 9 | 9 |
| ngu-am-bai-07-thanh-nhe-va-quy-tac-viet-phien-am.jsonl | 5 | 5 |
| ngu-am-bai-08-bien-dieu.jsonl | 5 | 5 |
| ngu-am-bai-09-am-uon-luoi-va-tro-tu-ngu-khi-a.jsonl | 7 | 7 |
| ngu-am-bai-10-trong-am-va-ngu-dieu-cua-cau.jsonl | 7 | 7 |
| van-tu-bai-01-qua-trinh-hinh-thanh.jsonl | 8 | 8 |
| van-tu-bai-02-phuong-phap-tao-chu-han.jsonl | 8 | 8 |
| van-tu-bai-03-cac-net-co-ban-cua-chu-han.jsonl | 8 | 8 |
| van-tu-bai-04-quy-tac-but-thuan-cua-chu-han.jsonl | 6 | 6 |
| van-tu-bai-05-phuong-thuc-ket-cau-chu-han-va-bo-thu.jsonl | 6 | 6 |
| van-tu-214-bo-thu.jsonl | 6 | 214 |
| hsk-exam-syllabus-2025.jsonl | 406 | 11131 |
| gf0025-2021.jsonl | 260 | 257 |

## Bổ sung OCR
Đã bỏ ngưỡng lọc confidence 0.5 cho GF và giữ cả kết quả thấp điểm. Các block có needs_review=true cần đối chiếu. Đây không phải xác nhận mọi ký tự đúng; bảng vẫn cần phục hồi hàng/cột. Số passage mới xem manifest.json.

## Đối soát bổ sung
Đã giữ toàn văn ưu tiên và ảnh của 114 trang trong `_review/source_pages`. HSK đã loại watermark theo hướng chữ, giữ chữ đơn thật. Bảng chữ GF được đọc theo ô ở các trang 21–41; các ô chưa chắc có placeholder và bản OCR ứng viên trong file cells. Những chỗ này chưa hoàn tất đối chiếu. Xem `audit_report.json`; không coi số trang hoặc JSON hợp lệ là kiểm chứng đủ nội dung.

## Đối chiếu ảnh cho nhóm ô nghi vấn
Đã kiểm tra bằng ảnh 613 bản ghi: 612 ô chữ được xác nhận/sửa, 1 bản ghi watermark bị loại. Đã đọc lại 30 số thứ tự sửa tự động. Không còn ô chưa đọc trong nhóm này. Phạm vi không bao gồm mọi ký tự OCR và mọi bảng; xem visual_verification.json. Các báo cáo đếm ô nghi vấn trước đó đã được thay bằng kết quả này.
