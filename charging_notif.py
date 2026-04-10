import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gio

class ChargingPopup(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_keep_above(True)
        self.set_decorated(False)
        self.set_accept_focus(False)
        self.set_visual(self.get_screen().get_rgba_visual())
        
        label = Gtk.Label()
        # تصميم أخضر مشع (Neon) يشبه واجهات Figma
        label.set_markup("<span foreground='#00ff00' size='40000' weight='bold'>⚡ CHARGING</span>")
        
        self.add(label)
        self.set_default_size(400, 150)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(b"""
            window {
                background-color: rgba(10, 10, 10, 0.9);
                border-radius: 60px;
                border: 4px solid #00ff00;
            }
        """)
        Gtk.StyleContext.add_provider_for_screen(self.get_screen(), style_provider, 800)

def on_properties_changed(proxy, changed_properties, invalidated_properties):
    changed = changed_properties.unpack()
    if 'State' in changed:
        state = changed['State']
        print(f"DEBUG: تم تغيير الحالة إلى: {state}")
        if state == 1: # 1 تعني شحن
            show_anim()

def show_anim():
    print("ACTION: إظهار أنيميشن الشحن! ⚡")
    popup = ChargingPopup()
    popup.show_all()
    GObject.timeout_add(3000, popup.destroy)

# الاتصال مباشرة بالبطارية BAT0 لضمان الدقة
bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
proxy = Gio.DBusProxy.new_sync(
    bus, Gio.DBusProxyFlags.NONE, None,
    'org.freedesktop.UPower',
    '/org/freedesktop/UPower/devices/battery_BAT0', # غيرنا المسار هنا
    'org.freedesktop.UPower.Device', None
)

proxy.connect("g-properties-changed", on_properties_changed)

print("السكربت يعمل الآن.. جرب توصيل الشاحن (BAT0 Monitoring)")
Gtk.main()
