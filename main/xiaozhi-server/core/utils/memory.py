import os
import sys
import importlib
from config.logger import setup_logging

logger = setup_logging()


def create_instance(class_name, *args, **kwargs):
    # 使用绝对路径而不是相对路径，确保从任何工作目录都能找到文件
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    provider_file_path = os.path.join(current_file_dir, "..", "providers", "memory", class_name, f"{class_name}.py")
    
    if os.path.exists(provider_file_path):
        lib_name = f"core.providers.memory.{class_name}.{class_name}"
        if lib_name not in sys.modules:
            sys.modules[lib_name] = importlib.import_module(f"{lib_name}")
        return sys.modules[lib_name].MemoryProvider(*args, **kwargs)

    raise ValueError(f"不支持的记忆服务类型: {class_name}")
