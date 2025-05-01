# Smart Power Manager

Smart Power Manager là một ứng dụng tự động điều chỉnh chế độ năng lượng của Windows dựa trên hoạt động của người dùng và các tiến trình đang chạy, giúp tối ưu hóa hiệu suất và tiết kiệm pin cho máy tính.

## Tính năng

- **Chuyển sang chế độ Hiệu suất cao (High Performance)** khi phát hiện các ứng dụng nặng đang chạy (trò chơi, trình biên tập video, trình duyệt web,...)
- **Chuyển sang chế độ Tiết kiệm pin (Power Saver)** khi người dùng không hoạt động trong một khoảng thời gian có thể cấu hình
- **Quay lại chế độ Cân bằng (Balanced)** trong các trường hợp khác
- **Theo dõi hoạt động thực tế của bàn phím và chuột** để phát hiện chính xác thời gian không hoạt động
- **Hỗ trợ chạy như dịch vụ Windows** để tự động khởi động cùng hệ thống
- **Tùy chỉnh linh hoạt** thông qua file cấu hình settings.ini
- **Thu thập dữ liệu sử dụng tài nguyên** (CPU, RAM, GPU) của hệ thống và ứng dụng
- **Theo dõi thời gian sử dụng ứng dụng** và ghi lại thời lượng sử dụng
- **Ghi lại thay đổi chế độ nguồn** tự động và thủ công

## Yêu cầu hệ thống

- Windows 10 hoặc mới hơn
- Python 3.6 hoặc mới hơn
- Quyền Administrator (để thay đổi chế độ năng lượng)

## Cài đặt

### Cài đặt thông thường (Chạy khi cần)

1. **Cài đặt các gói phụ thuộc:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Cấu hình GUID của các chế độ năng lượng:**

   - Mở Command Prompt (cmd) với quyền Administrator
   - Chạy lệnh `powercfg /list` để xem các chế độ năng lượng có sẵn và GUID của chúng
   - Sao chép các GUID cho chế độ High Performance, Balanced, và Power Saver
   - Mở `config/settings.ini` và thay thế các GUID placeholder bằng GUID đúng cho hệ thống của bạn

3. **Cấu hình tùy chọn (Không bắt buộc):**
   - Điều chỉnh `idle_threshold_seconds` trong phần `[General]` để thay đổi thời gian phải không hoạt động trước khi chuyển sang chế độ Power Saver
   - Thêm tên các ứng dụng nặng vào danh sách `heavy_processes` trong phần `[Processes]` (phân tách bằng dấu phẩy)

### Cài đặt như Dịch vụ Windows (Chạy liên tục, tự động)

1. **Mở Command Prompt (cmd) với quyền Administrator**

2. **Cài đặt các gói phụ thuộc:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Cấu hình GUID và các tùy chọn** như hướng dẫn ở phần trên

4. **Cấu hình chế độ tự động khởi động (nếu muốn):**

   - Trong `config/settings.ini`, thay đổi `enable_autostart = 0` thành `enable_autostart = 1`

5. **Cài đặt và khởi động dịch vụ:**
   ```bash
   python install_service.py
   ```
   Script này sẽ tự động cài đặt dịch vụ Windows và cấu hình nó theo các thiết lập trong file settings.ini.

## Sử dụng

### Chạy thông thường

```bash
python main.py
```

Chương trình sẽ chạy ở foreground, ghi log các hành động của nó vào console. Nhấn `Ctrl+C` để dừng.

### Quản lý Dịch vụ Windows

**Kiểm tra trạng thái dịch vụ:**

```bash
sc query SmartPowerManager
```

**Khởi động dịch vụ:**

```bash
sc start SmartPowerManager
```

**Dừng dịch vụ:**

```bash
sc stop SmartPowerManager
```

**Gỡ cài đặt dịch vụ:**

```bash
python windows_service.py remove
```

## Cách hoạt động

Smart Power Manager hoạt động bằng cách:

1. **Giám sát hoạt động người dùng** thông qua các sự kiện bàn phím và chuột
2. **Quét các tiến trình hệ thống** để phát hiện các ứng dụng nặng đã cấu hình
3. **Áp dụng luật ưu tiên** để chọn chế độ năng lượng:
   - Nếu phát hiện ứng dụng nặng → **High Performance**
   - Nếu người dùng không hoạt động → **Power Saver**
   - Nếu không có điều kiện nào ở trên → **Balanced**

## Xử lý sự cố

- **Lỗi "Invalid or placeholder GUID":** Đảm bảo rằng bạn đã cài đặt đúng GUID cho ba chế độ năng lượng trong file settings.ini
- **Chương trình không thay đổi chế độ năng lượng:** Đảm bảo rằng bạn đang chạy với quyền Administrator
- **Lỗi không tìm thấy powercfg:** Đảm bảo rằng bạn đang chạy trên Windows và powercfg.exe có trong PATH

## Ghi chú quan trọng

- Để hoạt động tốt nhất, chương trình nên chạy với quyền Administrator
- File log dịch vụ nằm ở `C:\ProgramData\SmartPowerManager\logs\smart_power_service.log`
- Nếu bạn cập nhật file settings.ini, bạn cần khởi động lại dịch vụ để áp dụng thay đổi

## Phát triển thêm

- Bạn có thể mở rộng danh sách `heavy_processes` trong settings.ini với các ứng dụng riêng của bạn
- File debug_log.txt được tạo ra trong thư mục chạy chương trình và có thể hữu ích khi gỡ lỗi
- Sửa đổi giá trị `check_interval_seconds` để thay đổi tần suất kiểm tra trạng thái hệ thống
