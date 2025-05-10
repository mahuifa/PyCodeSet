import pyudev
import threading
import time


class USBMonitor:
    """
    Linux系统USB设备热插拔监测
    功能特性：
    - 基于pyudev库监听内核级设备事件
    - 支持USB设备插入/移除事件回调
    - 自动过滤非USB设备事件
    - 支持设备详细信息获取（厂商ID、产品ID等）
    """

    def __init__(self, on_device_added=None, on_device_removed=None):
        """
        初始化监测器
        :param on_device_added:   插入回调函数 func(device_info_dict)
        :param on_device_removed: 移除回调函数 func(device_info_dict)
        """
        self.context = pyudev.Context()  # 创建pyudev上下文，用于与udev交互
        self.monitor = pyudev.Monitor.from_netlink(self.context)  # 创建监测器，监听内核设备事件
        self.monitor.filter_by(subsystem='usb')  # 只监听USB子系统的事件

        self.on_device_added = on_device_added  # USB设备插入事件的回调函数
        self.on_device_removed = on_device_removed  # USB设备移除事件的回调函数
        self.monitor_thread = None  # 监测线程
        self.running = False  # 标志监测是否正在运行

    def _parse_device_info(self, device):
        """解析设备信息为字典
        :param device: 设备对象
        :return: 包含设备信息的字典
        """
        return {
            'action': device.action,  # 设备事件类型（add/remove）
            'devnode': device.device_node,  # 设备节点路径
            'vendor_id': device.get('ID_VENDOR_ID'),  # 厂商ID
            'product_id': device.get('ID_MODEL_ID'),  # 产品ID
            'serial': device.get('ID_SERIAL_SHORT'),  # 设备序列号
            'name': device.get('ID_MODEL')  # 设备名称
        }

    def _event_handler(self, device):
        """统一事件处理器
        根据设备事件类型调用相应的回调函数
        :param device: 设备对象
        """
        info = self._parse_device_info(device)  # 解析设备信息
        if device.action == 'add':  # 设备插入事件
            if callable(self.on_device_added):  # 检查回调函数是否可调用
                self.on_device_added(info)
        elif device.action == 'remove':  # 设备移除事件
            if callable(self.on_device_removed):  # 检查回调函数是否可调用
                self.on_device_removed(info)

    def start_monitoring(self):
        """启动事件监听循环
        在循环中监听设备事件并调用事件处理器
        """
        self.running = True  # 设置运行标志
        print("[USB Monitor] 开始监测USB设备...")
        for device in iter(self.monitor.poll, None):  # 持续监听设备事件
            if not self.running:  # 如果停止标志被设置，退出循环
                break
            self._event_handler(device)  # 调用事件处理器

    def start(self):
        """启动监测线程
        在单独的线程中运行监测循环
        """
        if not self.monitor_thread or not self.monitor_thread.is_alive():  # 检查线程是否已启动
            self.monitor_thread = threading.Thread(target=self.start_monitoring)  # 创建新线程
            self.monitor_thread.daemon = True  # 设置为守护线程
            self.monitor_thread.start()  # 启动线程

    def stop(self):
        """安全停止监测
        停止监测线程并等待其结束
        """
        self.running = False  # 设置停止标志
        if self.monitor_thread and self.monitor_thread.is_alive():  # 检查线程是否仍在运行
            self.monitor_thread.join(timeout=2)  # 等待线程结束，超时时间为2秒
