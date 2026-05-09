"""
OpenBCI Cyton 学习计划 — 共享工具函数
========================================
本模块提供跨 Notebook 复用的工具函数，涵盖信号生成、数据格式解析、
可视化辅助和 BrainFlow 设备管理等功能。
"""

import numpy as np
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
    freqs = np.fft.rfftfreq(n_samples, d=1.0 / sfreq)
    pink_noise_spectrum = np.where(freqs > 0, 1.0 / np.sqrt(freqs), 0.0)
    pink_noise_spectrum[0] = 0.0

    data = np.zeros((n_channels, n_samples))
    for ch in range(n_channels):
        # 随机相位生成粉红噪声时域信号
        phase = rng.uniform(0, 2 * np.pi, len(freqs))
        spectrum = pink_noise_spectrum * np.exp(1j * phase)
        pink = np.fft.irfft(spectrum, n=n_samples)
        pink = pink / np.std(pink) * noise_level

        # alpha 振荡 (8-13 Hz)，模拟后部电极 alpha 更强
        alpha_freq = rng.uniform(8.5, 12.5)
        alpha_amp = alpha_power * (0.5 + 0.5 * (ch / n_channels))
        alpha = alpha_amp * np.sin(2 * np.pi * alpha_freq * times)

        # 60 Hz 工频干扰（北美/中国标准）
        line_noise_amp = rng.uniform(0.5, 2.0)
        line_noise = line_noise_amp * np.sin(2 * np.pi * 60.0 * times)

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
    设计巴特沃斯带通滤波器系数。

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
    b, a = sp_signal.butter(order, [low, high], btype="band")
    return b, a


def design_notch_filter(freq=60.0, sfreq=250.0, quality_factor=30.0):
    """
    设计 IIR 陷波滤波器（去除工频干扰）。

    Parameters
    ----------
    freq : float
        目标频率（Hz），中国/北美 60 Hz，欧洲 50 Hz
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
        freqs, psd = sp_signal.welch(
            data[ch], fs=sfreq, nperseg=int(sfreq * 2), noverlap=int(sfreq)
        )
        mask = (freqs >= freq_range[0]) & (freqs <= freq_range[1])
        ax.semilogy(freqs[mask], psd[mask], color=colors[ch],
                     label=channel_names[ch], linewidth=1.2)

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
    """计算信号在指定频段内的绝对和相对功率。"""
    if bands is None:
        bands = {
            "delta": (0.5, 4), "theta": (4, 8), "alpha": (8, 13),
            "beta": (13, 30), "gamma": (30, 45),
        }
    if data.ndim == 1:
        data = data[np.newaxis, :]
    freqs, psd_all = sp_signal.welch(data, fs=sfreq, axis=-1,
                                      nperseg=int(sfreq * 2))
    total_power = np.trapz(psd_all.mean(axis=0), freqs)
    if total_power == 0:
        total_power = 1.0
    results = {}
    for name, (lo, hi) in bands.items():
        mask = (freqs >= lo) & (freqs <= hi)
        band_power = np.trapz(psd_all[:, mask].mean(axis=0), freqs[mask])
        results[name] = {
            "absolute": band_power,
            "relative": band_power / total_power
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
