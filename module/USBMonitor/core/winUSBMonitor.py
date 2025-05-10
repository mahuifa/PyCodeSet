import wmi
import threading
import time
import pythoncom  # 用于处理COM库的线程安全初始化


class USBMonitor:
    """
    USB设备实时监控类（Windows平台专用）
    功能特性：
    - 基于WMI实现设备热插拔事件监听
    - 支持设备插入/移除的双向回调机制
    - 使用独立监控线程避免阻塞主程序
    - 自动处理COM库线程初始化问题
    """

    def __init__(self, on_device_added=None, on_device_removed=None):
        """
        初始化监控实例
        :param on_device_added:   设备插入回调函数，格式 func(device_obj)
        :param on_device_removed: 设备移除回调函数，格式 func(device_obj)
        """
        self.on_device_added = on_device_added
        self.on_device_removed = on_device_removed
        self.monitor_thread = threading.Thread(target=self.start_monitoring)
        self.monitor_thread.daemon = True  # 设为守护线程确保主程序退出时自动终止
        self.thread_running = False  # 线程运行状态标志

    def get_all_devices(self):
        """获取当前已连接的USB设备列表（快照）"""
        c = wmi.WMI(moniker="root/cimv2")
        return c.Win32_USBControllerDevice()  # 返回Win32_USBControllerDevice对象集合

    def device_added_callback(self, new_device):
        """内部设备插入事件处理器"""
        if callable(self.on_device_added):  # 安全检查回调函数
            self.on_device_added(new_device)

    def device_removed_callback(self, removed_device):
        """内部设备移除事件处理器"""
        if callable(self.on_device_removed):
            self.on_device_removed(removed_device)

    def start_monitoring(self):
        """监控线程主循环（核心逻辑）"""
        pythoncom.CoInitialize()  # 每个线程必须独立初始化COM库
        try:
            c = wmi.WMI(moniker="root/cimv2")
            # 配置插入事件监听器（1秒轮询间隔）
            arr_filter = c.Win32_PnPEntity.watch_for(
                notification_type="creation",
                delay_secs=1
            )
            # 配置移除事件监听器
            rem_filter = c.Win32_PnPEntity.watch_for(
                notification_type="deletion",
                delay_secs=1
            )

            self.thread_running = True
            print("[监控系统] USB设备监控服务启动")
            while self.thread_running:
                # 非阻塞式检测插入事件（0.5秒超时）
                try:
                    new_device = arr_filter(0.5)
                    self.device_added_callback(new_device)
                except wmi.x_wmi_timed_out:
                    pass  # 正常超时，继续循环

                # 非阻塞式检测移除事件
                try:
                    removed_device = rem_filter(0.5)
                    self.device_removed_callback(removed_device)
                except wmi.x_wmi_timed_out:
                    pass

        except KeyboardInterrupt:
            print("\n[监控系统] 用户主动终止监控")
        finally:
            pythoncom.CoUninitialize()  # 必须释放COM资源
            print("[监控系统] 监控服务已安全关闭")

    def start(self):
        """启动监控服务"""
        if not self.monitor_thread.is_alive():
            self.monitor_thread.start()

    def stop(self):
        """安全停止监控服务"""
        self.thread_running = False
        if self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)  # 等待线程结束