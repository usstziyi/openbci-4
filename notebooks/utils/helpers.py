"""
OpenBCI Cyton 学习计划 — 共享工具函数
========================================
本模块提供跨 Notebook 复用的工具函数，涵盖信号生成、数据格式解析、
可视化辅助和 BrainFlow 设备管理等功能。
"""

import numpy as np
# 从 scipy 库导入信号处理模块，用于数字滤波器设计和频谱分析
from scipy import signal as sp_signal
import matplotlib.pyplot as plt

# ============================================================
# 1. 模拟信号生成
# ============================================================

def generate_synthetic_eeg(
    duration=10.0, sfreq=250.0, n_channels=8,
    noise_level=5.0, alpha_power=30.0, seed=42
):
    """
    生成模拟多通道 EEG 数据，用于在无真实设备时测试分析管线。

    Parameters
    ----------
    duration : float
        信号时长（秒）
    sfreq : float
        采样率（Hz），Cyton 默认 250 SPS
    n_channels : int
        通道数，默认 8
    noise_level : float
        背景噪声标准差 (muV)
    alpha_power : float
        alpha 频段信号振幅 (muV)
    seed : int
        随机种子，保证可复现

    Returns
    -------
    data : ndarray, shape (n_channels, n_samples)
        模拟 EEG 数据（muV）
    times : ndarray, shape (n_samples,)
        时间向量（秒）
    """
    rng = np.random.default_rng(seed)
    n_samples = int(duration * sfreq)
    times = np.arange(n_samples) / sfreq

    # 1/f 背景噪声（粉红噪声）
    # 计算 FFT 频率轴（实数 FFT，仅非负频率）
    # rfftfreq 返回的 freqs 范围是 [0, sfreq/2]，长度为 n_samples//2 + 1
    freqs = np.fft.rfftfreq(n_samples, d=1.0 / sfreq)
    
    # 构建 1/f 频谱（粉红噪声特性）：功率谱密度与频率成反比
    # 公式：S(f) ∝ 1/√f，即幅度谱 ∝ 1/√f，功率谱 ∝ 1/f
    # 先将零频率分量替换为非零值，避免 np.where 参数预计算时出现除以零
    safe_freqs = np.where(freqs > 0, freqs, 1.0)  # freq=0 时用 1.0 替代
    pink_noise_spectrum = 1.0 / np.sqrt(safe_freqs)
    pink_noise_spectrum[0] = 0.0  # 显式将直流分量置零
    
    # 显式将直流分量（0 Hz）置零，确保无直流偏移
    # 虽然 np.where 已处理，但此处双重保险，避免数值精度问题
    pink_noise_spectrum[0] = 0.0

    data = np.zeros((n_channels, n_samples))
    for ch in range(n_channels):
        # 随机相位生成粉红噪声时域信号
        phase = rng.uniform(0, 2 * np.pi, len(freqs))
        spectrum = pink_noise_spectrum * np.exp(1j * phase) # 添加随机相位
        pink = np.fft.irfft(spectrum, n=n_samples) # 反 FFT 得到时域信号
        # 归一化到指定噪声水平
        pink = pink / np.std(pink) * noise_level

        # alpha 振荡 (8-13 Hz)，模拟后部电极 alpha 更强
        # 生成 alpha 频段正弦波（8-13 Hz），模拟后部电极 alpha 活动更强的生理特征
        alpha_freq = rng.uniform(8.5, 12.5)  # 随机选择 alpha 频率，增加信号自然性
        # 振幅随通道索引递增：通道号越大（对应后部电极），alpha 功率越强
        alpha_amp = alpha_power * (0.5 + 0.5 * (ch / n_channels))
        alpha = alpha_amp * np.sin(2 * np.pi * alpha_freq * times)

        # 50 Hz 工频干扰（中国标准）
        line_noise_amp = rng.uniform(0.5, 2.0)
        line_noise = 20 * np.sin(2 * np.pi * 50.0 * times)

        data[ch] = pink + alpha + line_noise

    return data, times


# ============================================================
# 2. Cyton 数据包解析
# ============================================================

