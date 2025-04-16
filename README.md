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

