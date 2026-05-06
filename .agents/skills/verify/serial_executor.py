#!/usr/bin/env python3
"""
串口测试执行器 - 与STM32串口通信
"""

import serial
import serial.tools.list_ports
import re
import time
from typing import Optional, List


class SerialTestExecutor:
    """串口测试执行器"""

    def __init__(self, config: dict):
        self.config = config
        self.port = config.get('port', 'auto')
        self.baudrate = config.get('baudrate', 115200)
        self.serial = None

    def __enter__(self):
        """上下文管理器 - 连接串口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器 - 关闭串口"""
        self.disconnect()

    def connect(self):
        """连接串口"""
        if self.port == 'auto':
            self.port = self._auto_detect_port()

        print(f"  连接串口: {self.port} @ {self.baudrate}bps")

        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1
            )

            # 复位目标板（如果配置）
            if self.config.get('reset_before_test', True):
                self._reset_target()

        except serial.SerialException as e:
            raise ConnectionError(f"无法连接串口 {self.port}: {e}")

    def disconnect(self):
        """断开串口"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            print(f"  断开串口: {self.port}")

    def _auto_detect_port(self) -> str:
        """自动检测STM32串口"""
        ports = serial.tools.list_ports.comports()

        # 优先查找STM32相关的VID/PID
        for port in ports:
            # STM32 USB CDC的常见VID
            if 'STM' in port.description or 'STM' in port.manufacturer or \
               '0483' in port.hwid or '374B' in port.hwid:
                return port.device

        # 其次查找ST-Link虚拟串口
        for port in ports:
            if 'ST-Link' in port.description or 'STLink' in port.description:
                return port.device

        # 最后返回第一个可用串口
        if ports:
            return ports[0].device

        raise ConnectionError("未找到可用串口")

    def _reset_target(self):
        """通过DTR/RTS复位目标板"""
        if not self.serial:
            return

        # STM32通常使用DTR复位
        self.serial.dtr = False
        time.sleep(0.1)
        self.serial.dtr = True
        time.sleep(0.1)
        self.serial.dtr = False

        # 等待启动
        delay_ms = self.config.get('delay_after_reset_ms', 500)
        time.sleep(delay_ms / 1000)

        # 清空启动期间的输出
        self.clear_buffer()

    def send(self, data: str):
        """发送数据"""
        if not self.serial or not self.serial.is_open:
            raise ConnectionError("串口未连接")

        # 自动添加换行
        if not data.endswith('\n'):
            data += '\n'

        self.serial.write(data.encode('utf-8'))
        self.serial.flush()

    def receive(self, timeout: float = 1.0) -> str:
        """接收数据（带超时）"""
        if not self.serial or not self.serial.is_open:
            raise ConnectionError("串口未连接")

        self.serial.timeout = timeout
        data = self.serial.read(4096)
        return data.decode('utf-8', errors='ignore')

    def receive_until(self, pattern: str, timeout: float = 2.0) -> str:
        """接收数据直到匹配模式或超时"""
        if not self.serial or not self.serial.is_open:
            raise ConnectionError("串口未连接")

        buffer = ""
        start_time = time.time()

        while time.time() - start_time < timeout:
            # 非阻塞读取
            if self.serial.in_waiting:
                data = self.serial.read(self.serial.in_waiting)
                buffer += data.decode('utf-8', errors='ignore')

                # 检查是否匹配
                if pattern in buffer:
                    return buffer

            time.sleep(0.01)

        # 超时返回已收到的内容
        return buffer

    def receive_line(self, timeout: float = 2.0) -> str:
        """接收一行数据"""
        if not self.serial or not self.serial.is_open:
            raise ConnectionError("串口未连接")

        self.serial.timeout = timeout
        line = self.serial.readline()
        return line.decode('utf-8', errors='ignore').strip()

    def clear_buffer(self):
        """清空接收缓冲区"""
        if not self.serial or not self.serial.is_open:
            return

        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()

    def list_ports() -> List[str]:
        """列出可用串口"""
        return [p.device for p in serial.tools.list_ports.comports()]