def parse_cyton_packet(packet):
    """
    解析单个 OpenBCI Cyton 33 字节数据包（v3.0.0+ 固件）。

    数据包结构 (33 bytes):
        Byte 0:      Header (0xA0)
        Byte 1:      Sample Counter (0-255, circular)
        Byte 2-4:    Channel 1 data (MSB first, 24-bit signed)
        Byte 5-7:    Channel 2 data
        ...
        Byte 23-25:  Channel 8 data
        Byte 26-31:  Aux Data (Accelerometer: 3 axis x 2 bytes, MSB first)
        Byte 32:      Footer (0xC0)

    Parameters
    ----------
    packet : bytes
        33 字节的原始数据包

    Returns
    -------
    parsed : dict or None
        解析后的字典，包含 sample_number、channel_data、accel_data
    """
    if len(packet) != 33:
        return None
    if packet[0] != 0xA0 or packet[32] != 0xC0:
        return None

    sample_number = packet[1]

    # 通道数据：每个通道 3 字节，24 位有符号整数（二进制补码）
    channel_data = np.zeros(8, dtype=np.float64)
    for ch in range(8):
        offset = 2 + ch * 3
        raw = (packet[offset] << 16) | (packet[offset + 1] << 8) | packet[offset + 2]
        # 24 位有符号扩展
        if raw & 0x800000:
            raw = raw - 0x1000000
        # 转换为 muV：OpenBCI 官方标定值
        scale_factor = 0.02235  # muV/count
        channel_data[ch] = raw * scale_factor

    # 加速度计数据 (6 bytes)
    accel_data = np.zeros(3, dtype=np.int16)
    for axis in range(3):
        offset = 26 + axis * 2
        accel_data[axis] = (packet[offset] << 8) | packet[offset + 1]

    return {
        "sample_number": sample_number,
        "channel_data": channel_data,  # muV
        "accel_data": accel_data,       # raw counts
    }


# ============================================================
# 3. 数字滤波器设计
# ============================================================

def design_bandpass_filter(lowcut, highcut, sfreq=250.0, order=4):
    """
    设计巴特沃斯 带通滤波器系数。

    Parameters
    ----------
    lowcut : float
        低截止频率（Hz）
    highcut : float
        高截止频率（Hz）
    sfreq : float
        采样率（Hz）
    order : int
        滤波器阶数

    Returns
    -------
    b, a : ndarray
        IIR 滤波器系数
    """
    nyquist = 0.5 * sfreq
    low = lowcut / nyquist
    high = highcut / nyquist
    # order: 滤波器阶数，决定滤波器滚降陡度
    # [low, high]: 归一化截止频率，范围 [0, 1]，其中 1 对应奈奎斯特频率
    # btype="band": 滤波器类型为带通，保留 low 和 high 之间的频率成分
    b, a = sp_signal.butter(order, [low, high], btype="band")
    return b, a


def design_notch_filter(freq=50.0, sfreq=250.0, quality_factor=30.0):
    """
    设计 IIR 陷波滤波器（去除工频干扰）。

    Parameters
    ----------
    freq : float
        目标频率（Hz），50 Hz
    sfreq : float
        采样率（Hz）
    quality_factor : float
        品质因数，越大陷波越窄

    Returns
    -------
    b, a : ndarray
        IIR 滤波器系数
    """
    w0 = freq / (sfreq / 2.0)
    b, a = sp_signal.iirnotch(w0, quality_factor)
    return b, a


# ============================================================
# 4. 可视化辅助
# ============================================================

def plot_eeg_channels(data, times, sfreq=250.0, title="EEG Signals",
                      channel_names=None, figsize=(14, 8), ylim=(-100, 100)):
    """多通道 EEG 信号波形绘制。"""
    n_channels = data.shape[0]
    if channel_names is None:
        channel_names = [f"CH{i+1}" for i in range(n_channels)]

    fig, axes = plt.subplots(n_channels, 1, figsize=figsize, sharex=True)
    if n_channels == 1:
        axes = [axes]

    for i, ax in enumerate(axes):
        ax.plot(times, data[i], linewidth=0.5, color="steelblue")
        ax.set_ylabel(f"{channel_names[i]}\n(muV)", fontsize=8)
        ax.set_ylim(ylim)
        ax.grid(True, alpha=0.3)
        if i < n_channels - 1:
            ax.tick_params(labelbottom=False)

    axes[-1].set_xlabel("Time (s)")
    fig.suptitle(title, fontsize=12, fontweight="bold")
    plt.tight_layout()
    return fig


