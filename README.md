# ubuntu-desktop
## 背景

工厂测试人员用ubuntu系统去测试realsense相机是否正常显示，需要使用到realsense-viewer，而一般开发人员使用它的时候的操作步骤是：

1. 安装realsense sdk
2. 打开终端
3. 在终端输入`realsense-viewer`
   

即可打开Intel Realsense Viewer界面。

那这步骤对于测试人员来说太麻烦了，他们熟悉使用应用程序打开某个应用，有没有什么办法能在ubuntu上创建桌面快捷方式？

肯定有的，以下是具体操作步骤：

#### **步骤 1：确定 `realsense-viewer` 的路径**

在终端运行以下命令，确认 `realsense-viewer` 的安装位置：

```bash
which realsense-viewer
```

通常会输出类似 `/usr/local/bin/realsense-viewer` 的路径，记下它。

#### **步骤 2：创建 `.desktop` 文件**

1. 打开终端，运行以下命令创建并编辑 `.desktop` 文件：

   ```bash
   nano ~/桌面/realsense-viewer.desktop
   ```

2. 粘贴以下内容（根据实际情况调整 `Exec` 和 `Icon`）：

   ```ini
   [Desktop Entry]
   Version=1.0
   Type=Application
   Name=RealSense Viewer
   Comment=Intel RealSense Depth Camera Viewer
   Exec=/usr/local/bin/realsense-viewer
   Icon=camera  # 可选：使用系统图标，或指定自定义图标路径（如 /path/to/icon.png）
   Terminal=false  #可选：是否调出终端
   Categories=Utility;Development;
   ```

   - 如果 `realsense-viewer` 的路径不同，修改 `Exec=` 后的路径。
   - 如果需要自定义图标，将 `Icon=` 替换为图标的绝对路径（如 `Icon=/home/username/Pictures/realsense-icon.png`）。

3. 按 `Ctrl+O` 保存，`Ctrl+X` 退出 nano。

#### **步骤 3：赋予可执行权限**

```
chmod +x ~/桌面/realsense-viewer.desktop
```

#### **步骤 4：添加到桌面或应用程序菜单**

- **添加到桌面**：
  将文件复制到桌面右键.desktop文件点击【允许启动】，此时.desktop文件就会变成icon图标

### **验证**

- 双击桌面图标或在应用菜单中点击 **RealSense Viewer**，应该能直接启动。

### 加载rqt_image_view的方法

只需将文件中的`Exec`项改成：

```bash
Exec=bash -c "source /opt/ros/noetic/setup.bash && rqt_image_view"
```

即可。

**1. `bash -c` 的基本作用**

- **`bash`**：调用 Bash 解释器（Ubuntu 的默认 Shell）。

- **`-c`**：表示后面跟着一段要执行的命令字符串。

- **完整格式**：

  ```bash
  bash -c "你的命令"
  ```

  例如：

  ```bash
  bash -c "echo Hello World"
  ```

  会输出 `Hello World`。

**2. 为什么在 `.desktop` 文件中使用 `bash -c`？**

在 `.desktop` 文件的 `Exec=` 行中，直接写复杂命令（尤其是需要环境变量或逻辑操作时）可能会失效。
使用 `bash -c` 可以：

1. **解决环境变量问题**
   例如 ROS 工具（如 `rqt_image_view`）需要先加载 ROS 环境变量（`source /opt/ros/noetic/setup.bash`），但 `.desktop` 文件默认不继承终端的环境变量。

   ```ini
   Exec=bash -c "source /opt/ros/noetic/setup.bash && rqt_image_view"
   ```

   - 这里 `&&` 表示前一条命令成功后再执行后一条命令。

2. **支持复杂命令**
   可以组合多个命令，例如：

   ```ini
   Exec=bash -c "cd /path/to/dir && ./script.sh"
   ```

### 加载 python3 代码的方法
在终端查询 python3 的路径：
```bash
which python3
```
得到路径后将其替换到 `Exec=` 中：
```ini
Exec=/usr/bin/python3 /home/ppn/camera_test/camera_display.py
```


------

### **注意事项**

