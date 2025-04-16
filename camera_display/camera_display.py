#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
摄像头显示脚本
同时显示外接USB摄像头的彩色图像、RealSense D405的深度图像和彩色图像
包含帧率(FPS)显示功能
窗口整齐排列功能
摄像头检测提示功能
"""

import cv2
import numpy as np
import pyrealsense2 as rs
import time
import tkinter as tk
from tkinter import messagebox

def create_alert_window(title, message):
    """创建提示窗口"""
    # 创建一个临时的根窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    # 显示消息框
    messagebox.showwarning(title, message)
    
    # 销毁根窗口
    root.destroy()

def create_placeholder_image(width, height, text):
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

def main():
    # 初始化变量
    rs_pipeline = None
    rs_depth_frame_available = False
    rs_color_frame_available = False
    usb_cam_available = False
    
    # 尝试初始化RealSense D405摄像头
    try:
        # 初始化RealSense管道和配置
        rs_pipeline = rs.pipeline()
        rs_config = rs.config()
        
        # 查找RealSense设备
        ctx = rs.context()
        devices = ctx.query_devices()
        
        if len(devices) == 0:
            print("未检测到RealSense设备，将显示提示窗口")
            create_alert_window("摄像头检测", "未检测到RealSense设备，将显示占位图像")
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
            rs_pipeline.start(rs_config)
            print("RealSense D405摄像头已启动")
            rs_depth_frame_available = True
            rs_color_frame_available = True
    except Exception as e:
        print(f"RealSense摄像头初始化失败: {e}")
        create_alert_window("摄像头检测", f"RealSense摄像头初始化失败: {e}\n将显示占位图像")
        if rs_pipeline is not None:
            try:
                rs_pipeline.stop()
            except:
                pass
    
    # 初始化外接USB摄像头
    # 注意：我们从索引1开始尝试，避免使用笔记本自带摄像头（通常是索引0）
    usb_cam = None
    usb_cam_index = 1  # 从索引1开始尝试
    
    while usb_cam_index < 10:  # 尝试多个索引以找到外接USB摄像头
        try:
            temp_cam = cv2.VideoCapture(usb_cam_index)
            if temp_cam.isOpened():
                ret, frame = temp_cam.read()
                if ret:
                    usb_cam = temp_cam
                    usb_cam_available = True
                    print(f"外接USB摄像头已找到，索引: {usb_cam_index}")
                    break
                else:
                    temp_cam.release()
            else:
                temp_cam.release()
        except Exception as e:
            print(f"尝试索引 {usb_cam_index} 失败: {e}")
        
        usb_cam_index += 1
    
    if usb_cam is None:
        print("未找到外接USB摄像头，将显示提示窗口")
        create_alert_window("摄像头检测", "未找到外接USB摄像头，将显示占位图像")
    
    # 如果所有摄像头都不可用，则提示用户但继续运行
    if not rs_depth_frame_available and not rs_color_frame_available and not usb_cam_available:
        create_alert_window("摄像头检测", "所有摄像头均不可用，将显示占位图像")
    
    # 创建窗口
    cv2.namedWindow('USB摄像头 (彩色)', cv2.WINDOW_AUTOSIZE)
    cv2.namedWindow('RealSense D405 (彩色)', cv2.WINDOW_AUTOSIZE)
    cv2.namedWindow('RealSense D405 (深度)', cv2.WINDOW_AUTOSIZE)
    
    # 设置窗口位置，使其整齐排列
    # 假设每个窗口宽度为640，高度为480
    window_width = 640
    window_height = 480
    margin = 30  # 窗口之间的间距
    
    # 水平排列三个窗口
    cv2.moveWindow('USB摄像头 (彩色)', 100, 100)  # 第一个窗口位于左上角
    cv2.moveWindow('RealSense D405 (彩色)', window_width + margin + 100, 100)  # 第二个窗口位于第一个窗口右侧
    cv2.moveWindow('RealSense D405 (深度)', ((window_width + margin) * 2)+100, 130)  # 第三个窗口位于第二个窗口右侧
    
    # 创建深度图像的颜色映射对象（如果RealSense可用）
    colorizer = rs.colorizer() if rs_depth_frame_available else None
    
    # 创建占位图像
    usb_placeholder = create_placeholder_image(window_width, window_height, "The USB camera is not connected")
    rs_color_placeholder = create_placeholder_image(window_width, window_height, "The RealSense color camera is not connected")
    rs_depth_placeholder = create_placeholder_image(window_width, window_height, "The RealSense depth camera is not connected")
    
    # 显示操作提示
    print("按ESC键或空格键退出程序")
    print("窗口已整齐排列在屏幕上")
    
    # 初始化FPS计算变量
    usb_fps_start_time = time.time()
    rs_color_fps_start_time = time.time()
    rs_depth_fps_start_time = time.time()
    usb_frame_count = 0
    rs_color_frame_count = 0
    rs_depth_frame_count = 0
    usb_fps = 0
    rs_color_fps = 0
    rs_depth_fps = 0
    
    try:
        while True:
            # 初始化图像变量
            rs_depth_image = rs_depth_placeholder
            rs_color_image = rs_color_placeholder
            usb_color_image = usb_placeholder
            
            # 获取RealSense帧（如果可用）
            if rs_pipeline is not None and (rs_depth_frame_available or rs_color_frame_available):
                try:
                    rs_frames = rs_pipeline.wait_for_frames(200)  # 设置超时时间为200ms
                    
                    if rs_depth_frame_available:
                        rs_depth_frame = rs_frames.get_depth_frame()
                        if rs_depth_frame:
                            # 将RealSense深度帧转换为numpy数组
                            rs_depth_image = np.asanyarray(colorizer.colorize(rs_depth_frame).get_data())
                            
                            # 计算RealSense深度摄像头FPS
                            rs_depth_frame_count += 1
                            if (time.time() - rs_depth_fps_start_time) > 1.0:  # 每秒更新一次FPS
                                rs_depth_fps = rs_depth_frame_count / (time.time() - rs_depth_fps_start_time)
                                rs_depth_frame_count = 0
                                rs_depth_fps_start_time = time.time()
                            
                            # 在RealSense深度图像上显示FPS
                            font = cv2.FONT_HERSHEY_SIMPLEX
                            font_scale = 0.7
                            font_color = (0, 255, 0)  # 绿色
                            font_thickness = 2
                            fps_text = f"FPS: {rs_depth_fps:.1f}"
                            cv2.putText(rs_depth_image, fps_text, (10, 30), font, font_scale, font_color, font_thickness)
                    
                    if rs_color_frame_available:
                        rs_color_frame = rs_frames.get_color_frame()
                        if rs_color_frame:
                            # 将RealSense彩色帧转换为numpy数组
                            rs_color_image = np.asanyarray(rs_color_frame.get_data())
                            
                            # 计算RealSense彩色摄像头FPS
                            rs_color_frame_count += 1
                            if (time.time() - rs_color_fps_start_time) > 1.0:  # 每秒更新一次FPS
                                rs_color_fps = rs_color_frame_count / (time.time() - rs_color_fps_start_time)
                                rs_color_frame_count = 0
                                rs_color_fps_start_time = time.time()
                            
                            # 在RealSense彩色图像上显示FPS
                            font = cv2.FONT_HERSHEY_SIMPLEX
                            font_scale = 0.7
                            font_color = (0, 255, 0)  # 绿色
                            font_thickness = 2
                            fps_text = f"FPS: {rs_color_fps:.1f}"
                            cv2.putText(rs_color_image, fps_text, (10, 30), font, font_scale, font_color, font_thickness)
                except Exception as e:
                    print(f"获取RealSense帧时出错: {e}")
            
            # 获取USB摄像头帧（如果可用）
            if usb_cam is not None and usb_cam_available:
                try:
                    ret, frame = usb_cam.read()
                    if ret:
                        usb_color_image = frame
                        
                        # 计算USB摄像头FPS
                        usb_frame_count += 1
                        if (time.time() - usb_fps_start_time) > 1.0:  # 每秒更新一次FPS
                            usb_fps = usb_frame_count / (time.time() - usb_fps_start_time)
                            usb_frame_count = 0
                            usb_fps_start_time = time.time()
                        
                        # 在USB摄像头图像上显示FPS
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        font_scale = 0.7
                        font_color = (0, 255, 0)  # 绿色
                        font_thickness = 2
                        fps_text = f"FPS: {usb_fps:.1f}"
                        cv2.putText(usb_color_image, fps_text, (10, 30), font, font_scale, font_color, font_thickness)
                except Exception as e:
                    print(f"获取USB摄像头帧时出错: {e}")
            
            # 显示图像
            cv2.imshow('USB摄像头 (彩色)', usb_color_image)
            cv2.imshow('RealSense D405 (彩色)', rs_color_image)
            cv2.imshow('RealSense D405 (深度)', rs_depth_image)
            
            # 检测按键 - 按ESC键或空格键退出
            key = cv2.waitKey(1)
            if key == 27 or key == 32:  # ESC键(27)或空格键(32)
                print("检测到退出按键，正在关闭程序...")
                break
    
    except Exception as e:
        print(f"运行时错误: {e}")
    
    finally:
        # 释放资源
        if usb_cam is not None:
            usb_cam.release()
        if rs_pipeline is not None:
            rs_pipeline.stop()
        cv2.destroyAllWindows()
        print("已关闭所有摄像头和窗口")

if __name__ == "__main__":
    main()
