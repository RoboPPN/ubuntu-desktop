#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
摄像头显示脚本
同时显示外接USB摄像头的彩色图像、RealSense D405的深度图像和彩色图像
包含帧率(FPS)显示功能
窗口整齐排列功能
"""

import cv2
import numpy as np
import pyrealsense2 as rs
import time

def main():
    # 初始化RealSense D405摄像头
    rs_pipeline = rs.pipeline()
    rs_config = rs.config()
    
    # 尝试启用RealSense D405摄像头
    try:
        # 查找RealSense设备
        ctx = rs.context()
        devices = ctx.query_devices()
        if len(devices) == 0:
            print("未检测到RealSense设备，请检查连接")
            return
        
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
    except Exception as e:
        print(f"RealSense摄像头初始化失败: {e}")
        return
    
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
        print("未找到外接USB摄像头，请检查连接")
        rs_pipeline.stop()
        return
    
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
    
    # 创建深度图像的颜色映射对象
    colorizer = rs.colorizer()
    
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
            # 获取RealSense帧
            rs_frames = rs_pipeline.wait_for_frames()
            rs_depth_frame = rs_frames.get_depth_frame()
            rs_color_frame = rs_frames.get_color_frame()
            
            if not rs_depth_frame or not rs_color_frame:
                print("未能获取RealSense帧，重试中...")
                continue
            
            # 将RealSense帧转换为numpy数组
            rs_depth_image = np.asanyarray(colorizer.colorize(rs_depth_frame).get_data())
            rs_color_image = np.asanyarray(rs_color_frame.get_data())
            
            # 获取USB摄像头帧
            ret, usb_color_image = usb_cam.read()
            if not ret:
                print("未能获取USB摄像头帧，重试中...")
                continue
            
            # 计算USB摄像头FPS
            usb_frame_count += 1
            if (time.time() - usb_fps_start_time) > 1.0:  # 每秒更新一次FPS
                usb_fps = usb_frame_count / (time.time() - usb_fps_start_time)
                usb_frame_count = 0
                usb_fps_start_time = time.time()
            
            # 计算RealSense彩色摄像头FPS
            rs_color_frame_count += 1
            if (time.time() - rs_color_fps_start_time) > 1.0:  # 每秒更新一次FPS
                rs_color_fps = rs_color_frame_count / (time.time() - rs_color_fps_start_time)
                rs_color_frame_count = 0
                rs_color_fps_start_time = time.time()
            
            # 计算RealSense深度摄像头FPS
            rs_depth_frame_count += 1
            if (time.time() - rs_depth_fps_start_time) > 1.0:  # 每秒更新一次FPS
                rs_depth_fps = rs_depth_frame_count / (time.time() - rs_depth_fps_start_time)
                rs_depth_frame_count = 0
                rs_depth_fps_start_time = time.time()
            
            # 在图像上显示FPS
            # 设置文本参数
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.7
            font_color = (0, 255, 0)  # 绿色
            font_thickness = 2
            
            # 在USB摄像头图像上显示FPS
            fps_text = f"FPS: {usb_fps:.1f}"
            cv2.putText(usb_color_image, fps_text, (10, 30), font, font_scale, font_color, font_thickness)
            
            # 在RealSense彩色图像上显示FPS
            fps_text = f"FPS: {rs_color_fps:.1f}"
            cv2.putText(rs_color_image, fps_text, (10, 30), font, font_scale, font_color, font_thickness)
            
            # 在RealSense深度图像上显示FPS
            fps_text = f"FPS: {rs_depth_fps:.1f}"
            cv2.putText(rs_depth_image, fps_text, (10, 30), font, font_scale, font_color, font_thickness)
            
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
        rs_pipeline.stop()
        cv2.destroyAllWindows()
        print("已关闭所有摄像头和窗口")

if __name__ == "__main__":
    main()
