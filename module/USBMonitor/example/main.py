import sys
import os
import time
# 将父目录添加到 sys.path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)
import core


def device_added_callback(device_info):
    """设备插入回调函数
    :param device_info: 包含设备信息的字典
    """
    print(f"[插入] 设备接入: {device_info}")


def device_removed_callback(device_info):
    """设备移除回调函数
    :param device_info: 包含设备信息的字典
    """
    print(f"[移除] 设备断开: {device_info}")

if __name__ == "__main__":
    usb_monitor = core.USBMonitor(device_added_callback, device_removed_callback)
    try:
        usb_monitor.start()
        print("监测运行中，按Ctrl+C停止...")
        while True:
            time.sleep(1)  # 主线程保持运行
    except KeyboardInterrupt:
        usb_monitor.stop()
        print("\n监测已停止")