1. **图标问题**：
   - 如果 `Icon=camera` 不生效，可以下载一个 RealSense 图标（如 [官方图标](https://github.com/IntelRealSense/librealsense)），然后指定绝对路径（如 `Icon=/home/username/Downloads/realsense-icon.png`）。
2. **终端启动**：
   - 如果仍需调试，可将 `Terminal=false` 改为 `Terminal=true`，启动时会显示终端输出。

------

完成后，你就可以像普通应用一样通过点击图标启动 RealSense Viewer 了！

## 附录-系统自带图标列表

以下是系统自带的常用图标，可以在.desktop文件的`Icon=`字段中直接使用。

### 应用程序图标

|      图标名称      |        描述         |
| :----------------: | :-----------------: |
|   google-chrome    | Google Chrome浏览器 |
|        gvim        |   GVim文本编辑器    |
|       xterm        |     终端模拟器      |
|     mini.xterm     |      迷你终端       |
| com.gexperts.Tilix |   Tilix终端模拟器   |
|      openbox       |  Openbox窗口管理器  |
|      computer      |     计算机/系统     |

### 设备和硬件图标

|       图标名称        |      描述      |
| :-------------------: | :------------: |
|     camera-photo      |  相机/摄像头   |
|      audio-card       | 声卡/音频设备  |
|   audio-headphones    |      耳机      |
|    audio-speakers     |     扬声器     |
|        battery        |      电池      |
|       computer        |     计算机     |
|    drive-harddisk     |   硬盘驱动器   |
|     drive-optical     |   光盘驱动器   |
| drive-removable-media | 可移动存储设备 |
|    input-keyboard     |      键盘      |
|      input-mouse      |      鼠标      |
|     input-tablet      |     数位板     |
|     media-optical     |      光盘      |
|      media-flash      |    闪存设备    |
|     network-wired     |    有线网络    |
|   network-wireless    |    无线网络    |
|         phone         |      电话      |
|        printer        |     打印机     |
|        scanner        |     扫描仪     |
|     video-display     |     显示器     |

### 文件和文件夹图标

|       图标名称        |     描述     |
| :-------------------: | :----------: |
|        folder         |    文件夹    |
|   folder-documents    |  文档文件夹  |
|    folder-download    |  下载文件夹  |
|     folder-music      |  音乐文件夹  |
|    folder-pictures    |  图片文件夹  |
|     folder-videos     |  视频文件夹  |
|     user-desktop      |  桌面文件夹  |
|       user-home       |    主目录    |
|      user-trash       |    垃圾桶    |
|    text-x-generic     | 通用文本文件 |
|    image-x-generic    | 通用图像文件 |
|    video-x-generic    | 通用视频文件 |
|    audio-x-generic    | 通用音频文件 |
|   package-x-generic   |  通用包文件  |
|   x-office-document   |   办公文档   |
| x-office-spreadsheet  |   电子表格   |
| x-office-presentation |   演示文稿   |

### 状态和通知图标

|         图标名称          |     描述     |
| :-----------------------: | :----------: |
|    dialog-information     |  信息对话框  |
|      dialog-warning       |  警告对话框  |
|       dialog-error        |  错误对话框  |
|      dialog-question      |  问题对话框  |
|      dialog-password      |  密码对话框  |
|       network-error       |   网络错误   |
|       network-idle        |   网络空闲   |
|      network-offline      |   网络离线   |
|     network-transmit      |   网络发送   |
|      network-receive      |   网络接收   |
| network-transmit-receive  | 网络发送接收 |
|       security-high       |   高安全性   |
|      security-medium      |  中等安全性  |
|       security-low        |   低安全性   |
| software-update-available | 软件更新可用 |
|  software-update-urgent   | 紧急软件更新 |

### 网络和连接图标

|             图标名称              |     描述     |
| :-------------------------------: | :----------: |
|           network-wired           |   有线网络   |
|         network-wireless          |   无线网络   |
|            network-vpn            |   VPN连接    |
|        network-cellular-2g        |  2G蜂窝网络  |
|        network-cellular-3g        |  3G蜂窝网络  |
|        network-cellular-4g        |  4G蜂窝网络  |
|        network-cellular-5g        |  5G蜂窝网络  |
| network-wireless-signal-excellent | 无线信号极好 |
|   network-wireless-signal-good    | 无线信号良好 |
|    network-wireless-signal-ok     | 无线信号一般 |
|   network-wireless-signal-weak    |  无线信号弱  |
|   network-wireless-signal-none    |  无无线信号  |

### 天气图标

|         图标名称          |     描述     |
| :-----------------------: | :----------: |
|       weather-clear       |     晴天     |
|    weather-clear-night    |   晴朗夜晚   |
|    weather-few-clouds     |     少云     |
| weather-few-clouds-night  |   夜间少云   |
|        weather-fog        |      雾      |
|     weather-overcast      |     阴天     |
|   weather-severe-alert    | 恶劣天气警报 |
|      weather-showers      |     阵雨     |
| weather-showers-scattered |   零星阵雨   |
|       weather-snow        |      雪      |
|       weather-storm       |    暴风雨    |
|       weather-windy       |     大风     |

### 媒体控制图标

|        图标名称        |     描述     |
| :--------------------: | :----------: |
|  media-playback-start  |     播放     |
|  media-playback-pause  |     暂停     |
|  media-playback-stop   |     停止     |
|   media-skip-forward   |     快进     |
|  media-skip-backward   |     快退     |
|      media-record      |     录制     |
|      media-eject       |     弹出     |
| media-playlist-repeat  | 重复播放列表 |
| media-playlist-shuffle |   随机播放   |
|   audio-volume-high    |    高音量    |
|  audio-volume-medium   |   中等音量   |
|    audio-volume-low    |    低音量    |
|   audio-volume-muted   |     静音     |

### 系统操作图标

|             图标名称              |       描述       |
| :-------------------------------: | :--------------: |
|            system-run             |       运行       |
|           system-search           |       搜索       |
|            system-help            |       帮助       |
|          system-log-out           |       注销       |
|          system-shutdown          |       关机       |
|           system-reboot           |       重启       |
|        system-lock-screen         |       锁屏       |
|           system-users            |       用户       |
|      system-software-install      |     软件安装     |
|      system-software-update       |     软件更新     |
|        preferences-system         |   系统偏好设置   |
|        preferences-desktop        |   桌面偏好设置   |
|   preferences-desktop-keyboard    |   键盘偏好设置   |
|    preferences-desktop-display    |   显示偏好设置   |
|     preferences-desktop-theme     |   主题偏好设置   |
| preferences-desktop-accessibility | 辅助功能偏好设置 |

### 编辑操作图标

|         图标名称          |   描述   |
| :-----------------------: | :------: |
|         edit-cut          |   剪切   |
|         edit-copy         |   复制   |
|        edit-paste         |   粘贴   |
|        edit-delete        |   删除   |
|        edit-clear         |   清除   |
|         edit-find         |   查找   |
|     edit-find-replace     | 查找替换 |
|         edit-redo         |   重做   |
|         edit-undo         |   撤销   |
|     format-text-bold      |   粗体   |
|    format-text-italic     |   斜体   |
|   format-text-underline   |  下划线  |
| format-text-strikethrough |  删除线  |
|    format-justify-left    |  左对齐  |
|   format-justify-center   | 居中对齐 |
|   format-justify-right    |  右对齐  |
|    format-justify-fill    | 两端对齐 |

### 窗口控制图标

|       图标名称       |    描述    |
| :------------------: | :--------: |
|     window-close     |  关闭窗口  |
|   window-maximize    | 最大化窗口 |
|   window-minimize    | 最小化窗口 |
|    window-restore    |  还原窗口  |
|      window-new      |   新窗口   |
|   view-fullscreen    |  全屏查看  |
|     view-restore     |  还原视图  |
|     view-refresh     |  刷新视图  |
| view-sort-ascending  |  升序排序  |
| view-sort-descending |  降序排序  |

### 用户状态图标

|    图标名称    |   描述   |
| :------------: | :------: |
| user-available | 用户在线 |
|   user-away    | 用户离开 |
|   user-busy    | 用户忙碌 |
|   user-idle    | 用户空闲 |
| user-invisible | 用户隐身 |
|  user-offline  | 用户离线 |

### 注意事项

1. 这些图标名称可以直接在.desktop文件的`Icon=`字段中使用，无需指定完整路径。
2. 系统会根据当前主题自动选择合适的图标。
3. 如果某个图标名称在当前主题中不可用，系统会尝试使用备用图标。
4. 某些图标可能在不同的Linux发行版中有所不同。
5. 除了上述图标外，您还可以使用完整路径指定自定义图标，例如：`Icon=/path/to/your/icon.png`。
