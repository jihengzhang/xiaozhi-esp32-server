import importlib
import os
import sys
from core.providers.vad.base import VADProviderBase
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


def create_instance(class_name: str, *args, **kwargs) -> VADProviderBase:
    """工厂方法创建VAD实例"""
    # 使用绝对路径而不是相对路径，确保从任何工作目录都能找到文件
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    provider_file_path = os.path.join(current_file_dir, "..", "providers", "vad", f"{class_name}.py")
    
    if os.path.exists(provider_file_path):
        lib_name = f"core.providers.vad.{class_name}"
        if lib_name not in sys.modules:
            sys.modules[lib_name] = importlib.import_module(f"{lib_name}")
        return sys.modules[lib_name].VADProvider(*args, **kwargs)

    raise ValueError(f"不支持的VAD类型: {class_name}，请检查该配置的type是否设置正确")
