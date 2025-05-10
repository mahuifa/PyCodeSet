import platform

# 判断操作系统
system_name = platform.system()

if system_name == "Windows":
    # Windows 系统
    from .winUSBMonitor import USBMonitor
    print("已导入 Windows 模块")
elif system_name == "Linux":
    # Linux 系统
    from .linuxUSBMonitor import USBMonitor
    print("已导入 Linux 模块")
elif system_name == "Darwin":
    # macOS 系统
    pass
    print("已导入 macOS 模块")
else:
    print("未知操作系统")