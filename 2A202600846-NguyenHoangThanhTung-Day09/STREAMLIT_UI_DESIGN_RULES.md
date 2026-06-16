# Design Rules UI Streamlit

Áp dụng cho các màn hình Streamlit của project `AI Thổ Địa Mua Sắm`. Mục tiêu là giữ UI giống tinh thần hiện tại: gọn, sáng, dễ debug, nhấn mạnh luồng multi-agent realtime và trải nghiệm chat.

## 1. Tinh thần giao diện

- UI là công cụ vận hành/debug multi-agent, không phải landing page marketing.
- Ưu tiên bố cục rõ, mật độ thông tin vừa phải, thao tác nhanh.
- Giữ tone tiếng Việt thân thiện, trực tiếp, có ngữ cảnh mua sắm.
- Trạng thái hệ thống phải nhìn được ngay: agent nào đang chạy, dữ liệu nào được gọi, câu trả lời cuối nằm ở đâu.

## 2. Layout tổng thể

- Luôn dùng `st.set_page_config(..., layout="wide")`.
- Màn hình chính chia 2 cột cân bằng:
  - Cột trái: tiêu đề, workflow multi-agent realtime, tiện ích, câu hỏi mẫu.
  - Cột phải: lịch sử chat và input.
- Tỉ lệ mặc định: `st.columns([1, 1], gap="large")`.
- Không tạo hero lớn hoặc section trang trí. Nội dung chính phải xuất hiện ngay trong viewport đầu.
- Các khối phụ bên cột trái có thể chia 2 cột nhỏ để tiết kiệm chiều cao.

## 3. Header

- Header nhỏ gọn, nằm đầu cột trái.
- H2 khoảng `1.8rem`, font-weight `700`, màu `#111`.
- Mô tả phụ khoảng `0.95rem`, màu `#666`.
- Header nên nêu rõ vai trò app, ví dụ: trợ lý mua sắm multi-agent.

## 4. Màu sắc

Nền và khung:

- Nền chính: trắng hoặc gần trắng.
- Workflow container: `#fcfcfc`.
- Viền container: `#eaeaea`.
- Viền card: `#dcdcdc`.
- Text chính: `#111` hoặc `#333`.
- Text phụ: `#666` hoặc `#777`.

Màu trạng thái agent:

- Supervisor: xanh dương `#00aaff`, nền active `#e6f7ff`, text `#005580`.
- Policy Worker: cam `#ff9900`, nền active `#fff4e6`, text `#804d00`.
- Data Worker: xanh lá `#00cc66`, nền active `#e6fff2`, text `#006633`.
- Response Worker: tím `#9933ff`, nền active `#f2e6ff`, text `#4d0099`.

Không dùng một palette đơn sắc cho toàn app. Màu chỉ nên dùng để phân biệt trạng thái agent, không phủ toàn bộ giao diện.

## 5. Card và container

- Card worker dùng nền trắng, viền xám, bo góc `12px`, padding `15px 20px`.
- Shadow nhẹ: `0 3px 6px rgba(0,0,0,0.06)`.
- Card cần có kích thước tối thiểu, ví dụ `min-width: 150px`, để workflow không nhảy layout.
- Button bo góc `8px`, full width trong khu vực câu hỏi mẫu/tiện ích.
- Không lồng card trong card. Chỉ dùng card cho worker, item lặp, hoặc vùng debug có biên rõ.

## 6. Workflow realtime

- Workflow là điểm nhận diện chính của project, phải xuất hiện gần đầu cột trái.
- Cấu trúc luồng:
  - Supervisor
  - Nhánh song song Policy Worker và Data Worker
  - Response Worker
- Dùng mũi tên đơn giản giữa các bước để giữ flow dễ đọc.
- Mỗi worker cần có:
  - Icon/emoji nhất quán.
  - Tên agent rõ ràng.
  - Một dòng mô tả ngắn.
- Khi agent đang chạy hoặc vừa được dùng, bật class active tương ứng.
- Animation pulse nên nhẹ, chu kỳ khoảng `1.5s`, không làm người dùng mất tập trung.

## 7. Chat experience

- Chat là vùng làm việc chính ở cột phải.
- Dùng `st.chat_message` cho lịch sử và `st.chat_input` cho nhập liệu.
- Chiều cao chat container mặc định khoảng `650px`.
- Khi chưa có hội thoại, dùng `st.info` để hướng dẫn ngắn gọn.
- Khi xử lý, hiển thị trạng thái ngắn như `Đang suy nghĩ...`.
- Sau khi trả lời xong, cập nhật workflow về các node đã được sử dụng để người dùng nhìn lại đường đi của câu hỏi.

## 8. Debug trace

- Debug là tính năng first-class, nhưng không được làm rối chat mặc định.
- Dùng toggle `Bật Debug` ở cột trái.
- Khi bật debug, mỗi câu trả lời assistant có expander `Xem Trace chi tiết`.
- Trace nên có 2 tab:
  - Visual Trace: mô tả từng node bằng ngôn ngữ dễ đọc.
  - Raw JSON State: hiển thị state gốc bằng `st.json`.
- Với dữ liệu dài, dùng `st.expander`, `st.code`, `st.json`, không đổ toàn bộ vào màn hình chính.

## 9. Tiện ích và câu hỏi mẫu

- Tiện ích đặt ở cột trái, dưới workflow.
- Toggle dùng cho lựa chọn nhị phân như fallback/debug.
- Nút làm mới trò chuyện dùng `type="primary"`.
- Câu hỏi mẫu đặt trong container có chiều cao cố định khoảng `250px`, có border.
- Mỗi câu hỏi mẫu là một button full width. Khi bấm, đẩy nội dung vào input/session state và xử lý như user prompt.

## 10. Nội dung hiển thị

- Text UI dùng tiếng Việt nhất quán.
- Label ngắn, rõ hành động: `Bật Debug`, `Dùng Fallback`, `Làm mới trò chuyện`.
- Mô tả agent không quá một dòng nếu có thể.
- Tránh giải thích dài trong UI. Chi tiết kỹ thuật đưa vào expander/debug.
- Với câu trả lời cuối, khi tắt debug cần làm sạch các prefix kỹ thuật như `Status:`, `Answer:`, `Evidence:`.

## 11. CSS và code Streamlit

- Custom CSS nên gom ở đầu file sau `set_page_config`.
- Tên class theo vai trò UI: `main-header`, `workflow-container`, `worker-card`, `glow-supervisor`.
- Không hardcode CSS rải rác trong nhiều block nếu cùng một màn hình.
- Dùng `st.cache_resource` cho object nặng như assistant/graph.
- Dùng `st.session_state` cho:
  - `messages`
  - prompt từ câu hỏi mẫu
  - trạng thái active/last-used nodes
  - các toggle ảnh hưởng đến render
- Luồng xử lý user input phải cập nhật UI trước, stream graph sau, rồi lưu kết quả vào session.

## 12. Checklist trước khi thêm UI mới

- Màn hình vẫn giữ bố cục wide 2 cột nếu là luồng chat/debug chính.
- Component mới có lý do vận hành rõ ràng, không chỉ để trang trí.
- Màu mới không trùng ý nghĩa với 4 màu agent hiện có.
- Text không bị dài quá trong button/card/container.
- Debug data dài nằm trong expander hoặc tab riêng.
- Workflow không bị thay đổi kích thước khi active/inactive.
- Chat vẫn là vùng nhập và đọc kết quả rõ nhất.
- App chạy được với trạng thái rỗng, trạng thái loading, trạng thái lỗi và trạng thái có lịch sử chat.