def plot_psd(data, sfreq=250.0, title="Power Spectral Density",
             channel_names=None, freq_range=(0.5, 80), figsize=(12, 6)):
    """多通道 PSD 绘制（对数坐标）。"""
    n_channels = data.shape[0]
    if channel_names is None:
        channel_names = [f"CH{i+1}" for i in range(n_channels)]

    colors = plt.cm.viridis(np.linspace(0, 1, n_channels))
    fig, ax = plt.subplots(figsize=figsize)

    for ch in range(n_channels):
        # 计算功率谱密度（PSD）：使用 Welch 方法
        freqs, psd = sp_signal.welch(
            data[ch],           # 输入信号：第 ch 个通道的时间序列数据
            fs=sfreq,           # 采样率：信号的采样频率（Hz），用于正确计算频率轴
            nperseg=int(sfreq * 2),  # 每段长度：每个窗的样本数，此处设为 2 秒数据（Welch 方法的分段长度）
            noverlap=int(sfreq)      # 重叠长度：相邻窗之间的重叠样本数，此处设为 1 秒（50% 重叠）
        )
        # 根据指定频率范围创建掩码，筛选有效频段数据
        mask = (freqs >= freq_range[0]) & (freqs <= freq_range[1])
        # 使用对数坐标绘制功率谱密度曲线，便于观察各频段能量分布
        ax.semilogy(
            freqs[mask], 
            psd[mask], 
            color=colors[ch],
            label=channel_names[ch], 
            linewidth=1.2
        )

    # 标注 EEG 频段
    bands = {"delta": (0.5, 4), "theta": (4, 8), "alpha": (8, 13),
             "beta": (13, 30), "gamma": (30, 80)}
    for name, (lo, hi) in bands.items():
        ax.axvspan(lo, hi, alpha=0.08, color="gray")
        ax.text((lo + hi) / 2, ax.get_ylim()[1] * 0.95, name,
                ha="center", fontsize=9, fontweight="bold", alpha=0.5)

    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("PSD (muV^2/Hz)")
    ax.set_title(title)
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig


# ============================================================
# 5. BrainFlow 设备管理
# ============================================================

def list_available_boards():
    """扫描并列出所有可用的 BrainFlow 兼容设备。"""
    try:
        from brainflow.board_shim import BoardShim
        boards = []
        for bid in [0, 2]:  # Cyton, Cyton+Daisy
            try:
                desc = BoardShim.get_board_descr(bid)
                boards.append({
                    "board_id": bid,
                    "name": desc.get("name", f"Board {bid}"),
                    "description": desc
                })
            except Exception:
                pass

        import serial.tools.list_ports
        serial_ports = [p.device for p in serial.tools.list_ports.comports()]
        for board in boards:
            board["available_ports"] = serial_ports
        return boards
    except ImportError:
        return [{"error": "brainflow not installed. Run: pip install brainflow"}]

def parse_and_print_desc(board_id):
    """
    获取并解析指定板卡的描述信息
    """
    try:
        import json
        from brainflow.board_shim import BoardShim
        # 1. 获取原始描述字典
        desc = BoardShim.get_board_descr(board_id)
        
        print(f"--- 📋 板卡 ID {board_id} 的详细描述 ---")
        # 如果是 OpenBCI Cyton，通常会返回类似下面的结构
        # 注意：不同版本的 brainflow 返回的具体字段可能略有差异
        
        # 2. 格式化输出 (模拟人类可读的解析)
        print(f"{'参数名称':<20} | {'值':<30} | {'说明'}")
        print("-" * 70)
        
        for key, value in desc.items():
            description = ""
            
            # 根据常见的 BrainFlow 字段进行语义解释
            if key == "accel_channels":
                description = "加速度计通道数"
            elif key == "analog_channels":
                description = "模拟通道数"
            elif key == "eeg_channels":
                description = "脑电通道数"
            elif key == "ecg_channels":
                description = "心电通道数"
            elif key == "eeg_names":
                description = "脑电通道名称"
            elif key == "emg_channels":
                description = "肌电通道数"
            elif key == "eog_channels":
                description = "眼动通道数"
            elif key == "marker_channel":
                description = "标记通道数"
            elif key == "name":
                description = "板卡名称"
            elif key == "num_rows":
                description = "数据矩阵的总列数"
            elif key == "other_channels":
                description = "保留通道数"
            elif key == "package_num_channel":
                description = "包序号通道索引"
            elif key == "sampling_rate":
                description = "采样率"
            elif key == "timestamp_channel":
                description = "时间戳通道索引"
            
            # 打印解析后的行
            print(f"{key:<23} | {str(value):<30} | {description}")
            
        print("-" * 70)
        
        # 3. 如果你需要将其作为 JSON 字符串用于日志记录
        json_str = json.dumps(desc, indent=4)
        return json_str
        # print("JSON 格式备份:\n", json_str) 
    except Exception as e:
        print(f"❌ 获取描述信息失败: {e}")
        return None



