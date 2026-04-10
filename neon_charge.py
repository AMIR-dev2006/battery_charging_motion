import sys
import os
from PyQt6.QtCore import Qt, QTimer, QPointF, QDateTime, QRectF, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath, QRadialGradient
from PyQt6.QtWidgets import QApplication, QMainWindow

def get_linux_battery():
    # قراءة نسبة البطارية مباشرة من جذور نظام لينكس للحصول على دقة مطلقة
    try:
        with open("/sys/class/power_supply/BAT0/capacity", "r") as f:
            return int(f.read().strip())
    except Exception:
        # محاولة قراءة BAT1 في حال كان اسم البطارية مختلفاً
        try:
            with open("/sys/class/power_supply/BAT1/capacity", "r") as f:
                return int(f.read().strip())
        except Exception:
            return 99

class NeonChargeOverlay(QMainWindow):
    def __init__(self):
        super().__init__()

        # --- إعدادات النافذة الشبحية ---
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.showFullScreen()

        # --- متغيرات الحركة ---
        self.total_duration_ms = 3000
        self.start_time = QDateTime.currentMSecsSinceEpoch()
        self.battery_percent = get_linux_battery()
        self.is_running = True
        self.elapsed_ratio = 0.0

        # --- المؤقت ---
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)

    def update_animation(self):
        current_time = QDateTime.currentMSecsSinceEpoch()
        elapsed = current_time - self.start_time

        if elapsed >= self.total_duration_ms:
            # عندما تمر 3 ثواني (3000 ميلي ثانية)
            self.timer.stop()
            QApplication.quit() # إغلاق التطبيق واختفاء التأثير
        else:
            self.elapsed_ratio = elapsed / self.total_duration_ms
        
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        NEON_CYAN = QColor(0, 255, 255, 255)
        GLOW_COLOR = QColor(0, 255, 255, 50)

        scr_width = self.width()
        scr_height = self.height()
        center = QPointF(scr_width / 2.0, scr_height / 2.0)

        easer = QEasingCurve(QEasingCurve.Type.OutQuart)
        smooth_ratio = easer.valueForProgress(self.elapsed_ratio)

        # 1. الخط الذي يدور على الأطراف
        border_progress = (smooth_ratio * 2.0) % 1.0 
        perimeter = (scr_width + scr_height) * 2
        trace_length = perimeter * border_progress

        pen = QPen(NEON_CYAN)
        pen.setWidth(4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        path = QPainterPath()
        path.moveTo(0, 0)
        
        if trace_length < scr_width:
            path.lineTo(trace_length, 0)
        elif trace_length < scr_width + scr_height:
            path.lineTo(scr_width, 0)
            path.lineTo(scr_width, trace_length - scr_width)
        elif trace_length < scr_width * 2 + scr_height:
            path.lineTo(scr_width, 0)
            path.lineTo(scr_width, scr_height)
            path.lineTo(scr_width - (trace_length - scr_width - scr_height), scr_height)
        else:
            path.lineTo(scr_width, 0)
            path.lineTo(scr_width, scr_height)
            path.lineTo(0, scr_height)
            path.lineTo(0, perimeter - trace_length)
        
        glow_pen = QPen(GLOW_COLOR)
        glow_pen.setWidth(10)
        painter.setPen(glow_pen)
        painter.drawPath(path)
        
        painter.setPen(pen)
        painter.drawPath(path)

        # 2. النبض الكوني
        max_radius = min(scr_width, scr_height) * 0.4
        current_radius = max_radius * smooth_ratio

        if current_radius > 0:
            gradient = QRadialGradient(center, current_radius)
            gradient.setColorAt(0.0, QColor(0, 255, 255, 0))
            gradient.setColorAt(0.8, GLOW_COLOR)
            gradient.setColorAt(1.0, QColor(0, 255, 255, 0))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            
            # الحل الجذري لمشكلة الـ QPointF برسم مربع وهمي
            rect = QRectF(center.x() - current_radius, center.y() - current_radius, current_radius * 2, current_radius * 2)
            painter.drawEllipse(rect)

        # 3. الظهور (التلاشي العكسي)
        content_opacity = 0
        if self.elapsed_ratio > 0.5:
            content_opacity = int((self.elapsed_ratio - 0.5) * 2.0 * 255)
            content_opacity = min(255, max(0, content_opacity))

        content_color = QColor(0, 255, 255, content_opacity)
        painter.setPen(QPen(content_color, 2))

        lightning_path = QPainterPath()
        lx = center.x()
        ly = center.y() - 20
        scale = 1.5
        lightning_path.moveTo(lx + (10 * scale), ly - (30 * scale))
        lightning_path.lineTo(lx - (15 * scale), ly + (0 * scale))
        lightning_path.lineTo(lx + (5 * scale), ly + (0 * scale))
        lightning_path.lineTo(lx - (10 * scale), ly + (30 * scale))
        lightning_path.lineTo(lx + (15 * scale), ly + (0 * scale))
        lightning_path.lineTo(lx - (5 * scale), ly + (0 * scale))
        lightning_path.closeSubpath()
        
        painter.setBrush(QBrush(content_color))
        painter.drawPath(lightning_path)

        font = QFont("Monospace", 30, QFont.Weight.Bold)
        painter.setFont(font)
        text_rect = QRectF(center.x() - 100, center.y() + 50, 200, 50)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, f"{self.battery_percent}%")

if __name__ == "__main__":
    # إجبار النظام على استخدام XWayland للسماح بالشفافية الكاملة وتجاوز قيود Wayland
    os.environ["QT_QPA_PLATFORM"] = "xcb"
        
    app = QApplication(sys.argv)
    overlay = NeonChargeOverlay()
    sys.exit(app.exec())

# تلاشي