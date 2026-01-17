import importlib
import logging
import os
import sys
import time
import wave
import uuid
from abc import ABC, abstractmethod
from typing import Optional, Tuple, List
from core.providers.asr.base import ASRProviderBase
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()

def create_instance(class_name: str, *args, **kwargs) -> ASRProviderBase:
    """工厂方法创建ASR实例"""
    # 使用绝对路径而不是相对路径，确保从任何工作目录都能找到文件
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    provider_file_path = os.path.join(current_file_dir, '..', 'providers', 'asr', f'{class_name}.py')
    
    if os.path.exists(provider_file_path):
        lib_name = f'core.providers.asr.{class_name}'
        if lib_name not in sys.modules:
            sys.modules[lib_name] = importlib.import_module(f'{lib_name}')
        return sys.modules[lib_name].ASRProvider(*args, **kwargs)

    raise ValueError(f"不支持的ASR类型: {class_name}，请检查该配置的type是否设置正确")