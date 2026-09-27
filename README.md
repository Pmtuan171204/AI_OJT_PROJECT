# AI OJT Risk

Repo Python dùng cấu trúc src/ojt_ai. Thư mục local giữ tên AI_OJT_PROJECT.
Hiện chạy được xét OJT theo quy tắc, gom lớp và dự báo có điều kiện.
ML trainer/evaluator/predictor mới là khung mở rộng: chưa có model hoặc metrics.

## Cấu trúc và dữ liệu

- configs/: cấu hình model, training và ngưỡng nghiệp vụ. YAML sử dụng cú pháp JSON hợp lệ để đọc bằng thư viện chuẩn.
- data/raw/: curricula.csv và curriculum_courses.csv lấy từ FLM (12 khung, 577 dòng).
- data/synthetic/: student.csv (2.000 sinh viên), student_course_status.csv (96.166 dòng).
- data/synthetic/student_study_plan.csv: 10.666 dòng kế hoạch kỳ 5 cho 2.000 sinh viên, giả định 2027_Spring theo khung, chưa thêm môn học lại.
- tests/fixtures/demo/: bộ dữ liệu nhỏ cho tests, giữ kế hoạch DEMO cũ ở đây.
- data/processed/: dành cho dữ liệu biến đổi trong tương lai; hiện không chứa bản sao CSV. Code đọc trực tiếp raw/synthetic.
- data/backups/: snapshot local, không đồng bộ theo dataset và không đưa vào Git.
- src/ojt_ai/: data, features, rules, ml, services, schemas, utils.
- scripts/: generate_dataset.py, train.py, evaluate.py, predict.py.
- api/: API FastAPI, hiện dùng quy tắc; chưa có xác thực/phân quyền cho vận hành thực tế.
- tests/: unit và integration; notebooks/: thử nghiệm; docker/: cấu hình container.
- models/trained/: model tương lai; models/metadata/: thông tin phiên bản/metrics tương lai.
- output/: kết quả phân tích và báo cáo kiểm tra, được Git bỏ qua.

## Cài đặt

Python 3.10+; nên tạo môi trường ảo trước khi cài thư viện.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Core chỉ dùng thư viện chuẩn. API và HTTP tests cần các extra trong requirements.txt.
.env.example là mẫu cấu hình; ứng dụng đọc biến môi trường của tiến trình, chưa tự tải .env.

## Chạy dataset chính

```powershell
python scripts/generate_dataset.py . --prepare
python scripts/predict.py --data data --evaluation-term 2026_Fall --target-term 2027_Spring
```

2027_Spring chỉ là đợt mục tiêu trong ví dụ, cần chọn theo lịch của trường.
Kế hoạch kỳ 5 dùng CURRICULUM_ASSUMPTION. Dự báo giả định đạt toàn bộ môn trong kế hoạch; các môn trượt từ kỳ trước vẫn còn nếu chưa có kế hoạch học lại.
student.csv và kỳ 0 trong khung đã được loader hỗ trợ.

## Sinh lại trạng thái giả lập

```powershell
python scripts/generate_dataset.py . --dry-run
python scripts/generate_dataset.py . --sync-credits
```

Lệnh --sync-credits thay trạng thái giả lập và tín chỉ, tự backup trước khi sửa.
Sau đó chạy --prepare để kiểm tra dữ liệu, không tạo bản sao. Không chạy generator trên dữ liệu sinh viên thật.
Tín chỉ hiện cộng mọi môn PASSED trong dataset thử nghiệm; cần xác nhận quy tắc công nhận tín chỉ thực tế.
Mã combo/elective là vị trí học phần chưa có lựa chọn cá nhân, không suy ra đã học tất cả môn của combo.

## Kiểm thử và demo

```powershell
python -m unittest discover -s tests -v
python scripts/predict.py --data tests/fixtures/demo --evaluation-term 2026_HK1 --target-term 2026_HK2
```

Nếu chưa cài package, đặt $env:PYTHONPATH='src' khi chạy unittest.
Các script tự tìm src nên có thể chạy trực tiếp từ repo mà không cài package.

## API phát triển

```powershell
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

GET /health báo rõ ML chưa sẵn sàng. POST /prediction nhận evaluation_term và target_term,
đọc dữ liệu từ OJT_DATA_DIR (mặc định data), trả kết quả mode=rules.
Không đặt API chưa có xác thực lên mạng công khai.

## Docker

```powershell
docker build -f docker/Dockerfile -t ai-ojt-risk .
docker run --rm -p 127.0.0.1:8000:8000 -v "${PWD}/data:/app/data:ro" ai-ojt-risk
```

Model training chỉ được triển khai khi có mục tiêu dự báo, nhãn lịch sử và cách chia train/test phù hợp.
Các lệnh train.py và evaluate.py hiện dừng với thông báo chưa triển khai, không xuất model giả.

## Tạo lại kế hoạch kỳ 5

Chạy: python scripts/generate_study_plan.py . --target-term 2027_Spring
Sau đó chạy generate_dataset.py . --prepare để kiểm tra dữ liệu.
Mỗi mã combo là một vị trí học phần; chưa có lựa chọn cá nhân. Không cộng tất cả môn của combo.

Bộ CSV chính gồm 2 bảng trong data/raw và 3 bảng trong data/synthetic. Bản sao CSV cũ trong backups đã nén ZIP; fixtures chỉ dùng kiểm thử. CSV trong output/data_checks là báo cáo đối soát, không phải bản sao dataset.
