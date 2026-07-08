# Invisible Network

这是一个面向 Python 的计算机视觉原型项目，目标是通过摄像头采集多人姿态数据，并为后续的人际关系建模预留接口。

## 当前阶段

已完成第一阶段：多人姿态数据采集模块。

### 功能

- 调用电脑摄像头进行实时视频输入
- 检测画面中的多人（目标 3-5 人）
- 提取人体关键点：nose、肩膀、手肘、手腕、髋部、膝盖、脚踝
- 在当前环境中若 MediaPipe 不可用，会自动回退到 OpenCV 的轻量检测逻辑，保证原型可运行
- 为每个人生成稳定 ID
- 计算基础行为特征：position、orientation、velocity
- 将每一帧数据保存为 JSON，便于后续关系模型开发

## 项目结构

InvisibleNetwork/
├── main.py
├── camera.py
├── pose_detection.py
├── tracking.py
├── data_logger.py
└── README.md

## 依赖安装

```bash
pip install opencv-python mediapipe numpy
```

## 运行方式

```bash
python main.py
```

### 可选参数

```bash
python main.py --camera-index 0 --output output/pose_data.json
```

- `--camera-index`：指定摄像头编号
- `--output`：指定输出 JSON 文件路径
- `--no-display`：只采集数据，不显示窗口

## 说明

当前版本只实现数据采集与结构化存储，后续将继续扩展连接关系计算与可视化模块。
