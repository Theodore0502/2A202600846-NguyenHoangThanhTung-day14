# Lab 14 - AI Evaluation Benchmarking

## BÁO CÁO NHÓM VÀ CÁ NHÂN (REPORT TEMPLATE)
*Ghi chú: Điền thông tin vào phần này để nộp báo cáo cho giảng viên.*

## BÁO CÁO CÁ NHÂN (INDIVIDUAL REPORT)

- **Họ và Tên:** Nguyễn Hoàng Thanh Tùng
- **Mã sinh viên:** 2A202600846
- **Mục tiêu:** Thực hiện Lab cá nhân để rèn luyện và thử nghiệm năng lực xây dựng/debug hệ thống AI Evaluation Benchmarking.

### 🏆 Các công việc đã hoàn thành & Bài học rút ra:
1. **Thiết kế E2E Pipeline Đa Mô Hình (Multi-Model):** Tích hợp thành công nhiều model Qwen khác nhau (`qwen-flash`, `qwen-plus-2025-07-14`, v.v.) vào từng Agent riêng biệt (SDG, Agent V1, Agent V2, Strict Judge, Semantic Judge).
2. **Nâng cấp Synthetic Data Generator:** Cấu hình lại LLM để tạo ra 59 test cases hóc búa, vượt mốc 50 cases yêu cầu của bài Lab.
3. **Debug & Tối ưu Hệ thống Giám khảo (LLM Judge):** Viết lại Regex Parser để bóc tách chính xác điểm số từ LLM (vượt qua lỗi LLM trả về các thẻ Markdown dư thừa, tránh điểm 0.0 oan uổng).
4. **Xử lý triệt để lỗi API 429 Rate Limit:** Triển khai cơ chế *Exponential Backoff* (tự động sleep và thử lại) trong `llm_client.py` và giảm concurrency batch size, giúp pipeline chạy ổn định liên tục trên DashScope mà không bị ngắt kết nối.
5. **Đánh bại Baseline:** Hệ thống V2 hoàn thiện đạt điểm số 4.51/5.0 (so với V1 là 1.10), hoàn thành xuất sắc Release Gate.

---

Repository này xây dựng một pipeline đánh giá AI/RAG agent theo các tiêu chí:

- Synthetic golden dataset với hơn 50 test cases.
- Retrieval metrics: Hit Rate, MRR, Precision@k, NDCG.
- Multi-judge consensus: hai bộ judge heuristic độc lập, agreement rate và conflict handling.
- Benchmark runner bất đồng bộ.
- Regression gate so sánh `Agent_V1_Base` và `Agent_V2_Optimized`.
- Report đầu ra phục vụ chấm điểm: `reports/summary.json`, `reports/benchmark_results.json`.

Pipeline hiện chạy được ở chế độ offline/deterministic, không bắt buộc có API key thật.

## 1. Yêu cầu môi trường

- Windows PowerShell.
- Python 3.10+.
- Chạy toàn bộ lệnh từ thư mục project:

```powershell
cd "D:\AI20K\Day 14\Lab14-AI-Evaluation-Benchmarking"
```

Kiểm tra Python:

```powershell
python --version
```

## 2. Tạo virtual environment

```powershell
python -m venv .venv
```

Kích hoạt môi trường:

```powershell
.\.venv\Scripts\Activate.ps1
```

