# 《留下的痕迹》/ The Trace We Leave

一个基于计算机视觉的交互艺术项目。

<img width="956" height="536" alt="屏幕截图 2026-07-10 033318" src="https://github.com/user-attachments/assets/8a6da7d5-7da8-4b67-ad7f-c3e862309fb6" />

<img width="959" height="540" alt="屏幕截图 2026-07-10 033345" src="https://github.com/user-attachments/assets/109f2244-169a-4909-8dad-e1a3b50f2cdd" />

<img width="953" height="530" alt="屏幕截图 2026-07-10 033405" src="https://github.com/user-attachments/assets/d5226c94-cf88-413e-bee4-9629f580b9f5" />

<img width="959" height="538" alt="屏幕截图 2026-07-10 033413" src="https://github.com/user-attachments/assets/31a3ccb4-e527-47df-a502-a6a50fcaf043" />


## 核心概念

人的行为会留下不可见的影响。

项目通过摄像头捕捉用户手部动作，将短暂的动作转化为数字痕迹，并观察这些痕迹如何影响屏幕中的另一个抽象存在。

**这不是情绪识别系统。** 不判断用户开心、悲伤等心理状态。

## 核心逻辑

```
用户动作 → 手部运动数据 → 行为轨迹 → 动作结束后形成数字痕迹 → 痕迹传播 → 影响目标对象
```

## 技术栈

- Python 3.8+
- OpenCV - 摄像头捕获
- MediaPipe Hands - 手部追踪
- Pygame - 视觉渲染

## 文件结构

| 文件 | 说明 |
|------|------|
| `main.py` | 程序入口，主循环 |
| `hand_tracking.py` | 手部追踪模块 |
| `trajectory.py` | 轨迹管理与痕迹生成 |
| `behavior_analysis.py` | 运动行为分析 |
| `particle_system.py` | 粒子视觉效果 |
| `target_object.py` | 目标对象（抽象存在） |
| `interaction.py` | 交互逻辑处理 |

## 安装与运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行项目
python main.py
```

## 使用说明

1. 确保摄像头可用
2. 运行程序后，将手放入摄像头视野
3. 挥手或移动手部创造轨迹
4. 停止移动，轨迹将转化为痕迹
5. 观察痕迹如何影响屏幕中的抽象存在

## 创作理念

每一次动作都是独特的，留下的痕迹也是独特的。
痕迹会扩散、衰减，但在消失前会影响周围的存在。

正如我们在世界上留下的影响——
看不见，但真实存在。
