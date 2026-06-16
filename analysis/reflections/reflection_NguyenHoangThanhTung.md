# Individual Reflection - Nguyen Hoang Thanh Tung

## 1. What did you learn?
- Hiểu được tầm quan trọng của việc có một "Golden Dataset" để đánh giá độ chính xác của AI Agent. Việc có dữ liệu kiểm thử (synthetic data generation) giúp việc benchmark trở nên deterministic và khách quan hơn.
- Nắm vững các chỉ số đánh giá Retrieval như Hit Rate, MRR, Precision@k, và NDCG. Các chỉ số này giúp đo lường chính xác xem bước tìm kiếm tài liệu (vector search) có hoạt động tốt hay không trước khi xét đến chất lượng câu trả lời.
- Hiểu và ứng dụng được Multi-Judge Consensus Engine. Việc dùng nhiều LLM làm giám khảo (Judge) và tính toán Agreement Rate giúp đánh giá đáng tin cậy hơn, tránh được bias (thiên vị) của một model đơn lẻ.
- Hiểu cách thức thiết lập một Regression Release Gate, giúp tự động ngăn chặn việc deploy các phiên bản AI bị lỗi hoặc có chất lượng đi xuống.

## 2. Challenges & Solutions
- **Thách thức:** Cấu hình và đánh giá các "Hard cases" (như prompt injection, thiếu context, câu hỏi mơ hồ). Ban đầu, Baseline Agent trả lời rất chung chung hoặc thậm chí bị hallucination.
- **Giải pháp:** Cải thiện Prompt cho Optimized Agent (V2). Thêm các policy rõ ràng vào system prompt để bắt buộc mô hình phải từ chối trả lời nếu không có đủ thông tin trong ngữ cảnh (context), và yêu cầu bám sát vào tài liệu được truy xuất.
- **Thách thức:** Quản lý chi phí và thời gian khi chạy đánh giá qua nhiều LLM Judges.
- **Giải pháp:** Áp dụng cơ chế chạy bất đồng bộ (async execution) trong `runner.py`, giúp đánh giá song song nhiều test case, từ đó giảm đáng kể tổng thời gian benchmark.

## 3. Future Improvements
- Bổ sung cơ chế Reranking cho pipeline Retrieval để cải thiện chỉ số Precision@k (giúp đưa tài liệu quan trọng nhất lên vị trí đầu tiên tốt hơn thay vì chỉ dựa vào lexical search).
- Tối ưu hóa chi phí đánh giá bằng cách dùng một mô hình Judge nhỏ/rẻ cho các câu hỏi dễ, và chỉ dùng LLM lớn (như GPT-4o) cho những câu hỏi khó hoặc khi có xung đột điểm số giữa các Judge nhỏ.
- Tích hợp thêm các bộ test cases có tính chất đa ngôn ngữ để kiểm tra khả năng suy luận chéo ngôn ngữ của Agent.
