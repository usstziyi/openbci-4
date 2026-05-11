"""
OpenBCI Cyton 学习计划 — 工具包入口
=================================

统一导出 helpers.py 中常用的工具函数、设备管理函数和常量。
"""

from .helpers import (
    generate_synthetic_eeg,
    parse_cyton_packet,
    design_bandpass_filter,
    design_notch_filter,
    plot_eeg_channels,
    plot_psd,
    list_available_boards,
    parse_and_print_desc,
    create_cyton_board,
    compute_band_powers,
    CYTON_8CH_1020_MAP,
    DAISY_8CH_1020_MAP,
    BAND_COLORS,
)

__all__ = [
    "generate_synthetic_eeg",
    "parse_cyton_packet",
    "design_bandpass_filter",
    "design_notch_filter",
    "plot_eeg_channels",
    "plot_psd",
    "list_available_boards",
    "parse_and_print_desc",
    "create_cyton_board",
    "compute_band_powers",
    "CYTON_8CH_1020_MAP",
    "DAISY_8CH_1020_MAP",
    "BAND_COLORS",
]