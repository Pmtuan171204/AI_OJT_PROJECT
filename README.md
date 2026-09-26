# OJT Risk — Python

Bản đầu tiên cho hệ thống cảnh báo điều kiện OJT. Chạy bằng Python 3.10+,
chưa cần cài thư viện ngoài. Dữ liệu trong `data/sample` hoàn toàn giả lập;
môn OJT_PREP và số tín chỉ chỉ dùng kiểm thử, không phải khung chính thức.

## Chạy

Trên máy Windows hiện tại có thể chạy `./run-demo.ps1`; script dùng Python
trong PATH hoặc runtime Python đi kèm Codex nếu có.

```powershell
python -m ojt_risk --data data/sample --evaluation-term 2026_HK1 --target-term 2026_HK2 --output output/report.json
python -m unittest discover -s tests -v
```

Nếu máy dùng Python Launcher, thay `python` bằng `py -3`.
Kết quả JSON gồm evaluations, recommendations, forecasts và warnings.
Chạy lại cùng dữ liệu tạo cùng kết quả; file đầu ra được ghi đè.

## Đã triển khai

- Import năm CSV UTF-8 (có thể có BOM), đọc theo tên cột, chấp nhận cột bổ sung.
- Kiểm tra cột, khóa trùng, số không hợp lệ và liên kết dữ liệu.
- Xét OJT: ít nhất 70 tín chỉ và tối đa hai môn FAILED.
- Gom môn FAILED của sinh viên chưa đủ điều kiện OJT.
- Đề xuất lớp 18–22: ưu tiên bố trí nhiều sinh viên nhất, sau đó gần 20 nhất.
  Ví dụ 23 sinh viên → một lớp 22 và một người chờ; 40 → hai lớp 20.
- Dự báo cuối kỳ 4 dựa trên kế hoạch kỳ 5 được cung cấp, kiểm tra cả tín chỉ
  và số môn trượt còn lại; thiếu kế hoạch → INSUFFICIENT_DATA.
- Chặn cộng thêm tín chỉ đối với môn đã PASSED.

## Hợp đồng dữ liệu

Tên cột bắt buộc được định nghĩa trong `ojt_risk/engine.py` (SCHEMA).
Mỗi CSV phải có tiêu đề kể cả khi không có dòng dữ liệu.
Khung chương trình và kế hoạch phải được nhà trường xác nhận trước vận hành.

- `students`: một dòng/sinh viên/đợt đánh giá; email có thể trống.
- `curricula`: một dòng/mã khung.
- `curriculum_courses`: một dòng/mã khung/mã môn.
- `student_course_status`: một dòng/sinh viên/đợt/môn; phản ánh trạng thái
  hiện tại và đầy đủ mọi môn FAILED còn tồn tại, không phải lịch sử lần thi.
- `student_study_plan`: một dòng/sinh viên/đợt mục tiêu/môn; phải chứa đầy đủ
  kế hoạch kỳ 5. REGISTERED là kế hoạch cá nhân, CURRICULUM_ASSUMPTION là
  kế hoạch giả định đã chuẩn bị từ khung. Không tự sinh kế hoạch giả định ở bản này.

Trạng thái môn: PASSED, FAILED, IN_PROGRESS, NOT_TAKEN. Chỉ FAILED được đếm.
Việc thiếu một môn trượt trong nguồn không thể tự phát hiện chỉ từ CSV;
nhà cung cấp dữ liệu phải xác nhận tính đầy đủ. Tín chỉ tích lũy lấy từ trường,
không suy ra từ lịch sử chưa đầy đủ. Chạy đánh giá cuối kỳ chỉ sau khi chốt điểm.
Đợt mục tiêu phải được người chạy chọn đúng, không suy luận thứ tự từ tên đợt.
Cùng mã môn được giả định có thể học chung giữa các khung.

## Phần tiếp theo

1. Đối chiếu dữ liệu thật và chính sách với trường, hỗ trợ ánh xạ cột/Excel.
2. Lưu cơ sở dữ liệu, lịch sử import, kết quả và trạng thái phê duyệt.
3. API và phân quyền tích hợp giao diện.
4. AI diễn giải từ kết quả quy tắc, có mẫu nội dung dự phòng.
5. Email: lịch gửi, chống trùng, gửi lại lỗi và môi trường kiểm thử.

Chưa có API, dịch vụ AI hoặc gửi email trong phiên bản này. Không tải dữ liệu
sinh viên thật lên Git; đặt dữ liệu riêng vào `data/private/` (được gitignore).
