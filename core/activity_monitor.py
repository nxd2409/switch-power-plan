import time
import logging
import threading
from pynput import mouse, keyboard

logger = logging.getLogger(__name__)

class ActivityMonitor:
    def __init__(self, idle_threshold_seconds):
        self.idle_threshold_seconds = idle_threshold_seconds
        self.last_activity_time = time.time()
        self.last_update_time = time.time()
        self.mouse_listener = None
        self.keyboard_listener = None
        self.monitor_lock = threading.Lock()
        self.last_mouse_position = None
        logger.info(f"ActivityMonitor initialized with idle threshold of {idle_threshold_seconds}s")

    def update_activity(self, source="unknown"):
        """
        Updates the last activity timestamp.
        This is called automatically by the mouse/keyboard listeners.
        """
        current_time = time.time()
        with self.monitor_lock:
            # Chỉ cập nhật nếu đã 1 giây kể từ lần cập nhật trước
            if current_time - self.last_update_time >= 1.0:
                self.last_activity_time = current_time
                self.last_update_time = current_time
                logger.debug(f"Activity detected from {source}")

    def get_idle_time(self):
        """Returns the number of seconds since the last activity."""
        with self.monitor_lock:
            idle_duration = time.time() - self.last_activity_time
            logger.debug(f"Current idle time: {idle_duration:.2f} seconds")
            return idle_duration

    def is_user_idle(self):
        """Returns True if the user has been idle longer than the threshold."""
        idle_time = self.get_idle_time()
        is_idle = idle_time > self.idle_threshold_seconds
        
        # Log only when trạng thái idle thay đổi
        if is_idle and not hasattr(self, '_last_idle_state') or \
           hasattr(self, '_last_idle_state') and self._last_idle_state != is_idle:
            if is_idle:
                logger.info(f"User became idle (no activity for {idle_time:.1f}s > {self.idle_threshold_seconds}s threshold)")
            else:
                logger.info(f"User became active (idle time: {idle_time:.1f}s)")
            self._last_idle_state = is_idle
            
        return is_idle

    def _on_mouse_move(self, x, y):
        """Callback for mouse movement."""
        # Chỉ cập nhật nếu chuột di chuyển đủ xa
        if self.last_mouse_position is None:
            self.last_mouse_position = (x, y)
            self.update_activity("mouse_move")
        else:
            old_x, old_y = self.last_mouse_position
            # Tính khoảng cách di chuyển
            distance = ((x - old_x) ** 2 + (y - old_y) ** 2) ** 0.5
            # Chỉ cập nhật nếu di chuyển hơn 5 pixels
            if distance > 5:
                self.last_mouse_position = (x, y)
                self.update_activity("mouse_move")
        return True

    def _on_mouse_click(self, x, y, button, pressed):
        """Callback for mouse clicks."""
        if pressed:  # Only count press, not release
            self.update_activity("mouse_click")
        return True

    def _on_mouse_scroll(self, x, y, dx, dy):
        """Callback for mouse scroll."""
        self.update_activity("mouse_scroll")
        return True

    def _on_key_press(self, key):
        """Callback for keyboard press."""
        self.update_activity("keyboard")
        return True

    def start_monitoring(self):
        """Start monitoring for keyboard and mouse activity."""
        logger.info("Starting keyboard and mouse activity monitoring...")
        
        try:
            # Reset các biến theo dõi
            self.last_activity_time = time.time()
            self.last_update_time = time.time()
            self.last_mouse_position = None
            
            # Đảm bảo dừng các listener cũ
            self.stop_monitoring()
            
            # Start the mouse listener
            self.mouse_listener = mouse.Listener(
                on_move=self._on_mouse_move,
                on_click=self._on_mouse_click,
                on_scroll=self._on_mouse_scroll
            )
            self.mouse_listener.daemon = True
            self.mouse_listener.start()
            logger.debug("Mouse listener started successfully.")
            
            # Start the keyboard listener
            self.keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press
            )
            self.keyboard_listener.daemon = True
            self.keyboard_listener.start()
            logger.debug("Keyboard listener started successfully.")
            
            logger.info("Activity monitoring active - tracking keyboard and mouse input.")
            return True
        except Exception as e:
            logger.error(f"Failed to start activity monitoring: {e}")
            self.stop_monitoring()
            return False

    def stop_monitoring(self):
        """Stop all monitoring activities."""
        logger.info("Stopping keyboard and mouse activity monitoring...")
        
        if self.mouse_listener:
            try:
                self.mouse_listener.stop()
                self.mouse_listener = None
                logger.debug("Mouse listener stopped.")
            except Exception as e:
                logger.error(f"Error stopping mouse listener: {e}")
        
        if self.keyboard_listener:
            try:
                self.keyboard_listener.stop()
                self.keyboard_listener = None
                logger.debug("Keyboard listener stopped.")
            except Exception as e:
                logger.error(f"Error stopping keyboard listener: {e}")
        
        # Reset state
        self.last_activity_time = time.time()
        self.last_update_time = time.time()
        self.last_mouse_position = None