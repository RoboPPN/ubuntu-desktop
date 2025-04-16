#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
摄像头显示脚本
同时显示外接USB摄像头的彩色图像、RealSense D405的深度图像和彩色图像
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
    
    # 创建深度图像的颜色映射对象
    colorizer = rs.colorizer()
    
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
            
            # 显示图像
            cv2.imshow('USB摄像头 (彩色)', usb_color_image)
            cv2.imshow('RealSense D405 (彩色)', rs_color_image)
            cv2.imshow('RealSense D405 (深度)', rs_depth_image)
            
            # 按ESC键退出
            key = cv2.waitKey(1)
            if key == 27:  # ESC键
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

