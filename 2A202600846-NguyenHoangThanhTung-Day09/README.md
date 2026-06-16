# Báo Cáo Dự Án Cá Nhân: Shopping Assistant Multi-Agent System

**Sinh viên thực hiện:** Nguyễn Hoàng Thanh Tùng  
**Mã số sinh viên:** 2A202600846  

---

## 1. Giới thiệu dự án
Dự án tập trung xây dựng một trợ lý mua sắm thông minh (`shopping assistant`) áp dụng mô hình kiến trúc multi-agent sử dụng framework `LangGraph`. Hệ thống được tích hợp với Mô hình Ngôn ngữ Lớn (LLM), kỹ thuật RAG (Retrieval-Augmented Generation) thực tế, và sử dụng dữ liệu mẫu (mock data) cục bộ để xử lý và giải đáp các thắc mắc của khách hàng.

## 2. Kiến trúc hệ thống
Hệ thống được thiết kế theo mô hình phân tán với nhiều agent chuyên biệt, được điều phối nhịp nhàng:

- **Supervisor Agent**: Đóng vai trò là người quản lý, phân loại câu hỏi của người dùng và điều hướng luồng xử lý đến các worker agent phù hợp.
- **Worker 1 (Policy / RAG Agent)**: Chuyên trách tra cứu và xử lý các câu hỏi liên quan đến chính sách cửa hàng. Agent này sử dụng RAG để tìm kiếm ngữ cảnh chính xác từ knowledge base.
- **Worker 2 (Order / Customer Lookup Agent)**: Nhiệm vụ tra cứu dữ liệu cấu trúc như thông tin khách hàng, chi tiết đơn hàng, và trạng thái voucher từ cơ sở dữ liệu.
- **Worker 3 (Response Agent)**: Tổng hợp thông tin từ các agent phía trên để đưa ra câu trả lời cuối cùng, tự nhiên và đầy đủ nhất cho người dùng.

**Luồng dữ liệu xử lý:**  
User → Supervisor → Policy worker và/hoặc Data worker → Response worker → Final answer

## 3. Công nghệ và Công cụ sử dụng
- **Flow Orchestration**: `LangGraph` để tổ chức và quản lý trạng thái của các agent.
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` dùng để chuyển đổi văn bản chính sách thành vector embeddings.
- **Vector Database**: `Chroma` được sử dụng làm vector store để lưu trữ và truy xuất nhanh các chunk dữ liệu chính sách.
- **LLM Provider**: Hỗ trợ linh hoạt thông qua abstraction (ví dụ: Google Gemini API).

## 4. Các tính năng và Yêu cầu kỹ thuật đã thực hiện
- **Xử lý Dữ liệu (RAG)**: Phân tách (chunk) dữ liệu chính sách một cách có cấu trúc dựa trên cấp độ heading (heading 2, heading 3) để đảm bảo độ chính xác khi truy xuất.
- **Công cụ (Tools)**:
  - Tích hợp 1 tool cho RAG search policy.
  - Tích hợp 3 tools phục vụ tra cứu thông tin (Order, Customer, Voucher).
- **Hỗ trợ đa dạng loại câu hỏi**:
  - Truy vấn về chính sách (ví dụ: "Chính sách đổi trả như thế nào?").
  - Truy vấn về dữ liệu cụ thể (ví dụ: "Tình trạng đơn hàng #123?").
  - Truy vấn kết hợp, đòi hỏi đối chiếu dữ liệu khách hàng với chính sách.
- **Xử lý ngoại lệ**: Xử lý tốt các tình huống cần làm rõ thêm thông tin (`clarification_needed`) hoặc không tìm thấy dữ liệu (`not_found`).

## 5. Hướng dẫn cài đặt và chạy ứng dụng

### 5.1. Cài đặt môi trường
1. Khởi tạo file `.env` tại thư mục gốc với cấu hình tối thiểu:
```bash
LLM_MODEL=gemini-3.1-flash-lite
GOOGLE_API_KEY=your_key_here
```

2. Cài đặt các thư viện phụ thuộc:
```bash
pip install -r src/requirements.txt
```

### 5.2. Chạy ứng dụng
- **Truy vấn một câu hỏi trực tiếp qua CLI:**
```bash
PYTHONPATH=src python -m app.cli --question "Đơn hàng 1971 có được hoàn trả không?"
```

- **Chạy kiểm thử hàng loạt (Batch testing):**
```bash
PYTHONPATH=src python -m app.cli --batch --test-file data/test.json
```
