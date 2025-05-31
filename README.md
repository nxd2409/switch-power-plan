# Smart Power Manager
Smart Power Manager là một ứng dụng tự động điều chỉnh power plan của Windows dựa trên hoạt động của người dùng và các tiến trình đang chạy, giúp tối ưu hóa hiệu suất và tiết kiệm pin cho máy tính.

## Yêu cầu hệ thống
- Windows 10 hoặc mới hơn
- Python 3.6 hoặc mới hơn
- Quyền Administrator (để có thể thay đổi được power plan)

## Cài đặt

### Cài đặt thông thường

1. **Cài đặt các gói phụ thuộc:**
   pip install -r requirements.txt

2. **Cấu hình GUID của các power plan:**
   - Mở Command Prompt (cmd) với quyền Administrator
   - Chạy lệnh `powercfg /list` để xem các GUID
   - Cập nhật các GUID trong `config/settings.ini`
   (Mỗi thiết bị sẽ có những power plan có tên khác nhau, tùy chọn phù hợp để thay thế vào trong settings.ini)

3. **Cấu hình tùy chọn:**
   - `[General]`
     - `idle_threshold_seconds`: Thời gian không hoạt động trước khi chuyển sang Power Saver
     - `check_interval_seconds`: Tần suất kiểm tra trạng thái hệ thống
     - `enable_debug_logging`: Bật/tắt log chi tiết
   - `[PowerPlans]`
     - Cập nhật GUID cho các chế độ nguồn
     - `turbo_guid`: GUID tùy chọn cho chế độ turbo
   - `[Processes]`
     - `heavy_processes`: Danh sách các ứng dụng có thể kích hoạt chế độ performance (nhiều hơn 2 ứng dụng trong danh sách performance kích hoạt thì chế độ turbo sẽ được kích hoạt, nếu không thì chế độ performance sẽ được kích hoạt)
   - `[TurboMode]`
     - `turbo_apps`: Danh sách các ứng dụng có thể kích hoạt chế độ turbo (chỉ cần 1 ứng dụng trong danh sách hoạt động này thì chế độ turbo sẽ được kích hoạt)

## Sử dụng

### Chạy thông thường
- Chạy CMD với quyền Administrator
- Chuyển đến thư mục chính của ứng dụng
- Kích hoạt môi trường python ảo: .venv\Scripts\activate
- Khởi động ứng dụng: python main.py

Chương trình sẽ chạy ở foreground, ghi log các hành động của nó vào console. Nhấn `Ctrl+C` để dừng.

## Cách hoạt động
Smart Power Manager hoạt động theo thứ tự ưu tiên:

1. **Chế độ Turbo** (Cao nhất)
   - Kích hoạt khi phát hiện ứng dụng trong nhóm turbo hoặc nhiều ứng dụng trong nhóm performance đang chạy

2. **Chế độ Performance**
   - Kích hoạt khi có ứng dụng nặng và người dùng đang hoạt động
   - Tối ưu cho hiệu suất

3. **Chế độ Tiết kiệm pin**
   - Kích hoạt khi người dùng không hoạt động trong thời gian quy định
   - Tiết kiệm năng lượng tối đa

4. **Chế độ Cân bằng** (Mặc định)
   - Áp dụng khi không có điều kiện nào ở trên
   - Cân bằng giữa hiệu suất và tiết kiệm pin

## Theo dõi hoạt động
- File log chính được lưu trong thư mục `logs/activity_debug.txt`
- File log chi tiết `debug_logs.txt`
- Xem log để theo dõi:
  - Thay đổi chế độ nguồn
  - Phát hiện ứng dụng đang làm thay đổi power plan
  - Thời gian không hoạt động
  - Lỗi và cảnh báo

## Xử lý sự cố
- **Không có quyền thay đổi power plan:** Chạy với quyền Administrator
- **GUID không hợp lệ:** Kiểm tra lại `powercfg /list` và cập nhật settings.ini
- **Dịch vụ không khởi động:** Kiểm tra Log hoặc Terminal để xem lỗi chi tiết
- **Không nhận diện ứng dụng:** Kiểm tra tên process trong Task Manager

## Ghi chú quan trọng
- Khởi động lại dịch vụ sau khi thay đổi settings.ini
- Backup settings.ini trước khi chỉnh sửa
- Kiểm tra log thường xuyên để đảm bảo hoạt động đúng
- File README này được cập nhật lần cuối: 31/05/2025
