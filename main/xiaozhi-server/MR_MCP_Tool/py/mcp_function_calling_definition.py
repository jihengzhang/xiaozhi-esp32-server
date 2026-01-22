# from mcp.server.fastmcp import FastMCP  # 注释掉，改用简单的装饰器
import traceback
import sys
import inspect

# 简单的装饰器类，替代 FastMCP
class SimpleMCPServer:
    def __init__(self, name):
        self.name = name
    
    def tool(self):
        def decorator(func):
            return func
        return decorator
    
    def run(self, transport):
        pass  # 占位，不实际运行

server = SimpleMCPServer("Local Agent Helper")

# sheets: load_protocol_from_library
@server.tool()
def load_protocol_from_library(library_name: str=None, protocol_name: str=None) -> str:
    """
    Load a specified MRI protocol.
    Parameters:
        library_name (str): The name of the protocol library. Valid values are 'ge', 'site', and 'service'.
        protocol_name (str): The name or identifier of the protocol to load (e.g., 'Brain Routine').
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: select_task_by_index, select_series_by_index
@server.tool()
def select_task_or_series(index: str=None) -> str:
    """
    Select a task or series by index. If no index is specified, select the default task or series.
    Parameters:
        index (str): The index of the task to be selected as the current task. Default is None.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: duplicate_task_by_index, duplicate_series_by_index
@server.tool()
def duplicate_task_or_series(index: str=None) -> str:
    """
    Duplicate a task or series by index. If no index is specified, duplicate the default task or series.
    Parameters:
        index (str): The index of task or series to be duplicated. Default is None.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: start_examination
@server.tool()
def start_examination() -> str:
    """
    Start a new MRI exam or examination session.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: end_examination
@server.tool()
def end_examination() -> str:
    """
    End the current MRI exam session.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: set_parameter_by_index
@server.tool()
def set_parameter(index: str=None, param_name: str=None, param_value: str=None) -> str:
    """
    Set a specific parameter for a task or series identified by its index. If no index is specified, set the default one's parameter.
    Parameters:
        index (str): The index of the task or series in the task or series list. Default is None.
        param_name (str): The name of the parameter to set. Default is None.
        param_value (str): The value to assign to the parameter. Default is None.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

#sheets: save_task_by_index
@server.tool()
def save_task_or_series(index=None) -> str:
    """
    Save the RX(prescription) of a specific task or series identified by its index. If no index is specified, save the default one.
    Parameters:
        index : The index of the task in the task list to be confirmed. Default is None.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: prescan
@server.tool()
def prescan(method="automatic") -> str:
    """
    Perform prescan.
    Parameters:
        method (str): The method of prescan. Default is 'automatic'.:
            - "automatic": Perform an automatic prescan. Automatic prescan is commonly abbreviated as “auto prescan.
            - "manual": Perform a manual prescan.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: stop_prescan
@server.tool()
def stop_prescan() -> str:
    """
    Stop current prescan.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: start_scan
@server.tool()
def start_scan(index: str = None) -> str:
    """
    Execute the scan operation for a specific task or series identified by its index. If no index is specified, scan the default one.
    Parameters:
        index (str): The index of the task in the task list to be scanned. Default is None.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: pause_scan
@server.tool()
def pause_scan() -> str:
    """
    Pause the scanning operation.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: stop_scan
@server.tool()
def stop_scan() -> str:
    """
    Stop the scanning operation.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: resume_scan
@server.tool()
def resume_scan() -> str:
    """
    Resume the early stopped scanning.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: control_fan
@server.tool()
def control_fan(level: str=None) -> str:
    """
    Control fan and set speed level(optional).
    Parameters:
        level (str): The desired fan control level. Accepted values are:
            - "on": Turn on the fan
            - "low": Set fan to low speed
            - "medium": Set fan to medium speed
            - "high": Set fan to high speed
            - "off": Turn off the fan
            - None: Do nothing
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: control_fan
@server.tool()
def control_light(level: str=None) -> str:
    """
    Control light status and set brightness level(optional).
    Parameters:
        level (str): The desired light control level. Accepted values are:
            - "on": Turn on the light
            - "low": Set light to low brightness
            - "medium": Set light to medium brightness
            - "high": Set light to high brightness
            - "off": Turn off the light
            - None: Do nothing
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: set_hardware_landmark
@server.tool()
def set_hardware_landmark(value: float=None) -> str:
    """
    Sets the hardware landmark position.
    Parameters:
        value (float): The desired landmark position in millimeters (mm). Default is None, meaning do nothing.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: move_out
@server.tool()
def move_out_to_home_position() -> str:
    """
    Moves the MRI table/cradle to the HOME position.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: move_to_scan_position
@server.tool()
def move_in_to_scan_position() -> str:
    """
    Moves the MRI table/cradle in to the scan position.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: load_patient
