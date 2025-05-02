# Smart Power Manager

Smart Power Manager là một ứng dụng tự động điều chỉnh chế độ năng lượng của Windows dựa trên hoạt động của người dùng và các tiến trình đang chạy, giúp tối ưu hóa hiệu suất và tiết kiệm pin cho máy tính.

## Tính năng

- **Chuyển sang chế độ Hiệu suất cao (High Performance)** khi phát hiện các ứng dụng nặng đang chạy
- **Chế độ Turbo** cho các ứng dụng đặc biệt được cấu hình trong nhóm turbo
- **Chuyển sang chế độ Tiết kiệm pin (Power Saver)** khi người dùng không hoạt động
- **Quay lại chế độ Cân bằng (Balanced)** trong các trường hợp thông thường
- **Theo dõi hoạt động thực tế** của bàn phím và chuột để phát hiện chính xác thời gian không hoạt động
- **Hỗ trợ chạy như dịch vụ Windows** để tự động khởi động cùng hệ thống
- **Ghi log chi tiết** vào thư mục logs để theo dõi hoạt động của ứng dụng
- **Tùy chỉnh linh hoạt** thông qua file cấu hình settings.ini

## Yêu cầu hệ thống

- Windows 10 hoặc mới hơn
- Python 3.6 hoặc mới hơn
- Quyền Administrator (để thay đổi chế độ năng lượng)

## Cài đặt

### Cài đặt thông thường

1. **Cài đặt các gói phụ thuộc:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Cấu hình GUID của các chế độ năng lượng:**
   - Mở Command Prompt (cmd) với quyền Administrator
   - Chạy lệnh `powercfg /list` để xem các GUID
   - Cập nhật các GUID trong `config/settings.ini`

3. **Cấu hình tùy chọn:**
   - `[General]`
     - `idle_threshold_seconds`: Thời gian không hoạt động trước khi chuyển sang Power Saver
     - `check_interval_seconds`: Tần suất kiểm tra trạng thái hệ thống
     - `enable_debug_logging`: Bật/tắt log chi tiết
   - `[PowerPlans]`
     - Cập nhật GUID cho các chế độ nguồn
     - `turbo_guid`: GUID tùy chọn cho chế độ turbo
   - `[Processes]`
     - `heavy_processes`: Danh sách các ứng dụng nặng
   - `[TurboMode]`
     - Cấu hình các nhóm ứng dụng cho chế độ turbo

### Cài đặt như Dịch vụ Windows

1. Thực hiện các bước cài đặt thông thường ở trên
2. Chạy với quyền Administrator:
   ```bash
   python install_service.py
   ```

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

Smart Power Manager hoạt động theo thứ tự ưu tiên:

1. **Chế độ Turbo** (Cao nhất)
   - Kích hoạt khi phát hiện ứng dụng trong nhóm turbo đang chạy
   - Sử dụng GUID riêng cho hiệu suất tối đa

2. **Chế độ Hiệu suất cao**
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
- Log của dịch vụ Windows: `C:\ProgramData\SmartPowerManager\logs\smart_power_service.log`
- Xem log để theo dõi:
  - Thay đổi chế độ nguồn
  - Phát hiện ứng dụng nặng/turbo
  - Thời gian không hoạt động
  - Lỗi và cảnh báo

## Xử lý sự cố

- **Không có quyền thay đổi nguồn:** Chạy với quyền Administrator
- **GUID không hợp lệ:** Kiểm tra lại `powercfg /list` và cập nhật settings.ini
- **Dịch vụ không khởi động:** Kiểm tra Windows Event Log để xem lỗi chi tiết
- **Không nhận diện ứng dụng:** Kiểm tra tên process trong Task Manager

## Ghi chú quan trọng

- Khởi động lại dịch vụ sau khi thay đổi settings.ini
- Backup settings.ini trước khi chỉnh sửa
- Kiểm tra log thường xuyên để đảm bảo hoạt động đúng
- File README này được cập nhật lần cuối: 02/05/2025
