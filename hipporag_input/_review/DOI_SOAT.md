# Đối soát nguồn và JSONL

Kết luận: chưa đạt đầy đủ và đúng nội dung. Phủ trang không thay thế kiểm tra từng ô và ký tự.

| File | Trang nguồn | Trang có JSONL | Đoạn trùng | Kết quả nội dung |
|---|---:|---:|---:|---|
| ngu-am-bai-01-khai-quat.jsonl | 10 | 10 | 0 | preferred_text_preserved_images_not_transcribed |
| ngu-am-bai-02-van-mau-va-thanh-dieu.jsonl | 9 | 9 | 0 | preferred_text_preserved_images_not_transcribed |
| ngu-am-bai-03-thanh-mau.jsonl | 7 | 7 | 0 | preferred_text_preserved_images_not_transcribed |
| ngu-am-bai-04-thanh-mau.jsonl | 7 | 7 | 0 | preferred_text_preserved_images_not_transcribed |
| ngu-am-bai-05-cach-phat-am-van-mau-phuc.jsonl | 6 | 6 | 0 | preferred_text_preserved_images_not_transcribed |
| ngu-am-bai-06-van-mau-mui.jsonl | 9 | 9 | 0 | preferred_text_preserved_images_not_transcribed |
| ngu-am-bai-07-thanh-nhe-va-quy-tac-viet-phien-am.jsonl | 5 | 5 | 0 | preferred_text_preserved_images_not_transcribed |
| ngu-am-bai-08-bien-dieu.jsonl | 5 | 5 | 0 | preferred_text_preserved_images_not_transcribed |
| ngu-am-bai-09-am-uon-luoi-va-tro-tu-ngu-khi-a.jsonl | 7 | 7 | 0 | preferred_text_preserved_images_not_transcribed |
| ngu-am-bai-10-trong-am-va-ngu-dieu-cua-cau.jsonl | 7 | 7 | 0 | preferred_text_preserved_images_not_transcribed |
| van-tu-bai-01-qua-trinh-hinh-thanh.jsonl | 8 | 8 | 0 | preferred_text_preserved_images_not_transcribed |
| van-tu-bai-02-phuong-phap-tao-chu-han.jsonl | 8 | 8 | 0 | preferred_text_preserved_images_not_transcribed |
| van-tu-bai-03-cac-net-co-ban-cua-chu-han.jsonl | 8 | 8 | 0 | preferred_text_preserved_images_not_transcribed |
| van-tu-bai-04-quy-tac-but-thuan-cua-chu-han.jsonl | 6 | 6 | 0 | preferred_text_preserved_images_not_transcribed |
| van-tu-bai-05-phuong-thuc-ket-cau-chu-han-va-bo-thu.jsonl | 6 | 6 | 0 | preferred_text_preserved_images_not_transcribed |
| van-tu-214-bo-thu.jsonl | 6 | 6 | 0 | preferred_text_preserved_images_not_transcribed |
| hsk-exam-syllabus-2025.jsonl | 406 | 406 | 0 | not_fully_verified |
| gf0025-2021.jsonl | 260 | 260 | 0 | FAIL_unresolved_ocr_and_table_alignment |

## Phát hiện
- Hai bộ Ngữ âm/Văn tự: kiểm tra tính nguyên vẹn bản đọc ưu tiên lưu trong _review/source_pages; chưa chứng nhận OCR hoặc hình được chép đúng toàn bộ.
- HSK: kiểm tra chuỗi số mục từ 1–11.000; chưa xác nhận mọi ô pinyin/từ loại và phân cấp bảng.
- GF: còn ô không rõ và xung đột số thứ tự; file chưa đủ điều kiện coi là bản trích hoàn chỉnh.
- Không sửa hoặc tự điền ô trong lần đối soát này. Báo cáo JSON có chi tiết từng trang bảng GF.
