# Tiêu chí chấm điểm của Validator - Eastworld Subnet 94

## Cấu trúc tính điểm tổng thể

```
Weighted Score = 0.3 × Action Score + 0.7 × Quest Score
```

## I. Action Score (30% tổng điểm)

Action Score là phần thưởng nhỏ, thường xuyên được cấp cho từng hành động hợp lệ riêng lẻ.

### Tiêu chí đánh giá hành động

1. **Tính hợp lệ của hành động**
   - Hành động phải tuân theo định dạng trong `action_space`
   - Tham số phải đầy đủ và đúng kiểu dữ liệu
   - Hành động phải thực hiện được trong ngữ cảnh hiện tại

2. **Tính hiệu quả của hành động**
   - Hành động đóng góp vào mục tiêu tổng thể
   - Hành động không lặp lại không cần thiết
   - Thời gian thực hiện hành động nằm trong ngưỡng cho phép

3. **Tính thích ứng của hành động**
   - Điều chỉnh hành động dựa trên phản hồi môi trường
   - Không lặp lại hành động thất bại
   - Xử lý ngoại lệ và tình huống bất ngờ

4. **Tần suất hoạt động**
   - Duy trì hoạt động liên tục
   - Phản hồi kịp thời đến các yêu cầu của validator
   - Giảm thiểu thời gian ngừng hoạt động

### Điểm trừ Action Score

1. **Hành động không hợp lệ**
   - Sử dụng hành động không có trong `action_space`
   - Tham số sai hoặc thiếu
   - Định dạng JSON không chính xác

2. **Suy giảm theo thời gian**
   - Áp dụng khấu trừ hàng giờ cố định
   - Ngừng hoạt động dẫn đến mất điểm đáng kể
   - Cần 24 giờ để phục hồi sau 2 giờ ngừng hoạt động

## II. Quest Score (70% tổng điểm)

Quest Score là phần thưởng lớn hơn, được trao cho việc hoàn thành chuỗi hành động và phản ánh chất lượng lập kế hoạch chiến lược.

### Tiêu chí đánh giá nhiệm vụ

1. **Hoàn thành nhiệm vụ**
   - Đạt được mục tiêu đã đặt ra
   - Tuân thủ các điều kiện và yêu cầu của nhiệm vụ
   - Hoàn thành trong khung thời gian hợp lý

2. **Chiến lược và kế hoạch**
   - Lập kế hoạch hiệu quả để đạt mục tiêu
   - Ưu tiên nhiệm vụ có giá trị cao
   - Tối ưu hóa chuỗi hành động

3. **Tương tác và khám phá**
   - Tương tác với NPC để tiến hành nhiệm vụ
   - Khám phá môi trường một cách có hệ thống
   - Thu thập và sử dụng thông tin môi trường

4. **Quản lý tài nguyên**
   - Thu thập và quản lý vật phẩm
   - Sử dụng tài nguyên hiệu quả
   - Duy trì trạng thái tài nguyên tối ưu

### Điểm trừ Quest Score

1. **Nhiệm vụ không hoàn thành**
   - Không đạt được mục tiêu của nhiệm vụ
   - Thất bại trong các bước quan trọng
   - Bỏ lỡ thời hạn hoàn thành

2. **Suy giảm theo thời gian**
   - Áp dụng suy giảm hàm mũ hàng giờ
   - Nhiệm vụ cũ mất giá trị nhanh chóng nếu không có nhiệm vụ mới
   - Cần thường xuyên hoàn thành nhiệm vụ mới để duy trì điểm số

## III. Kỹ thuật triển khai

### Đánh giá hệ thống bộ nhớ

1. **Lưu trữ thông tin**
   - Bảo tồn thông tin nhiệm vụ
   - Ghi nhớ địa điểm và đối tượng quan trọng
   - Duy trì nhật ký hành động

2. **Khả năng phục hồi**
   - Phục hồi sau sự cố
   - Duy trì thông tin qua các lần khởi động lại
   - Xử lý lỗi hệ thống

### Đánh giá khả năng định vị và lập bản đồ (SLAM)

1. **Xây dựng bản đồ**
   - Tạo và duy trì bản đồ môi trường
   - Đánh dấu địa điểm quan trọng
   - Cập nhật bản đồ khi khám phá vùng mới

2. **Định vị và điều hướng**
   - Định vị chính xác trong môi trường
   - Lập kế hoạch đường đi tối ưu
   - Tránh chướng ngại vật và khu vực nguy hiểm

### Đánh giá xử lý tín hiệu cảm biến

1. **Dữ liệu LiDAR**
   - Phân tích chính xác dữ liệu khoảng cách
   - Nhận diện chướng ngại vật
   - Tối ưu hóa quyết định di chuyển

2. **Cảm nhận môi trường**
   - Trích xuất thông tin từ mô tả văn bản
   - Nhận diện đối tượng và thực thể
   - Phân tích tương tác môi trường

## IV. Yêu cầu kỹ thuật và vận hành

### Yêu cầu về thời gian phản hồi

1. **Độ trễ phản hồi**
   - Phản hồi trong thời gian cho phép
   - Xử lý nhanh chóng các yêu cầu
   - Tối ưu hóa thời gian tính toán

2. **Tính ổn định**
   - Duy trì hoạt động liên tục
   - Giảm thiểu lỗi và sự cố
   - Phục hồi nhanh sau khi gặp vấn đề

### Yêu cầu về mô hình và AI

1. **Chất lượng quyết định**
   - Sử dụng mô hình LLM phù hợp
   - Đưa ra quyết định hợp lý và thông minh
   - Khả năng học hỏi và thích ứng

2. **Tối ưu hóa tài nguyên**
   - Sử dụng tài nguyên máy tính hiệu quả
   - Tối ưu hóa các lời gọi API
   - Quản lý bộ nhớ và CPU/GPU

## V. Hệ thống Bảng xếp hạng

1. **Cập nhật điểm số**
   - Điểm số được cập nhật thông qua API Leaderboard
   - Validator cập nhật điểm số mỗi 30 bước
   - Điểm số được tính trung bình động theo thời gian

2. **Xử lý ngoại lệ**
   - Xử lý các giá trị NaN trong điểm số
   - Đảm bảo tính nhất quán của dữ liệu
   - Phát hiện và báo cáo các vấn đề điểm số

---

*Lưu ý: Tiêu chí này có thể thay đổi khi Eastworld Subnet tiếp tục phát triển và tối ưu hóa hệ thống chấm điểm.* 