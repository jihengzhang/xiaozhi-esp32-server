import os
import sys

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
sys.path.insert(0, project_root)

from config.logger import setup_logging
import importlib

logger = setup_logging()


def create_instance(class_name, *args, **kwargs):
    # 创建LLM实例
    # 使用绝对路径而不是相对路径，确保从任何工作目录都能找到文件
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    provider_file_path = os.path.join(current_file_dir, "..", "providers", "vllm", f"{class_name}.py")
    
    if os.path.exists(provider_file_path):
        lib_name = f"core.providers.vllm.{class_name}"
        if lib_name not in sys.modules:
            sys.modules[lib_name] = importlib.import_module(f"{lib_name}")
        return sys.modules[lib_name].VLLMProvider(*args, **kwargs)

    raise ValueError(f"不支持的VLLM类型: {class_name}，请检查该配置的type是否设置正确")
