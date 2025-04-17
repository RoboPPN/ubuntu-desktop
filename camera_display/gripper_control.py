#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
夹爪控制模块
提供串口通信和夹爪控制功能
"""

import serial
import serial.tools.list_ports
import struct
import time
import json
import threading

# 定义发送标志
class SendFlag:
    DISABLE = 10
    ENABLE = 11
    SET_ZERO = 12
    EFFORT_CTRL = 20
    VELOCITY_CTRL = 21
    POSITION_CTRL = 22

class GripperController:
    def __init__(self, port=None, baudrate=460800):
        self.serial = None
        self.port = port
        self.baudrate = baudrate
        self.enabled = False
        self.read_thread = None
        self.stop_thread = False
        self.data_callback = None
        self.current_angle = 0.0
        self.current_distance = 0.0
        self.last_data_time = 0
    
    def connect(self, port, baudrate=460800):
        """连接到指定串口"""
        try:
            if self.serial and self.serial.is_open:
                self.serial.close()
                if self.read_thread and self.read_thread.is_alive():
                    self.stop_thread = True
                    self.read_thread.join(timeout=1.0)
            
            self.serial = serial.Serial(port, baudrate, timeout=1)
            self.port = port
            self.baudrate = baudrate
            return True
        except Exception as e:
            print(f"串口连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开串口连接"""
        if self.read_thread and self.read_thread.is_alive():
            self.stop_thread = True
            self.read_thread.join(timeout=1.0)
            self.stop_thread = False
            
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.serial = None
            self.enabled = False
    
    def is_connected(self):
        """检查是否已连接"""
        return self.serial is not None and self.serial.is_open
    
    def enable(self):
        """使能夹爪"""
        if not self.is_connected():
            return False
        
        try:
            # 构建使能命令
            cmd = struct.pack('<cf2s', bytes([SendFlag.ENABLE]), 0.0, b'\r\n')
            self.serial.write(cmd)
            self.enabled = True
            return True
        except Exception as e:
            print(f"夹爪使能失败: {e}")
            return False
    
    def disable(self):
        """禁用夹爪"""
        if not self.is_connected():
            return False
        
        try:
            # 构建禁用命令
            cmd = struct.pack('<cf2s', bytes([SendFlag.DISABLE]), 0.0, b'\r\n')
            self.serial.write(cmd)
            self.enabled = False
            return True
        except Exception as e:
            print(f"夹爪禁用失败: {e}")
            return False
    
    def set_position(self, angle):
        """设置夹爪位置
        
        参数:
            angle (float): 夹爪角度，范围0-1.68
        """
        if not self.is_connected():
            return False
        
        # 确保角度在有效范围内
        angle = max(0.0, min(1.68, angle))
        
        try:
            # 构建位置控制命令
            cmd = struct.pack('<cf2s', bytes([SendFlag.POSITION_CTRL]), angle, b'\r\n')
            self.serial.write(cmd)
            return True
        except Exception as e:
            print(f"设置夹爪位置失败: {e}")
            return False
    
    def start_data_reception(self, callback=None):
        """开始接收数据
        
        参数:
            callback: 数据接收回调函数，接收参数为(angle, distance, timestamp)
        """
        if not self.is_connected():
            return False
        
        self.data_callback = callback
        self.stop_thread = False
        
        if self.read_thread is None or not self.read_thread.is_alive():
            self.read_thread = threading.Thread(target=self._read_data_thread, daemon=True)
            self.read_thread.start()
        
        return True
    
    def stop_data_reception(self):
        """停止接收数据"""
        if self.read_thread and self.read_thread.is_alive():
            self.stop_thread = True
            self.read_thread.join(timeout=1.0)
            self.stop_thread = False
            self.read_thread = None
    
    def _read_data_thread(self):
        """数据读取线程"""
        buffer = ""
        
        while not self.stop_thread and self.serial and self.serial.is_open:
            try:
                # 读取串口数据
                if self.serial.in_waiting > 0:
                    data = self.serial.read(self.serial.in_waiting).decode('utf-8', errors='ignore')
                    buffer += data
                    
                    # 查找完整的JSON对象
                    while True:
                        start_idx = buffer.find('{')
                        if start_idx == -1:
                            buffer = ""
                            break
                        
                        end_idx = buffer.find('}', start_idx)
                        if end_idx == -1:
                            buffer = buffer[start_idx:]
                            break
                        
                        # 提取JSON字符串
                        json_str = buffer[start_idx:end_idx+1]
                        buffer = buffer[end_idx+1:]
                        
                        try:
                            # 解析JSON数据
                            data_obj = json.loads(json_str)
                            
                            # 检查是否包含AS5047数据
                            if 'AS5047' in data_obj:
                                as5047_data = data_obj['AS5047']
                                if 'error' not in as5047_data:
                                    angle = as5047_data.get('rad', 0.0)
                                    if angle < 0:
                                        angle = 0.0
                                    distance = as5047_data.get('distance', 0.0)
                                    
                                    # 更新当前数据
                                    self.current_angle = angle
                                    self.current_distance = distance
                                    self.last_data_time = time.time()
                                    
                                    # 调用回调函数
                                    if self.data_callback:
                                        self.data_callback(angle, distance, self.last_data_time)
                        except json.JSONDecodeError:
                            # JSON解析错误，忽略
                            pass
                        except Exception as e:
                            print(f"数据处理错误: {e}")
                
                # 短暂休眠，避免CPU占用过高
                time.sleep(0.01)
            except Exception as e:
                print(f"数据读取线程错误: {e}")
                time.sleep(0.1)  # 出错时稍微延长休眠时间
    
    def get_current_data(self):
        """获取当前数据
        
        返回:
            tuple: (angle, distance, timestamp)
        """
        return (self.current_angle, self.current_distance, self.last_data_time)

def list_serial_ports():
    """列出所有可用的串口设备"""
    ports = []
    for port in serial.tools.list_ports.comports():
        if 'ttyUSB' in port.device:
            ports.append(port.device)
    return ports
