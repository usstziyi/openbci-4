# OpenBCI Cyton 开源脑机设备系统化学习计划

> 基于 [OpenBCI 官方文档](https://docs.openbci.com/) 和 [GitHub 官方仓库](https://github.com/OpenBCI) 编制  
> 适用人群：具备基础 Python 编程能力和神经科学基础知识的学习者  
> 版本：v1.0 | 更新日期：2026-05-07

---

## 一、总体概述

### 1.1 什么是 OpenBCI Cyton

OpenBCI Cyton 是一款开源的 8 通道生物传感采集板，核心组件包括：

| 组件 | 说明 |
|------|------|
| **ADS1299 模拟前端 (AFE)** | 8 通道、24 位分辨率、可编程增益（1/2/4/6/8/12/24）、默认采样率 250 SPS |
| **PIC32MX250F128B 微控制器** | 搭载 chipKIT UDB32-MX2-DIP bootloader，运行 v3.0.0+ 固件 |
| **LIS3DH 三轴加速度计** | 用于检测头部运动伪迹 |
| **RFDuino BLE 无线电模块** | 基于 Nordic Gazelle 协议栈，通过 USB Dongle 与 PC 连接 |
| **Micro SD 卡槽** | 支持离线数据记录（最大 32GB） |
| **Daisy 扩展模块（可选）** | 额外增加 8 通道，扩展到 16 通道 |

### 1.2 应用场景

- **EEG（脑电图）**：α 波（8-13 Hz）、β 波（13-30 Hz）、视觉诱发电位（VEP）、P300 等
- **EMG（肌电图）**：肌肉活动模式识别、手势识别
- **ECG（心电）**：心率变异性（HRV）分析
- **EOG（眼电）**：眼动追踪、眨眼检测
- **BCI（脑机接口）**：运动想象（Motor Imagery）、稳态视觉诱发电位（SSVEP）

### 1.3 学习路径图

```
Unit 1: 设备基础与理论
  └── 硬件架构、信号生物物理学、10-20 系统
        │
        ▼
Unit 2: 连接与数据流
  └── USB Dongle、串口通信、SDK 命令协议
        │
        ▼
Unit 3: 信号处理基础
  └── 滤波、伪迹去除、频谱分析、时频分析
        │
        ▼
Unit 4: EEG 信号分析
  └── 频带功率、ERD/ERS、连通性、特征提取
        │
        ▼
Unit 5: BCI 应用实战
  └── 运动想象分类、SSVEP 检测、实时反馈
        │
        ▼
Unit 6: 高级专题
  └── Daisy 16 通道、SD 卡记录、固件编程
```

---

## 二、学习单元划分

### Unit 1 · 设备基础与生物电信号理论
| 维度 | 内容 |
|------|------|
| **学习目标** | 理解 Cyton 硬件架构、ADS1299 工作原理、EEG/EMG/ECG 信号生物学起源 |
| **核心概念** | 模拟前端 (AFE)、ADC 分辨率、共模抑制比 (CMRR)、电极-皮肤界面 |
| **关键技术** | 10-20 国际电极放置系统、参考电极选择（双极/单极）、阻抗匹配 |
| **Jupyter Notebook** | `unit_01_foundations.ipynb` |

### Unit 2 · 设备连接与数据流控制
| 维度 | 内容 |
|------|------|
| **学习目标** | 掌握 USB Dongle 驱动安装、串口识别、SDK 命令协议、实时数据读取 |
| **核心概念** | 虚拟串口 (VCP)、字节流协议、33 字节数据包结构、采样计数器 |
| **关键技术** | `brainflow` / `pyOpenBCI` 库的使用、通道配置命令（`x` 命令）、流启停 |
| **Jupyter Notebook** | `unit_02_connection.ipynb` |

### Unit 3 · 生物电信号处理基础
| 维度 | 内容 |
|------|------|
| **学习目标** | 理解并实践数字滤波器设计、伪迹检测与去除、频谱和时频分析方法 |
| **核心概念** | 巴特沃斯/切比雪夫滤波器、陷波滤波器（50/60 Hz）、ICA/PCA、STFT |
| **关键技术** | `scipy.signal` 滤波器设计、`mne` 预处理管线、Welch 功率谱估计 |
| **Jupyter Notebook** | `unit_03_signal_processing.ipynb` |

### Unit 4 · EEG 信号特征提取与分析
| 维度 | 内容 |
|------|------|
| **学习目标** | 从 EEG 信号中提取有意义的生物标记物并进行统计和可视化分析 |
| **核心概念** | 频带功率（δ/θ/α/β/γ）、事件相关去同步/同步 (ERD/ERS)、相干性 |
| **关键技术** | 带通滤波 + 希尔伯特变换、CSP (Common Spatial Patterns)、PSD 地形图 |
| **Jupyter Notebook** | `unit_04_eeg_analysis.ipynb` |

### Unit 5 · BCI 范式实战
| 维度 | 内容 |
|------|------|
| **学习目标** | 实现运动想象 (MI) 和 SSVEP 两种经典 BCI 范式的离线与在线分类 |
| **核心概念** | 感觉运动节律 (SMR)、C3/C4 电极、CCA 频率检测、分类器训练 |
| **关键技术** | CSP + LDA/SVM 分类管线、CCA 频率识别、实时反馈环路设计 |
| **Jupyter Notebook** | `unit_05_bci_applications.ipynb` |

### Unit 6 · 高级专题与系统集成
| 维度 | 内容 |
|------|------|
| **学习目标** | 掌握 Daisy 16 通道配置、Micro SD 离线记录、固件更新与自定义编程 |
| **核心概念** | 通道扩展、FAT32 文件系统、Arduino IDE 工具链、chipKIT bootloader |
| **关键技术** | Daisy 模块 `C` 命令、SD 卡 `A/S/F/G/H/J` 命令集、PIC32 编程流程 |
| **Jupyter Notebook** | `unit_06_advanced_topics.ipynb` |

---

## 三、环境依赖说明

### 3.1 Python 环境推荐配置

**推荐 Python 版本：** Python 3.9 - 3.11（已验证兼容性）

**使用 Conda（推荐）：**

```bash
# 创建环境
conda create -n openbci python=3.10
conda activate openbci

# 安装核心依赖
pip install -r requirements.txt
```

**使用 venv：**

```bash
python -m venv openbci_env
source openbci_env/bin/activate  # Linux/macOS
# openbci_env\Scripts\activate   # Windows
pip install -r requirements.txt
```

### 3.2 依赖库版本清单

| 库 | 版本 | 用途 | 必需？ |
|----|------|------|--------|
| `numpy` | ≥1.24.0 | 数值计算基础 | ✅ |
| `scipy` | ≥1.11.0 | 信号处理（滤波器、FFT） | ✅ |
| `matplotlib` | ≥3.7.0 | 数据可视化 | ✅ |
| `jupyter` | ≥1.0.0 | Notebook 运行环境 | ✅ |
| `brainflow` | ≥5.8.0 | OpenBCI 官方推荐的数据采集 SDK | ✅ |
| `mne` | ≥1.5.0 | EEG/MEG 高级分析 | ✅ |
| `scikit-learn` | ≥1.3.0 | 机器学习分类器 | ✅ |
| `pandas` | ≥2.0.0 | 数据管理与统计分析 | ✅ |
| `seaborn` | ≥0.12.0 | 统计可视化 | ❌ |
| `pyOpenBCI` | ≥1.0.0 | OpenBCI 社区 Python 库（备选） | ❌ |
| `pyserial` | ≥3.5 | 底层串口通信 | ❌ |

### 3.3 OpenBCI Cyton 设备前置配置步骤

1. **硬件准备：**
   - OpenBCI Cyton 主板 ×1
   - RFDuino USB Dongle ×1
   - 电池盒（3×AA 或 1×锂聚合物电池） ×1
   - 电极（湿电极/干电极） ×N
   - 电极线缆 ×N
   - （可选）Daisy 扩展模块 ×1
   - （可选）Micro SD 卡（≤32GB，FAT32 格式） ×1

2. **驱动安装：**
   - **Windows：** 插入 Dongle 后自动安装 FTDI VCP 驱动；如失败，访问 [FTDI VCP Drivers](https://ftdichip.com/drivers/vcp-drivers/)
   - **macOS：** 系统自带 FTDI 驱动，无需额外安装
   - **Linux：** 内核已内置 `ftdi_sio` 驱动模块，需确保当前用户有串口权限：
     ```bash
     sudo usermod -a -G dialout $USER
     # 注销后重新登录生效
     ```

3. **Dongle 配对（v3.0.0+ 固件）：**
   - Cyton 上电后蓝色 LED 闪烁（广播模式）
   - 插入 USB Dongle，Dongle 自动切换至 `Host` 模式
   - 配对成功后 Dongle 蓝色 LED 常亮
   - 配对仅在首次使用时需要，后续自动重连

4. **验证连接：**
   ```bash
   # 查看串口设备
   # Linux:   ls /dev/ttyUSB*
   # macOS:   ls /dev/tty.usbserial*
   # Windows: 设备管理器 → 端口(COM和LPT)
   ```

5. **安装 OpenBCI GUI（可选验证工具）：**
   - 从 [OpenBCI GUI Releases](https://github.com/OpenBCI/OpenBCI_GUI/releases) 下载对应平台版本
   - 启动 GUI 验证数据流正常

---

## 四、项目文件结构

```
openbci_cyton_learning/
├── README.md                         # 本文件：总体学习计划
├── requirements.txt                  # Python 依赖清单
├── environment.yml                   # Conda 环境配置
├── notebooks/                        # Jupyter Notebook 学习单元
│   ├── unit_01_foundations.ipynb     # Unit 1: 设备基础与理论
│   ├── unit_02_connection.ipynb      # Unit 2: 连接与数据流
│   ├── unit_03_signal_processing.ipynb  # Unit 3: 信号处理
│   ├── unit_04_eeg_analysis.ipynb    # Unit 4: EEG 分析
│   ├── unit_05_bci_applications.ipynb   # Unit 5: BCI 实战
│   └── unit_06_advanced_topics.ipynb # Unit 6: 高级专题
├── utils/
│   └── helpers.py                    # 共享工具函数
├── data/                             # 示例数据存放目录
└── review.md                         # 单元审查与优化建议
```

---

## 五、学习建议

1. **循序渐进：** 严格按照 Unit 1→6 的顺序学习，每个 Unit 内容依赖前一单元
2. **动手实践：** 每个 Notebook 包含可执行代码，建议逐行运行并理解输出
3. **硬件验证：** Unit 2 起建议连接真实设备；无设备时可使用提供的模拟数据
4. **查阅官方文档：** 本文档仅作引导，遇到细节问题请参考 [docs.openbci.com](https://docs.openbci.com/)
5. **社区支持：** 遇到问题可访问 [OpenBCI Forum](https://openbci.com/forum/) 寻求帮助

---

## 参考资料

- [OpenBCI 官方文档](https://docs.openbci.com/)
- [OpenBCI GitHub 组织](https://github.com/OpenBCI)
- [OpenBCI Cyton 数据格式](https://docs.openbci.com/Cyton/CytonDataFormat/)
- [OpenBCI Cyton SDK](https://docs.openbci.com/Cyton/CytonSDK/)
- [BrainFlow 文档](https://brainflow.readthedocs.io/)
- [MNE-Python 文档](https://mne.tools/stable/)