Nếu PowerShell chặn script activation, chạy:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\.venv\Scripts\Activate.ps1
```

## 3. Cài dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Ghi chú: pipeline hiện không cần gọi API thật để chạy benchmark. Nếu package `ragas` không cài được trong môi trường local, benchmark vẫn chạy vì project dùng evaluator nội bộ trong `engine/retrieval_eval.py`.

## 4. Cấu hình `.env`

File `.env` chứa các API Key cho mô hình Qwen từ DashScope (cần có để chạy E2E Benchmark):

```env
SDG_MODEL=qwen-flash
AGENT_V1_MODEL=qwen-flash
AGENT_V2_MODEL=qwen-flash-2025-07-28
JUDGE_STRICT_MODEL=qwen-plus-2025-07-14
JUDGE_SEMANTIC_MODEL=qwen-plus-2025-04-28
# Điền API KEY vào các biến tương ứng...
```

Không commit API key lên GitHub.

## 5. Sinh golden dataset

Chạy trước khi benchmark:

```powershell
python data\synthetic_gen.py
```

Kết quả mong đợi:

```text
Done. Saved 55 cases to data\golden_set.jsonl
```

File được tạo:

```text
data\golden_set.jsonl
```

## 6. Chạy benchmark (End-to-End)

Chạy pipeline E2E (Tự động sinh Data -> Chạy Benchmark -> Xuất Report):

```powershell
# Chạy với UTF-8 encoding để tránh lỗi font chữ trên Windows
$OutputEncoding = [System.Text.Encoding]::UTF8; [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; $env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe run_e2e.py | Tee-Object -FilePath "result.txt"
```

Benchmark sẽ chạy hai phiên bản:

- `Agent_V1_Base`: baseline để đo regression (điểm thường rất thấp ~1.0).
- `Agent_V2_Optimized`: agent đã tối ưu (Mục tiêu >= 4.0).

Kết quả đầu ra được ghi vào:

```text
reports\summary.json
reports\benchmark_results.json
reports\baseline_results.json
```

Ví dụ kết quả đạt chuẩn:

```text
--- Regression Summary ---
V1 avg score: 1.10
V2 avg score: 4.51
Delta: +3.41
Release gate: APPROVE
Reports written to reports
```

## 7. Kiểm tra trước khi nộp

```powershell
python check_lab.py
```

Kết quả mong đợi:

```text
Tổng số cases: 55
Điểm trung bình: 4.95
Đã tìm thấy Retrieval Metrics
Đã tìm thấy Multi-Judge Metrics
Bài lab đã sẵn sàng để chấm điểm!
```

## 8. Quy trình chạy nhanh

Nếu đã có Python và dependency, chạy lần lượt:

```powershell
cd "D:\AI20K\Day 14\Lab14-AI-Evaluation-Benchmarking"
.\.venv\Scripts\Activate.ps1
$OutputEncoding = [System.Text.Encoding]::UTF8; [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; $env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe run_e2e.py | Tee-Object -FilePath "result.txt"
```

## 9. Cấu trúc chính

```text
agent\main_agent.py              Agent/RAG logic
data\synthetic_gen.py            Sinh golden dataset
data\HARD_CASES_GUIDE.md         Hướng dẫn hard cases
engine\retrieval_eval.py         Retrieval metrics
engine\llm_judge.py              Multi-judge consensus
engine\runner.py                 Benchmark runner
engine\llm_client.py             Kết nối DashScope API (Hỗ trợ chống Rate Limit)
analysis\failure_analysis.md     Phân tích lỗi và 5 Whys
run_e2e.py                       Entry point E2E benchmark (Khuyên dùng)
main.py                          Entry point benchmark nội bộ
check_lab.py                     Validator trước khi nộp
```

## 10. Troubleshooting

### Lỗi không chạy được `Activate.ps1`

Chạy:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Sau đó kích hoạt lại:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Thiếu `data\golden_set.jsonl`

Chạy:

```powershell
python data\synthetic_gen.py
```

### Thiếu report trong `reports`

Chạy:

```powershell
python main.py
```

### Lỗi Unicode khi chạy trên Windows console

Project đã cấu hình `check_lab.py` để dùng UTF-8 cho stdout. Nếu terminal vẫn lỗi, chạy:

```powershell
$env:PYTHONUTF8="1"
python check_lab.py
```

## 11. Files cần nộp

- Source code toàn bộ repository.
- `reports\summary.json`
- `reports\benchmark_results.json`
- `analysis\failure_analysis.md`

