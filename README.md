# AI OJT Project

Hệ thống Python xét điều kiện OJT, gom nhóm học lại và dự báo theo kế hoạch học.

## Cấu trúc repo

```text
AI_OJT_PROJECT/
├── ojt_risk/                 # Mã nguồn xử lý nghiệp vụ
├── scripts/                  # Công cụ sinh và chuẩn hóa dữ liệu
├── data/
│   ├── dataset/              # Bộ CSV chính đang xây dựng
│   └── backups/              # Bản chụp cũ, chỉ lưu local, được Git bỏ qua
├── tests/
│   ├── fixtures/demo/        # Bộ CSV nhỏ độc lập để kiểm thử và chạy demo
│   └── test_engine.py
├── docs/                     # Tài liệu dataset, cách sao lưu
├── output/                   # Kết quả chạy, được Git bỏ qua
│   └── data_checks/          # Báo cáo sinh dữ liệu và đối chiếu tín chỉ
├── run-demo.ps1
└── pyproject.toml
```

## Dataset chính

`data/dataset/` là nơi làm việc cho nhóm, gồm:

| File | Hiện trạng |
|---|---|
| student.csv | 2.000 sinh viên giả lập; tín chỉ đã đồng bộ theo môn PASSED |
| curricula.csv | 12 mã khung lấy từ FLM |
| curriculum_courses.csv | 577 dòng môn/nhóm học phần của 12 khung |
| student_course_status.csv | 96.166 trạng thái giả lập cuối kỳ 4 |
| student_study_plan.csv | Còn là mẫu DEMO cũ; chưa tạo kế hoạch cho 2.000 sinh viên |

Không dùng thư mục backups làm dữ liệu đầu vào. Dataset chính chưa sẵn sàng
cho toàn bộ luồng: kế hoạch học còn là mẫu cũ; bộ import hiện đọc `students.csv`
(có s) và chưa chấp nhận kỳ 0 trong khung. Đây là việc tích hợp tiếp theo,
không được coi là đã xử lý khi sắp xếp thư mục.

## Chạy demo và kiểm thử

Demo chạy bộ dữ liệu nhỏ riêng trong tests/fixtures/demo, không phải 2.000 sinh viên.

```powershell
.\run-demo.ps1
python -m unittest discover -s tests -v
python -m ojt_risk --data tests/fixtures/demo --evaluation-term 2026_HK1 --target-term 2026_HK2 --output output/report.json
```

Cần Python 3.10+. Script PowerShell cũng hỗ trợ Python đi kèm Codex nếu có.

## Kiểm tra/sinh trạng thái cho dataset chính

```powershell
python scripts/generate_student_course_status.py . --dry-run
python scripts/generate_student_course_status.py . --sync-credits
```

Lệnh thứ hai sinh lại dữ liệu giả lập và cập nhật tín chỉ; tự sao lưu trước khi sửa.
Báo cáo được ghi ở output/data_checks. Không chạy lệnh này trên dữ liệu thật của trường.

## Backup và Git

Backup là ảnh chụp của các file trước một lần sửa, không phải bản đồng bộ trực tiếp.
Mỗi lần sinh dữ liệu có thư mục backup riêng; file cũ không tự cập nhật theo dataset.
`data/backups/` và `output/` được .gitignore loại khỏi các lần git add thông thường.
Chúng không được push lên GitHub bằng quy trình đó; cần tự sao chép ra nơi khác
nếu muốn có bản dự phòng ngoài máy. Không xóa backup khi chưa xác định còn cần phục hồi.

Chỉ version dữ liệu giả lập/khung chương trình được phép chia sẻ. Nếu có dữ liệu
sinh viên thật, dùng data/private/ (đã được .gitignore bỏ qua).

Chi tiết: [Quản lý dữ liệu](docs/data_management.md).
Chưa tích hợp API, AI diễn giải hoặc gửi email thực tế.