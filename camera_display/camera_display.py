#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Qt摄像头显示程序
同时显示外接USB摄像头的彩色图像、RealSense D405的深度图像和彩色图像
包含帧率(FPS)显示功能
包含摄像头打开/关闭功能，支持热拔插
包含gripper夹爪开合测试功能
包含Sense夹爪开合数据显示功能
"""

import sys
import cv2
import numpy as np
import pyrealsense2 as rs
import time
import os
import json
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
                            QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout,
                            QMessageBox, QFrame, QSlider, QComboBox, QGroupBox,
                            QLineEdit)
from gripper_control import GripperController, list_serial_ports

class CameraDisplayApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 设置窗口标题和大小
        self.setWindowTitle("pika 测试软件")
        self.setMinimumSize(1920, 900)  # 增加高度以容纳夹爪控制和数据显示区域
        
        # 初始化变量
        self.rs_pipeline = None
        self.rs_depth_frame_available = False
        self.rs_color_frame_available = False
        self.usb_cam_available = False
        self.usb_cam = None
        self.colorizer = None
        
        # 初始化夹爪控制器
        self.gripper = GripperController()
        self.gripper_enabled = False
        
        # 初始化夹爪数据接收器
        self.sense_gripper = GripperController()
        self.sense_data_receiving = False
        
        # 窗口尺寸
        self.window_width = 640
        self.window_height = 480
        
        # 初始化FPS计算变量
        self.usb_fps_start_time = time.time()
        self.rs_color_fps_start_time = time.time()
        self.rs_depth_fps_start_time = time.time()
        self.usb_frame_count = 0
        self.rs_color_frame_count = 0
        self.rs_depth_frame_count = 0
        self.usb_fps = 0
        self.rs_color_fps = 0
        self.rs_depth_fps = 0
        
        # 创建占位图像
        self.usb_placeholder = self.create_placeholder_image(self.window_width, self.window_height, "The USB camera is not connected")
        self.rs_color_placeholder = self.create_placeholder_image(self.window_width, self.window_height, "The RealSense color camera is not connected")
        self.rs_depth_placeholder = self.create_placeholder_image(self.window_width, self.window_height, "The RealSense depth camera is not connected")
        
        # 初始化UI
        self.init_ui()
        
        # 创建定时器用于更新摄像头画面
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frames)
        self.timer.start(30)  # 约33FPS
        
        # 创建定时器用于定期刷新串口列表
        self.port_timer = QTimer()
        self.port_timer.timeout.connect(self.refresh_serial_ports)
        self.port_timer.start(2000)  # 每2秒刷新一次
        
        # 创建定时器用于更新夹爪数据显示
        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self.update_gripper_data_display)
        self.data_timer.start(100)  # 每100ms更新一次
    
    def init_ui(self):
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建摄像头显示区域
        camera_layout = QHBoxLayout()
        
        # USB摄像头显示区域
        usb_frame = QFrame()
        usb_frame.setFrameShape(QFrame.Box)
        usb_frame.setLineWidth(2)
        usb_layout = QVBoxLayout(usb_frame)
        usb_title = QLabel("USB摄像头 (彩色)")
        usb_title.setAlignment(Qt.AlignCenter)
        usb_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.usb_label = QLabel()
        self.usb_label.setFixedSize(self.window_width, self.window_height)
        self.usb_label.setAlignment(Qt.AlignCenter)
        usb_layout.addWidget(usb_title)
        usb_layout.addWidget(self.usb_label)
        
        # RealSense彩色摄像头显示区域
        rs_color_frame = QFrame()
        rs_color_frame.setFrameShape(QFrame.Box)
        rs_color_frame.setLineWidth(2)
        rs_color_layout = QVBoxLayout(rs_color_frame)
        rs_color_title = QLabel("RealSense D405 (彩色)")
        rs_color_title.setAlignment(Qt.AlignCenter)
        rs_color_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.rs_color_label = QLabel()
        self.rs_color_label.setFixedSize(self.window_width, self.window_height)
        self.rs_color_label.setAlignment(Qt.AlignCenter)
        rs_color_layout.addWidget(rs_color_title)
        rs_color_layout.addWidget(self.rs_color_label)
        
        # RealSense深度摄像头显示区域
        rs_depth_frame = QFrame()
        rs_depth_frame.setFrameShape(QFrame.Box)
        rs_depth_frame.setLineWidth(2)
        rs_depth_layout = QVBoxLayout(rs_depth_frame)
        rs_depth_title = QLabel("RealSense D405 (深度)")
        rs_depth_title.setAlignment(Qt.AlignCenter)
        rs_depth_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.rs_depth_label = QLabel()
        self.rs_depth_label.setFixedSize(self.window_width, self.window_height)
        self.rs_depth_label.setAlignment(Qt.AlignCenter)
        rs_depth_layout.addWidget(rs_depth_title)
        rs_depth_layout.addWidget(self.rs_depth_label)
        
        # 添加三个摄像头显示区域到水平布局
        camera_layout.addWidget(usb_frame)
        camera_layout.addWidget(rs_color_frame)
        camera_layout.addWidget(rs_depth_frame)
        
        # 创建夹爪控制区域
        gripper_group = QGroupBox("Gripper夹爪开合测试")
        gripper_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        gripper_layout = QGridLayout(gripper_group)
        
        # 串口选择区域
        port_label = QLabel("Gripper串口选择:")
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(150)
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.clicked.connect(self.refresh_serial_ports)
        self.connect_button = QPushButton("连接")
        self.connect_button.clicked.connect(self.connect_gripper)
        
        # 夹爪使能区域
        self.enable_button = QPushButton("使能夹爪")
        self.enable_button.setCheckable(True)
        self.enable_button.clicked.connect(self.toggle_gripper_enable)
        self.enable_button.setEnabled(False)  # 初始禁用，直到连接成功
        
        # 夹爪位置控制区域
        position_label = QLabel("夹爪位置[0.0 - 1.68]:")
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 168)  # 0.0 到 1.68，乘以100
        self.position_slider.setValue(0)
        self.position_slider.setTickPosition(QSlider.TicksBelow)
        self.position_slider.setTickInterval(10)
        self.position_slider.valueChanged.connect(self.update_gripper_position)
        self.position_slider.setEnabled(False)  # 初始禁用，直到使能成功
        
        # 增大滑动条尺寸
        self.position_slider.setMinimumHeight(40)
        self.position_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 10px;
                margin: 0px;
                border-radius: 5px;
                background: #B0B0B0;
            }
            QSlider::handle:horizontal {
                background: #808080;
                border: 1px solid #5c5c5c;
                width: 30px;
                height: 30px;
                margin: -10px 0;
                border-radius: 15px;
            }
            QSlider::handle:horizontal:hover {
                background: #606060;
            }
        """)
        
        self.position_value_label = QLabel("0.00")
        self.position_value_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        # 添加控件到夹爪控制布局
        gripper_layout.addWidget(port_label, 0, 0)
        gripper_layout.addWidget(self.port_combo, 0, 1)
        gripper_layout.addWidget(self.refresh_button, 0, 2)
        gripper_layout.addWidget(self.connect_button, 0, 3)
        gripper_layout.addWidget(self.enable_button, 1, 0, 1, 2)
        gripper_layout.addWidget(position_label, 2, 0)
        gripper_layout.addWidget(self.position_slider, 2, 1, 1, 2)
        gripper_layout.addWidget(self.position_value_label, 2, 3)
        
        # 创建夹爪数据显示区域
        sense_group = QGroupBox("Sense夹爪开合数据")
        sense_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        sense_layout = QGridLayout(sense_group)
        
        # 串口选择区域
        sense_port_label = QLabel("Sense串口选择:")
        self.sense_port_combo = QComboBox()
        self.sense_port_combo.setMinimumWidth(150)
        self.sense_refresh_button = QPushButton("刷新")
        self.sense_refresh_button.clicked.connect(self.refresh_serial_ports)
        self.sense_connect_button = QPushButton("连接")
        self.sense_connect_button.clicked.connect(self.connect_sense_gripper)
        
        # 夹爪角度显示区域 - 使用简单的白色数字显示
        angle_label = QLabel("夹爪角度 (rad):")
        self.angle_display = QLineEdit("0.0000")
        self.angle_display.setReadOnly(True)
        self.angle_display.setAlignment(Qt.AlignCenter)
        self.angle_display.setFont(QFont("Arial", 16))
        self.angle_display.setStyleSheet("""
            QLineEdit {
                background-color: white;
                color: black;
                border: 1px solid #A0A0A0;
                border-radius: 5px;
                padding: 5px;
                min-height: 30px;
            }
        """)
        
        # 数据接收状态
        self.data_status_label = QLabel("数据状态: 未连接")
        self.data_status_label.setStyleSheet("color: red;")
        
        # 添加控件到夹爪数据显示布局
        sense_layout.addWidget(sense_port_label, 0, 0)
        sense_layout.addWidget(self.sense_port_combo, 0, 1)
        sense_layout.addWidget(self.sense_refresh_button, 0, 2)
        sense_layout.addWidget(self.sense_connect_button, 0, 3)
        sense_layout.addWidget(angle_label, 1, 0)
        sense_layout.addWidget(self.angle_display, 1, 1, 1, 3)
        sense_layout.addWidget(self.data_status_label, 2, 0, 1, 4)
        
        # 创建摄像头控制按钮区域
        button_layout = QHBoxLayout()
        self.open_camera_button = QPushButton("打开摄像头")
        self.open_camera_button.setFixedHeight(40)
        self.open_camera_button.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.open_camera_button.clicked.connect(self.open_cameras)
        
        self.close_camera_button = QPushButton("关闭摄像头")
        self.close_camera_button.setFixedHeight(40)
        self.close_camera_button.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.close_camera_button.clicked.connect(self.close_cameras)
        
        button_layout.addStretch(1)
        button_layout.addWidget(self.open_camera_button)
        button_layout.addSpacing(20)  # 添加间距
        button_layout.addWidget(self.close_camera_button)
        button_layout.addStretch(1)
        
        # 添加所有区域到主布局
        main_layout.addLayout(camera_layout)
        main_layout.addWidget(gripper_group)
        main_layout.addWidget(sense_group)
        main_layout.addLayout(button_layout)
        
        # 显示占位图像
        self.display_image(self.usb_label, self.usb_placeholder)
        self.display_image(self.rs_color_label, self.rs_color_placeholder)
        self.display_image(self.rs_depth_label, self.rs_depth_placeholder)
        
        # 初始化串口列表
        self.refresh_serial_ports()
    
    def refresh_serial_ports(self):
        """刷新串口设备列表"""
        # 保存当前选择的端口
        current_port = self.port_combo.currentText()
        current_sense_port = self.sense_port_combo.currentText()
        
        # 清空下拉框
        self.port_combo.clear()
        self.sense_port_combo.clear()
        
        # 获取可用串口列表
        ports = list_serial_ports()
        
        if ports:
            # 添加到下拉框
            self.port_combo.addItems(ports)
            self.sense_port_combo.addItems(ports)
            
            # 如果之前选择的端口仍然存在，则保持选择
            if current_port in ports:
                self.port_combo.setCurrentText(current_port)
            
            if current_sense_port in ports:
                self.sense_port_combo.setCurrentText(current_sense_port)
            
            # 启用连接按钮
            self.connect_button.setEnabled(True)
            self.sense_connect_button.setEnabled(True)
        else:
            # 无可用串口
            self.port_combo.addItem("未检测到设备")
            self.sense_port_combo.addItem("未检测到设备")
            self.connect_button.setEnabled(False)
            self.sense_connect_button.setEnabled(False)
    
    def connect_gripper(self):
        """连接或断开夹爪控制器"""
        if self.gripper.is_connected():
            # 断开连接
            self.gripper.disconnect()
            self.connect_button.setText("连接")
            self.enable_button.setEnabled(False)
            self.position_slider.setEnabled(False)
            self.enable_button.setChecked(False)
            self.gripper_enabled = False
            self.port_combo.setEnabled(True)
            self.refresh_button.setEnabled(True)
        else:
            # 连接
            port = self.port_combo.currentText()
            if port and port != "未检测到设备":
                if self.gripper.connect(port):
                    self.connect_button.setText("断开")
                    self.enable_button.setEnabled(True)
                    self.port_combo.setEnabled(False)
                    self.refresh_button.setEnabled(False)
                    QMessageBox.information(self, "连接成功", f"成功连接到串口设备: {port}")
                else:
                    QMessageBox.warning(self, "连接失败", f"无法连接到串口设备: {port}")
    
    def connect_sense_gripper(self):
        """连接或断开夹爪数据接收器"""
        if self.sense_gripper.is_connected():
            # 断开连接
            self.sense_gripper.stop_data_reception()
            self.sense_gripper.disconnect()
            self.sense_connect_button.setText("连接")
            self.sense_port_combo.setEnabled(True)
            self.sense_refresh_button.setEnabled(True)
            self.sense_data_receiving = False
            self.data_status_label.setText("数据状态: 未连接")
            self.data_status_label.setStyleSheet("color: red;")
            self.angle_display.setText("0.0000")
            # 重置角度显示颜色为默认
            self.angle_display.setStyleSheet("""
                QLineEdit {
                    background-color: white;
                    color: black;
                    border: 1px solid #A0A0A0;
                    border-radius: 5px;
                    padding: 5px;
                    min-height: 30px;
                }
            """)
        else:
            # 连接
            port = self.sense_port_combo.currentText()
            if port and port != "未检测到设备":
                if self.sense_gripper.connect(port):
                    # 开始数据接收
                    if self.sense_gripper.start_data_reception(self.on_gripper_data_received):
                        self.sense_connect_button.setText("断开")
                        self.sense_port_combo.setEnabled(False)
                        self.sense_refresh_button.setEnabled(False)
                        self.sense_data_receiving = True
                        self.data_status_label.setText("数据状态: 已连接")
                        self.data_status_label.setStyleSheet("color: green;")
                        QMessageBox.information(self, "连接成功", f"成功连接到串口设备: {port}")
                    else:
                        self.sense_gripper.disconnect()
                        QMessageBox.warning(self, "数据接收失败", "无法启动数据接收")
                else:
                    QMessageBox.warning(self, "连接失败", f"无法连接到串口设备: {port}")
    
    def on_gripper_data_received(self, angle, distance, timestamp):
        """夹爪数据接收回调函数"""
        # 数据接收回调，由数据接收线程调用
        # 不在此处更新UI，避免线程安全问题
        pass
    
    def update_gripper_data_display(self):
        """更新夹爪数据显示"""
        if not self.sense_gripper.is_connected() or not self.sense_data_receiving:
            return
        
        # 获取当前数据
        angle, distance, timestamp = self.sense_gripper.get_current_data()
        
        # 检查数据是否过期（超过1秒未更新）
        if time.time() - timestamp > 1.0:
            self.data_status_label.setText("数据状态: 无数据")
            self.data_status_label.setStyleSheet("color: orange;")
        else:
            self.data_status_label.setText("数据状态: 接收中")
            self.data_status_label.setStyleSheet("color: green;")
        
        # 更新显示
        self.angle_display.setText(f"{angle:.4f}")
        
        # 根据角度值设置颜色
        if angle < 1.68 or angle > 1.75:
            # 角度超出范围，显示红色
            self.angle_display.setStyleSheet("""
                QLineEdit {
                    background-color: #FFDDDD;
                    color: red;
                    border: 1px solid red;
                    border-radius: 5px;
                    padding: 5px;
                    min-height: 30px;
                    font-weight: bold;
                }
            """)
        else:
            # 角度在范围内，显示绿色
            self.angle_display.setStyleSheet("""
                QLineEdit {
                    background-color: #DDFFDD;
                    color: green;
                    border: 1px solid green;
                    border-radius: 5px;
                    padding: 5px;
                    min-height: 30px;
                    font-weight: bold;
                }
            """)
    
    def toggle_gripper_enable(self, checked):
        """切换夹爪使能状态"""
        if not self.gripper.is_connected():
            return
        
        if checked:
            # 使能夹爪
            if self.gripper.enable():
                self.gripper_enabled = True
                self.enable_button.setText("禁用夹爪")
                self.position_slider.setEnabled(True)
                QMessageBox.information(self, "夹爪使能", "夹爪已成功使能")
            else:
                self.enable_button.setChecked(False)
                QMessageBox.warning(self, "夹爪使能失败", "无法使能夹爪")
        else:
            # 禁用夹爪
            if self.gripper.disable():
                self.gripper_enabled = False
                self.enable_button.setText("使能夹爪")
                self.position_slider.setEnabled(False)
            else:
                self.enable_button.setChecked(True)
                QMessageBox.warning(self, "夹爪禁用失败", "无法禁用夹爪")
    
    def update_gripper_position(self, value):
        """更新夹爪位置"""
        if not self.gripper.is_connected() or not self.gripper_enabled:
            return
        
        # 将滑动条值转换为实际角度值 (0-168 -> 0.0-1.68)
        angle = value / 100.0
        self.position_value_label.setText(f"{angle:.2f}")
        
        # 设置夹爪位置
        self.gripper.set_position(angle)
    
    def create_placeholder_image(self, width, height, text):
        """创建一个带有文本提示的占位图像"""
        # 创建黑色背景图像
        image = np.zeros((height, width, 3), dtype=np.uint8)
        
        # 设置文本参数
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        font_color = (255, 255, 255)  # 白色
        font_thickness = 2
        
        # 计算文本大小以居中显示
        text_size = cv2.getTextSize(text, font, font_scale, font_thickness)[0]
        text_x = (width - text_size[0]) // 2
        text_y = (height + text_size[1]) // 2
        
        # 在图像上绘制文本
        cv2.putText(image, text, (text_x, text_y), font, font_scale, font_color, font_thickness)
        
        return image
    
    def display_image(self, label, image):
        """将OpenCV图像显示在QLabel上"""
        h, w, ch = image.shape
        bytes_per_line = ch * w
        qt_image = QImage(image.data, w, h, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(qt_image)
        label.setPixmap(pixmap)
    
    def open_cameras(self):
        """打开摄像头"""
        # 先关闭现有摄像头
        self.close_cameras()
        
        # 显示占位图像
        self.display_image(self.usb_label, self.usb_placeholder)
        self.display_image(self.rs_color_label, self.rs_color_placeholder)
        self.display_image(self.rs_depth_label, self.rs_depth_placeholder)
        
        # 尝试初始化RealSense D405摄像头
        try:
            # 初始化RealSense管道和配置
            self.rs_pipeline = rs.pipeline()
            rs_config = rs.config()
            
            # 查找RealSense设备
            ctx = rs.context()
            devices = ctx.query_devices()
            
            if len(devices) == 0:
                print("未检测到RealSense设备，将显示提示窗口")
                QMessageBox.warning(self, "摄像头检测", "未检测到RealSense设备，将显示占位图像")
            else:
                # 获取RealSense设备序列号
                device = devices[0]
                serial_number = device.get_info(rs.camera_info.serial_number)
                print(f"已检测到RealSense设备，序列号: {serial_number}")
                
                # 配置RealSense流
                rs_config.enable_device(serial_number)
                rs_config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
                rs_config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
                
                # 启动RealSense管道
                self.rs_pipeline.start(rs_config)
                print("RealSense D405摄像头已启动")
                self.rs_depth_frame_available = True
                self.rs_color_frame_available = True
                
                # 创建深度图像的颜色映射对象
                self.colorizer = rs.colorizer()
        except Exception as e:
            print(f"RealSense摄像头初始化失败: {e}")
            QMessageBox.warning(self, "摄像头检测", f"RealSense摄像头初始化失败: {e}\n将显示占位图像")
            if self.rs_pipeline is not None:
                try:
                    self.rs_pipeline.stop()
                    self.rs_pipeline = None
                except:
                    pass
        
        # 初始化外接USB摄像头
        # 注意：我们从索引1开始尝试，避免使用笔记本自带摄像头（通常是索引0）
        usb_cam_index = 1  # 从索引1开始尝试
        
        while usb_cam_index < 10:  # 尝试多个索引以找到外接USB摄像头
            try:
                temp_cam = cv2.VideoCapture(usb_cam_index)
                if temp_cam.isOpened():
                    ret, frame = temp_cam.read()
                    if ret:
                        self.usb_cam = temp_cam
                        self.usb_cam_available = True
                        print(f"外接USB摄像头已找到，索引: {usb_cam_index}")
                        break
                    else:
                        temp_cam.release()
                else:
                    temp_cam.release()
            except Exception as e:
                print(f"尝试索引 {usb_cam_index} 失败: {e}")
            
            usb_cam_index += 1
        
        if self.usb_cam is None:
            print("未找到外接USB摄像头，将显示提示窗口")
            QMessageBox.warning(self, "摄像头检测", "未找到外接USB摄像头，将显示占位图像")
        
        # 如果所有摄像头都不可用，则提示用户
        if not self.rs_depth_frame_available and not self.rs_color_frame_available and not self.usb_cam_available:
            QMessageBox.warning(self, "摄像头检测", "所有摄像头均不可用，将显示占位图像")
        else:
            QMessageBox.information(self, "摄像头打开", "摄像头已成功打开")
    
    def close_cameras(self):
        """关闭摄像头"""
        # 释放资源
        if self.usb_cam is not None:
            self.usb_cam.release()
            self.usb_cam = None
            self.usb_cam_available = False
        
        if self.rs_pipeline is not None:
            self.rs_pipeline.stop()
            self.rs_pipeline = None
            self.rs_depth_frame_available = False
            self.rs_color_frame_available = False
        
        # 重置FPS计算变量
        self.usb_fps_start_time = time.time()
        self.rs_color_fps_start_time = time.time()
        self.rs_depth_fps_start_time = time.time()
        self.usb_frame_count = 0
        self.rs_color_frame_count = 0
        self.rs_depth_frame_count = 0
        self.usb_fps = 0
        self.rs_color_fps = 0
        self.rs_depth_fps = 0
        
        # 显示占位图像
        self.display_image(self.usb_label, self.usb_placeholder)
        self.display_image(self.rs_color_label, self.rs_color_placeholder)
        self.display_image(self.rs_depth_label, self.rs_depth_placeholder)
        
        print("已关闭所有摄像头")
    
    def update_frames(self):
        """更新摄像头画面"""
        # 初始化图像变量
        rs_depth_image = self.rs_depth_placeholder.copy()
        rs_color_image = self.rs_color_placeholder.copy()
        usb_color_image = self.usb_placeholder.copy()
        
        # 获取RealSense帧（如果可用）
        if self.rs_pipeline is not None and (self.rs_depth_frame_available or self.rs_color_frame_available):
            try:
                rs_frames = self.rs_pipeline.wait_for_frames(200)  # 设置超时时间为200ms
                
                if self.rs_depth_frame_available:
                    rs_depth_frame = rs_frames.get_depth_frame()
                    if rs_depth_frame:
                        # 将RealSense深度帧转换为numpy数组
                        rs_depth_image = np.asanyarray(self.colorizer.colorize(rs_depth_frame).get_data())
                        
                        # 计算RealSense深度摄像头FPS
                        self.rs_depth_frame_count += 1
                        if (time.time() - self.rs_depth_fps_start_time) > 1.0:  # 每秒更新一次FPS
                            self.rs_depth_fps = self.rs_depth_frame_count / (time.time() - self.rs_depth_fps_start_time)
                            self.rs_depth_frame_count = 0
                            self.rs_depth_fps_start_time = time.time()
                        
                        # 在RealSense深度图像上显示FPS
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        font_scale = 0.7
                        font_color = (0, 255, 0)  # 绿色
                        font_thickness = 2
                        fps_text = f"FPS: {self.rs_depth_fps:.1f}"
                        cv2.putText(rs_depth_image, fps_text, (10, 30), font, font_scale, font_color, font_thickness)
                
                if self.rs_color_frame_available:
                    rs_color_frame = rs_frames.get_color_frame()
                    if rs_color_frame:
                        # 将RealSense彩色帧转换为numpy数组
                        rs_color_image = np.asanyarray(rs_color_frame.get_data())
                        
                        # 计算RealSense彩色摄像头FPS
                        self.rs_color_frame_count += 1
                        if (time.time() - self.rs_color_fps_start_time) > 1.0:  # 每秒更新一次FPS
                            self.rs_color_fps = self.rs_color_frame_count / (time.time() - self.rs_color_fps_start_time)
                            self.rs_color_frame_count = 0
                            self.rs_color_fps_start_time = time.time()
                        
                        # 在RealSense彩色图像上显示FPS
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        font_scale = 0.7
                        font_color = (0, 255, 0)  # 绿色
                        font_thickness = 2
                        fps_text = f"FPS: {self.rs_color_fps:.1f}"
                        cv2.putText(rs_color_image, fps_text, (10, 30), font, font_scale, font_color, font_thickness)
            except Exception as e:
                print(f"获取RealSense帧时出错: {e}")
        
        # 获取USB摄像头帧（如果可用）
        if self.usb_cam is not None and self.usb_cam_available:
            try:
                ret, frame = self.usb_cam.read()
                if ret:
                    usb_color_image = frame
                    
                    # 计算USB摄像头FPS
                    self.usb_frame_count += 1
                    if (time.time() - self.usb_fps_start_time) > 1.0:  # 每秒更新一次FPS
                        self.usb_fps = self.usb_frame_count / (time.time() - self.usb_fps_start_time)
                        self.usb_frame_count = 0
                        self.usb_fps_start_time = time.time()
                    
                    # 在USB摄像头图像上显示FPS
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 0.7
                    font_color = (0, 255, 0)  # 绿色
                    font_thickness = 2
                    fps_text = f"FPS: {self.usb_fps:.1f}"
                    cv2.putText(usb_color_image, fps_text, (10, 30), font, font_scale, font_color, font_thickness)
            except Exception as e:
                print(f"获取USB摄像头帧时出错: {e}")
        
        # 显示图像
        self.display_image(self.usb_label, usb_color_image)
        self.display_image(self.rs_color_label, rs_color_image)
        self.display_image(self.rs_depth_label, rs_depth_image)
    
    def closeEvent(self, event):
        """关闭窗口时释放资源"""
        # 停止定时器
        self.timer.stop()
        self.port_timer.stop()
        self.data_timer.stop()
        
        # 释放资源
        if self.usb_cam is not None:
            self.usb_cam.release()
        
        if self.rs_pipeline is not None:
            self.rs_pipeline.stop()
        
        # 断开夹爪连接
        if self.gripper.is_connected():
            self.gripper.disconnect()
        
        # 断开夹爪数据接收器连接
        if self.sense_gripper.is_connected():
            self.sense_gripper.stop_data_reception()
            self.sense_gripper.disconnect()
        
        print("已关闭所有摄像头和窗口")
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = CameraDisplayApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