def create_cyton_board(serial_port="", board_id=0, daisy=False):
    """创建并返回 BrainFlow BoardShim 实例。"""
    try:
        from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
        params = BrainFlowInputParams()
        params.serial_port = serial_port
        if daisy:
            board_id = BoardIds.CYTON_DAISY_BOARD.value
        elif board_id == 0:
            board_id = BoardIds.CYTON_BOARD.value
        board = BoardShim(board_id, params)
        return board
    except ImportError:
        print("Error: brainflow not installed.")
        return None
    except Exception as e:
        print(f"Error creating board: {e}")
        return None


# ============================================================
# 6. 频带功率计算
# ============================================================

def compute_band_powers(data, sfreq=250.0, bands=None):
    """
    计算 EEG 信号在指定频段内的绝对功率和相对功率。

    Parameters
    ----------
    data : np.ndarray
        EEG 数据。
        形状可以是：
        - (n_samples,)
        - (n_channels, n_samples)

    sfreq : float
        采样率，单位 Hz。

    bands : dict
        频段定义，例如：
        {
            "delta": (0.5, 4),
            "theta": (4, 8),
            ...
        }

    Returns
    -------
    results : dict
        每个频段的绝对功率和相对功率。
    """
    if bands is None:
        bands = {
            "delta": (0.5, 4), 
            "theta": (4, 8), 
            "alpha": (8, 13),
            "beta": (13, 30), 
            "gamma": (30, 45),
        }
    # 如果是单通道信号，转成二维：(1, n_samples)
    if data.ndim == 1:
        data = data[np.newaxis, :]
    freqs, psd_all = sp_signal.welch(
        data,           # 输入信号：多通道 EEG 数据，形状为 (n_channels, n_samples)
        fs=sfreq,       # 采样率：信号的采样频率（Hz），用于正确计算频率轴
        axis=-1,        # 计算 PSD 的轴：-1 表示沿最后一个轴（时间轴）计算
        nperseg=int(sfreq * 2),  # 每段长度：每个窗的样本数，此处设为 2 秒数据（Welch 方法的分段长度）
    )
    # freqs : (n_freqs,) n_freqs = nperseg // 2 + 1
    # psd_all : (n_channels, n_freqs)



    # 先对所有通道求平均 PSD
    mean_psd = psd_all.mean(axis=0)
    # mean_psd : (n_freqs,)

    # 总功率：对整个频率范围积分
    total_power = np.trapezoid(mean_psd, freqs)

    if total_power == 0:
        total_power = 1.0

    results = {}

    for name, (lo, hi) in bands.items():
        mask = (freqs >= lo) & (freqs <= hi)

        if not np.any(mask):
            band_power = 0.0
        else:
            # 使用梯形法对频段内的 PSD 进行数值积分，得到该频段的绝对功率
            band_power = np.trapezoid(mean_psd[mask], freqs[mask])

        results[name] = {
            "absolute": band_power,
            "relative": band_power / total_power,
        }

    return results


# ============================================================
# 7. 常量: 10-20 系统通道映射
# ============================================================

CYTON_8CH_1020_MAP = {
    1: "Fp1", 2: "Fp2", 3: "C3", 4: "C4",
    5: "P7",  6: "P8",  7: "O1", 8: "O2",
}

DAISY_8CH_1020_MAP = {
    9: "Fz", 10: "Cz", 11: "Pz", 12: "Oz",
    13: "F3", 14: "F4", 15: "T7", 16: "T8",
}

BAND_COLORS = {
    "delta": "#1f77b4", "theta": "#ff7f0e", "alpha": "#2ca02c",
    "beta": "#d62728", "gamma": "#9467bd",
}
