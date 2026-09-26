# Quản lý dữ liệu

## Một nơi làm việc chính

Chỉnh sửa các bảng đang phát triển ở data/dataset. Không chỉnh sửa bản backup
và không copy backup đè lên dataset nếu chưa kiểm tra thời điểm, phiên bản và liên kết.
Nội dung bảy file dữ liệu/báo cáo được di chuyển nguyên vẹn trong lần tổ chức này;
checksum trước/sau được lưu tại output/data_checks/folder_migration.json.

## Bản sao lưu

data/backups/student-status-<id>/ chứa những file bị thay thế trong một lần sinh.
Một nhóm backup có thể chỉ chứa student.csv và student_course_status.csv;
đó không phải bản sao toàn bộ năm bảng và không bảo đảm dữ liệu cũ vốn đã đồng nhất.
Khi phục hồi, đối chiếu khóa sinh viên, mã khung, mã môn và học kỳ của các bảng liên quan.
Backup mới tiếp tục được ghi ở data/backups. Không trộn chúng vào dataset hoặc demo.
Các backup có sẵn được giữ nguyên nội dung. Git hiện không theo dõi các file này,
và .gitignore ngăn thêm chúng vào Git trong các thao tác thông thường.

## Trạng thái bộ dữ liệu

- Sinh viên và trạng thái môn là giả lập, chốt cuối kỳ 4/2026_Fall.
- Khung chương trình và danh sách môn lấy từ FLM.
- PASSED: đã đạt; FAILED: chưa đạt; NOT_TAKEN: chưa học ở kỳ sau.
- Đợt dữ liệu đã chốt nên không có IN_PROGRESS.
- Tín chỉ giả lập cộng từ PASSED; cần đối chiếu quy định công nhận tín chỉ của trường.
- Các mã combo/elective là vị trí lựa chọn, chưa phải lựa chọn cá nhân từng sinh viên.
- Kế hoạch học kỳ 5 trong student_study_plan.csv chưa cập nhật cho dataset chính.

## Báo cáo và kiểm thử

output/data_checks lưu summary JSON, bảng đối chiếu tín chỉ trước/sau và nhật ký
di chuyển thư mục. Các báo cáo là kết quả của một lần chạy, không phải dữ liệu đầu vào.
tests/fixtures/demo chứa 3 sinh viên DEMO và khung giả lập nhỏ, chỉ dành cho demo/tests.
Không cập nhật bộ fixture này theo dataset 2.000 sinh viên: hai bộ có mục đích riêng.