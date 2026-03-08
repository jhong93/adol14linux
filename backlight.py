#!/usr/bin/env python3
"""
RGB keyboard control for ASUS Vivobook M5406WA via HID LampArray protocol.

https://bbs.archlinux.org/viewtopic.php?id=298591
"""

import sys
import os
import struct
import fcntl
import array

VENDOR_ID = "0B05"
PRODUCT_ID = "5570"

def find_device():
    """Auto-detect hidraw device for ASUS ITE5570 keyboard controller."""
    import glob
    for uevent_path in glob.glob("/sys/class/hidraw/hidraw*/device/uevent"):
        with open(uevent_path) as f:
            content = f.read()
        if f"0000{VENDOR_ID}:0000{PRODUCT_ID}" in content.upper():
            name = uevent_path.split("/")[4]
            return f"/dev/{name}"
    print("Error: ASUS keyboard RGB controller (ITE5570) not found", file=sys.stderr)
    sys.exit(1)

def _IOWR(type_char, nr, size):
    return 0xC0000000 | (size << 16) | (ord(type_char) << 8) | nr

def get_feature_report(fd, report_id, size):
    buf = array.array('B', [report_id] + [0] * (size - 1))
    fcntl.ioctl(fd, _IOWR('H', 0x07, size), buf)
    return buf

def set_feature_report(fd, data):
    buf = array.array('B', data)
    fcntl.ioctl(fd, _IOWR('H', 0x06, len(data)), buf)
    return buf

def get_lamp_array_attributes(fd):
    report = get_feature_report(fd, 0x41, 23)
    lamp_count = struct.unpack_from('<H', report, 1)[0]
    bbox_w, bbox_h, bbox_d, kind, min_interval = struct.unpack_from('<IIIII', report, 3)
    return {
        'lamp_count': lamp_count,
        'bbox_width': bbox_w,
        'bbox_height': bbox_h,
        'bbox_depth': bbox_d,
        'kind': kind,
        'min_update_interval': min_interval
    }

def set_autonomous_mode(fd, enabled):
    set_feature_report(fd, [0x46, 1 if enabled else 0])

def set_color_range(fd, start, end, r, g, b, intensity=255):
    data = [0x45, 0x01]
    data += list(struct.pack('<H', start))
    data += list(struct.pack('<H', end))
    data += [r, g, b, intensity]
    set_feature_report(fd, data)

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print(f"  {sys.argv[0]} info          - Show lamp array info")
        print(f"  {sys.argv[0]} color RRGGBB  - Set solid color (hex)")
        print(f"  {sys.argv[0]} off           - Turn off LEDs")
        print(f"  {sys.argv[0]} auto          - Re-enable autonomous (rainbow) mode")
        sys.exit(1)

    fd = os.open(find_device(), os.O_RDWR)

    try:
        cmd = sys.argv[1]

        if cmd == "info":
            attrs = get_lamp_array_attributes(fd)
            kinds = {0: "Undefined", 1: "Keyboard", 2: "Mouse", 3: "GameController",
                     4: "Peripheral", 5: "Scene", 6: "Notification", 7: "Chassis", 8: "Wearable", 9: "Furniture"}
            print(f"Lamp count:          {attrs['lamp_count']}")
            print(f"Kind:                {kinds.get(attrs['kind'], 'Unknown')} ({attrs['kind']})")
            print(f"Bounding box:        {attrs['bbox_width']}x{attrs['bbox_height']}x{attrs['bbox_depth']} µm")
            print(f"Min update interval: {attrs['min_update_interval']} µs")

        elif cmd == "color":
            if len(sys.argv) < 3:
                print("Provide hex color, e.g.: color ff0000")
                sys.exit(1)
            hex_color = sys.argv[2].lstrip('#')
            if len(hex_color) != 6:
                print("Color must be 6 hex digits (RRGGBB)")
                sys.exit(1)
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)

            attrs = get_lamp_array_attributes(fd)
            set_autonomous_mode(fd, False)
            set_color_range(fd, 0, attrs['lamp_count'] - 1, r, g, b, 255)

        elif cmd == "off":
            attrs = get_lamp_array_attributes(fd)
            set_autonomous_mode(fd, False)
            set_color_range(fd, 0, attrs['lamp_count'] - 1, 0, 0, 0, 0)

        elif cmd == "auto":
            set_autonomous_mode(fd, True)

        else:
            print(f"Unknown command: {cmd}")
            sys.exit(1)

    finally:
        os.close(fd)

if __name__ == "__main__":
    main()