@server.tool()
def load_patient(index: str=None, patient_id: str=None, record_type: str="all") -> str:
    """
    Loads a patient item from the MRI work list.
    Parameters:
        index (str): The record order on the work list UI. Default is None.
        patient_id (str): Optional patient ID to filter the record.
        record_type (str): The type of record to retrieve. Accepted values:
            - "local": Only local records
            - "ris": Only RIS records
            - "all": Both LOCAL and RIS records (default)
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# sheets: create_patient
@server.tool()
def create_patient(patient_id: str=None, weight: str=None) -> str:
    """
    Creates a patient record.
    Parameters:
        patient_id (str): The unique patient identifier.
        weight (str): The patient's weight in kilograms.
    Returns:
        str: Confirmation message
    """
    return f"{inspect.currentframe().f_code.co_name} called by mcp server."

# ============ 新增 MR 功能模块 ============

# MR 特定工具：获取脉冲序列
@server.tool()
def get_pulse_sequences() -> str:
    """
    获取设备支持的所有脉冲序列列表。
    
    Returns:
        str: 可用脉冲序列列表 (T1, T2, FLAIR, GRE, SPGR 等)
    """
    return "Available sequences: T1, T2, FLAIR, GRE, SPGR, DWI, DTI"

# MR 特定工具：设置扫描参数
@server.tool()
def set_scan_parameters(sequence: str, tr: float=1000.0, te: float=30.0, flip_angle: float=90.0) -> str:
    """
    设置 MRI 扫描参数（重复时间、回波时间、翻转角度）。
    
    Parameters:
        sequence (str): 脉冲序列名称 (e.g., 'T1', 'T2')
        tr (float): 重复时间 (ms)，默认 1000
        te (float): 回波时间 (ms)，默认 30
        flip_angle (float): 翻转角度 (度)，默认 90
    
    Returns:
        str: 参数配置确认
    """
    return f"Parameters set: {sequence} (TR={tr}ms, TE={te}ms, FA={flip_angle}°)"

# MR 特定工具：获取患者线缆位置
@server.tool()
def get_cable_position() -> str:
    """
    获取患者线缆当前位置。
    
    Returns:
        str: 线缆位置信息 (0-100%)
    """
    return "Cable position: 50%"

# MR 特定工具：移动患者线缆
@server.tool()
def move_cable(position: float=50.0, speed: str="normal") -> str:
    """
    移动患者线缆到指定位置。
    
    Parameters:
        position (float): 目标位置百分比 (0-100)
        speed (str): 移动速度 - 'slow'|'normal'|'fast'，默认 'normal'
    
    Returns:
        str: 操作确认消息
    """
    return f"Moving cable to {position}% at {speed} speed"

# MR 特定工具：检查线缆安全限制
@server.tool()
def check_cable_limits() -> str:
    """
    检查患者线缆是否触发安全限制。
    
    Returns:
        str: 安全状态确认
    """
    return "Cable within safe limits"

# MR 特定工具：获取设备信息
@server.tool()
def get_device_info(field: str="all") -> str:
    """
    获取设备基本信息（序列号、固件版本、型号等）。
    
    Parameters:
        field (str): 查询字段 - 'serial'|'firmware'|'model'|'all'，默认 'all'
    
    Returns:
        str: 设备信息
    """
    info = {
        "serial": "MR-2024-001",
        "firmware": "v5.2.1",
        "model": "3T MRI",
        "hw_config": "GE Discovery"
    }
    if field == "all":
        return str(info)
    return str(info.get(field, "Unknown"))

# MR 特定工具：获取校准状态
@server.tool()
def get_calibration_status() -> str:
    """
    获取设备校准状态和最后校准时间。
    
    Returns:
        str: 校准状态信息
    """
    return "Calibration status: OK, last calibrated: 2024-01-21"

# MR 特定工具：获取系统健康状态
@server.tool()
def get_system_health() -> str:
    """
    获取系统健康状态指标（CPU、内存、温度）。
    
    Returns:
        str: CPU 使用率、内存占用、系统温度 (%)
    """
    return "System health: CPU=45%, Memory=72%, Temp=35°C"

# MR 特定工具：获取错误日志
@server.tool()
def get_error_log(limit: int=10) -> str:
    """
    获取系统错误日志。
    
    Parameters:
        limit (int): 返回的日志条数，默认 10
    
    Returns:
        str: 错误日志摘要
    """
    return f"Error log (latest {limit}): [No errors detected]"

# MR 特定工具：加载协议
@server.tool()
def load_protocol_from_library_enhanced(library_name: str="site", protocol_name: str=None) -> str:
    """
    从协议库加载 MRI 扫描协议。
    
    Parameters:
        library_name (str): 协议库来源 - 'ge'|'site'|'service'，默认 'site'
        protocol_name (str): 协议名称 (e.g., 'Brain Routine')
    
    Returns:
        str: 协议加载确认
    """
    return f"Protocol loaded: {protocol_name} from {library_name}"

# MR 特定工具：获取协议列表
@server.tool()
def get_protocol_list(library: str="site") -> str:
    """
    获取可用协议列表。
    
    Parameters:
        library (str): 协议库 - 'ge'|'site'|'service'，默认 'site'
    
    Returns:
        str: 协议列表
    """
    return f"Available protocols from {library}: T1_BRAIN, T2_BRAIN, FLAIR_BRAIN, T1_SPINE, T2_SPINE, ..."

def main():
    print("READY", file=sys.stderr, flush=True)  # Use stderr for debug messages
    try:
        server.run(transport="stdio")
    except Exception as e:
        print(f"[FATAL] Server crashed: {e}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    print("Starting server", file=sys.stderr, flush=True)  # Use stderr for debug messages
    main()