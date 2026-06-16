# Báo cáo thực hành Lab 14: AI Evaluation Benchmarking

## 1. Thông tin cá nhân
- **Họ và Tên:** Nguyễn Hoàng Thanh Tùng
- **Mã sinh viên:** 2A202600846
- **Mục tiêu:** Thực hiện Lab cá nhân để rèn luyện và thử nghiệm năng lực xây dựng/debug hệ thống AI Evaluation Benchmarking.

## 2. Các công việc đã hoàn thành & Bài học rút ra
1. **Thiết kế E2E Pipeline Đa Mô Hình (Multi-Model):** Tích hợp thành công nhiều model Qwen khác nhau (`qwen-flash`, `qwen-plus-2025-07-14`, v.v.) vào từng Agent riêng biệt (SDG, Agent V1, Agent V2, Strict Judge, Semantic Judge).
2. **Nâng cấp Synthetic Data Generator:** Cấu hình lại LLM để tạo ra 59 test cases hóc búa, vượt mốc 50 cases yêu cầu của bài Lab.
3. **Debug & Tối ưu Hệ thống Giám khảo (LLM Judge):** Viết lại Regex Parser để bóc tách chính xác điểm số từ LLM (vượt qua lỗi LLM trả về các thẻ Markdown dư thừa, tránh điểm 0.0 oan uổng).
4. **Xử lý triệt để lỗi API 429 Rate Limit:** Triển khai cơ chế _Exponential Backoff_ (tự động sleep và thử lại) trong `llm_client.py` và giảm concurrency batch size, giúp pipeline chạy ổn định liên tục trên DashScope mà không bị ngắt kết nối.
5. **Đánh bại Baseline:** Hệ thống V2 hoàn thiện đạt điểm số 4.51/5.0 (so với V1 là 1.10), hoàn thành xuất sắc Release Gate.

## 3. So sánh kết quả Agent V1 và V2

Dưới đây là minh chứng kết quả chạy E2E Benchmark thực tế, cho thấy sự cải thiện hiệu suất rõ rệt từ bản V1 (Baseline) lên bản V2 (Optimized):

![Kết quả Regression Summary](Screenshot%202026-06-16%20222421.png)

Kết quả chi tiết:
```text
--- Regression Summary ---
V1 avg score: 1.10
V2 avg score: 4.51
Delta: +3.41
Release gate: APPROVE
```

## 4. Cấu trúc dự án

```text
agent/main_agent.py              Agent/RAG logic
data/synthetic_gen.py            Sinh golden dataset (59 cases)
data/HARD_CASES_GUIDE.md         Hướng dẫn hard cases
engine/retrieval_eval.py         Retrieval metrics
engine/llm_judge.py              Multi-judge consensus (Strict & Semantic)
engine/runner.py                 Benchmark runner
engine/llm_client.py             Kết nối DashScope API (Hỗ trợ chống Rate Limit)
analysis/failure_analysis.md     Phân tích lỗi và 5 Whys
run_e2e.py                       Entry point E2E benchmark 
main.py                          Entry point benchmark nội bộ
check_lab.py                     Validator chấm điểm
```

## 5. Hướng dẫn chạy thử nghiệm

Yêu cầu: Đã cấu hình `.env` với các API Key của DashScope.

**Khởi chạy môi trường và cài đặt:**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Sinh bộ dữ liệu vàng (Golden Dataset):**
```powershell
python data\synthetic_gen.py
```

**Chạy toàn bộ quá trình E2E Benchmark:**
```powershell
# Sử dụng UTF-8 để tránh lỗi font chữ hiển thị trên Windows
$OutputEncoding = [System.Text.Encoding]::UTF8; [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; $env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe run_e2e.py
```
