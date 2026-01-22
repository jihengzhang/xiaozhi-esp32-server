import { log } from '../../utils/logger.js';

// ==========================================
// MCP 工具管理逻辑
// ==========================================

// 全局变量
let mcpTools = [];
let mcpEditingIndex = null;
let mcpProperties = [];
let websocket = null; // 将从外部设置

// ==========================================
// MCP HTTP Bridge 服务调用
// ==========================================

// MCP HTTP Bridge 服务地址（MR 设备本地）
const MCP_HTTP_BRIDGE_URL = 'http://127.0.0.1:8765';

/**
 * 调用 MCP HTTP Bridge 执行工具
 * 通过 HTTP 调用运行在 MR 设备本地的 Python MCP 工具
 * 
 * @param {string} toolName - 工具名称
 * @param {object} toolArgs - 工具参数
 * @returns {Promise<object|null>} 执行结果，如果工具不存在或服务不可用则返回 null
 */
async function executeMcpHttpBridge(toolName, toolArgs) {
    try {
        log(`[MCP Bridge] 调用工具: ${toolName}`, 'info');
        
        const response = await fetch(`${MCP_HTTP_BRIDGE_URL}/tools/call`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: toolName,
                arguments: toolArgs || {}
            })
        });
        
        if (!response.ok) {
            if (response.status === 404) {
                log(`[hiPanda HTTP] 工具 ${toolName} 不存在`, 'warning');
                return null;
            }
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        log(`[MCP Bridge] 工具 ${toolName} 执行成功`, 'success');
        return result;
        
    } catch (error) {
        // 如果 MCP Bridge 服务不可用，返回 null（回退到模拟数据）
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            log(`[MCP Bridge] 服务不可用，请确保 mcp_http_bridge.py 正在运行`, 'debug');
            return null;
        }
        
        log(`[MCP Bridge] 调用失败: ${error.message}`, 'error');
        return {
            success: false,
            error: error.message
        };
    }
}

/**
 * 设置 WebSocket 实例
 * @param {WebSocket} ws - WebSocket 连接实例
 */
export function setWebSocket(ws) {
    websocket = ws;
}

/**
 * 从 MCP HTTP Bridge 加载工具列表
 */
async function loadMcpToolsFromBridge() {
    try {
        const response = await fetch(`${MCP_HTTP_BRIDGE_URL}/tools/list`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        if (data.tools && Array.isArray(data.tools)) {
            log(`从 MCP Bridge 加载了 ${data.tools.length} 个工具`, 'success');
            return data.tools;
        }
        return [];
    } catch (error) {
        log(`无法连接 MCP Bridge: ${error.message}`, 'warning');
        return [];
    }
}

/**
 * 初始化 MCP 工具
 */
export async function initMcpTools() {
    // 1. 尝试从 MCP HTTP Bridge 加载工具
    const bridgeTools = await loadMcpToolsFromBridge();
    
    // 2. 加载默认工具数据
    const defaultMcpTools = await fetch("js/config/default-mcp-tools.json").then(res => res.json());

    // 3. 合并工具列表：Bridge 工具 + 默认工具（去重）
    const allTools = [...bridgeTools];
    const bridgeToolNames = new Set(bridgeTools.map(t => t.name));
    defaultMcpTools.forEach(tool => {
        if (!bridgeToolNames.has(tool.name)) {
            allTools.push(tool);
        }
    });

    // 4. 从 localStorage 恢复用户自定义工具
    const savedTools = localStorage.getItem('mcpTools');
    if (savedTools) {
        try {
            const customTools = JSON.parse(savedTools);
            // 只添加不在 Bridge 和默认工具中的自定义工具
            const existingNames = new Set(allTools.map(t => t.name));
            customTools.forEach(tool => {
                if (!existingNames.has(tool.name)) {
                    allTools.push(tool);
                }
            });
        } catch (e) {
            log('加载自定义工具失败', 'warning');
        }
    }

    mcpTools = allTools;
    renderMcpTools();
    setupMcpEventListeners();
}

/**
 * 渲染工具列表
 */
function renderMcpTools() {
    const container = document.getElementById('mcpToolsContainer');
    const countSpan = document.getElementById('mcpToolsCount');

    countSpan.textContent = `${mcpTools.length} 个工具`;

    if (mcpTools.length === 0) {
        container.innerHTML = '<div style="text-align: center; padding: 30px; color: #999;">暂无工具，点击下方按钮添加新工具</div>';
        return;
    }

    container.innerHTML = mcpTools.map((tool, index) => {
        const paramCount = tool.inputSchema.properties ? Object.keys(tool.inputSchema.properties).length : 0;
        const requiredCount = tool.inputSchema.required ? tool.inputSchema.required.length : 0;
        const hasMockResponse = tool.mockResponse && Object.keys(tool.mockResponse).length > 0;

        return `
            <div class="mcp-tool-card">
                <div class="mcp-tool-header">
                    <div class="mcp-tool-name">${tool.name}</div>
                    <div class="mcp-tool-actions">
                        <button onclick="window.mcpModule.editMcpTool(${index})"
                            style="padding: 4px 10px; border: none; border-radius: 4px; background-color: #2196f3; color: white; cursor: pointer; font-size: 12px;">
                            ✏️ 编辑
                        </button>
                        <button onclick="window.mcpModule.deleteMcpTool(${index})"
                            style="padding: 4px 10px; border: none; border-radius: 4px; background-color: #f44336; color: white; cursor: pointer; font-size: 12px;">
                            🗑️ 删除
                        </button>
                    </div>
                </div>
                <div class="mcp-tool-description">${tool.description}</div>
                <div class="mcp-tool-info">
                    <div class="mcp-tool-info-row">
                        <span class="mcp-tool-info-label">参数数量:</span>
                        <span class="mcp-tool-info-value">${paramCount} 个 ${requiredCount > 0 ? `(${requiredCount} 个必填)` : ''}</span>
                    </div>
                    <div class="mcp-tool-info-row">
                        <span class="mcp-tool-info-label">模拟返回:</span>
                        <span class="mcp-tool-info-value">${hasMockResponse ? '✅ 已配置: ' + JSON.stringify(tool.mockResponse) : '⚪ 使用默认'}</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

/**
 * 渲染参数列表
 */
function renderMcpProperties() {
    const container = document.getElementById('mcpPropertiesContainer');

    if (mcpProperties.length === 0) {
        container.innerHTML = '<div style="text-align: center; padding: 20px; color: #999; font-size: 14px;">暂无参数，点击下方按钮添加参数</div>';
        return;
    }

    container.innerHTML = mcpProperties.map((prop, index) => `
        <div class="mcp-property-item">
            <div class="mcp-property-header">
                <span class="mcp-property-name">${prop.name}</span>
                <button type="button" onclick="window.mcpModule.deleteMcpProperty(${index})"
                    style="padding: 3px 8px; border: none; border-radius: 3px; background-color: #f44336; color: white; cursor: pointer; font-size: 11px;">
                    删除
                </button>
            </div>
            <div class="mcp-property-row">
                <div>
                    <label class="mcp-small-label">参数名称 *</label>
                    <input type="text" class="mcp-small-input" value="${prop.name}"
                        onchange="window.mcpModule.updateMcpProperty(${index}, 'name', this.value)" required>
                </div>
                <div>
                    <label class="mcp-small-label">数据类型 *</label>
                    <select class="mcp-small-input" onchange="window.mcpModule.updateMcpProperty(${index}, 'type', this.value)">
                        <option value="string" ${prop.type === 'string' ? 'selected' : ''}>字符串</option>
                        <option value="integer" ${prop.type === 'integer' ? 'selected' : ''}>整数</option>
                        <option value="number" ${prop.type === 'number' ? 'selected' : ''}>数字</option>
                        <option value="boolean" ${prop.type === 'boolean' ? 'selected' : ''}>布尔值</option>
                        <option value="array" ${prop.type === 'array' ? 'selected' : ''}>数组</option>
                        <option value="object" ${prop.type === 'object' ? 'selected' : ''}>对象</option>
                    </select>
                </div>
            </div>
            ${(prop.type === 'integer' || prop.type === 'number') ? `
            <div class="mcp-property-row">
                <div>
                    <label class="mcp-small-label">最小值</label>
                    <input type="number" class="mcp-small-input" value="${prop.minimum !== undefined ? prop.minimum : ''}"
                        placeholder="可选" onchange="window.mcpModule.updateMcpProperty(${index}, 'minimum', this.value ? parseFloat(this.value) : undefined)">
                </div>
                <div>
                    <label class="mcp-small-label">最大值</label>
                    <input type="number" class="mcp-small-input" value="${prop.maximum !== undefined ? prop.maximum : ''}"
                        placeholder="可选" onchange="window.mcpModule.updateMcpProperty(${index}, 'maximum', this.value ? parseFloat(this.value) : undefined)">
                </div>
            </div>
            ` : ''}
            <div class="mcp-property-row-full">
                <label class="mcp-small-label">参数描述</label>
                <input type="text" class="mcp-small-input" value="${prop.description || ''}"
                    placeholder="可选" onchange="window.mcpModule.updateMcpProperty(${index}, 'description', this.value)">
            </div>
            <label class="mcp-checkbox-label">
                <input type="checkbox" ${prop.required ? 'checked' : ''}
                    onchange="window.mcpModule.updateMcpProperty(${index}, 'required', this.checked)">
                必填参数
            </label>
        </div>
    `).join('');
}

/**
 * 添加参数
 */
function addMcpProperty() {
    mcpProperties.push({
        name: `param_${mcpProperties.length + 1}`,
        type: 'string',
        required: false,
        description: ''
    });
    renderMcpProperties();
}

/**
 * 更新参数
 */
function updateMcpProperty(index, field, value) {
    if (field === 'name') {
        const isDuplicate = mcpProperties.some((p, i) => i !== index && p.name === value);
        if (isDuplicate) {
            alert('参数名称已存在，请使用不同的名称');
            renderMcpProperties();
            return;
        }
    }

    mcpProperties[index][field] = value;

    if (field === 'type' && value !== 'integer' && value !== 'number') {
        delete mcpProperties[index].minimum;
        delete mcpProperties[index].maximum;
        renderMcpProperties();
    }
}

/**
 * 删除参数
 */
function deleteMcpProperty(index) {
    mcpProperties.splice(index, 1);
    renderMcpProperties();
}

/**
 * 设置事件监听
 */
function setupMcpEventListeners() {
    const toggleBtn = document.getElementById('toggleMcpTools');
    const panel = document.getElementById('mcpToolsPanel');
    const addBtn = document.getElementById('addMcpToolBtn');
    const modal = document.getElementById('mcpToolModal');
    const closeBtn = document.getElementById('closeMcpModalBtn');
    const cancelBtn = document.getElementById('cancelMcpBtn');
    const form = document.getElementById('mcpToolForm');
    const addPropertyBtn = document.getElementById('addMcpPropertyBtn');

    toggleBtn.addEventListener('click', () => {
        const isExpanded = panel.classList.contains('expanded');
        panel.classList.toggle('expanded');
        toggleBtn.textContent = isExpanded ? '展开' : '收起';
    });

    addBtn.addEventListener('click', () => openMcpModal());
    closeBtn.addEventListener('click', closeMcpModal);
    cancelBtn.addEventListener('click', closeMcpModal);
    addPropertyBtn.addEventListener('click', addMcpProperty);

    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeMcpModal();
    });

    form.addEventListener('submit', handleMcpSubmit);
}

/**
 * 打开模态框
 */
function openMcpModal(index = null) {
    const isConnected = websocket && websocket.readyState === WebSocket.OPEN;
    if (isConnected) {
        alert('WebSocket 已连接，无法编辑工具');
        return;
    }

    mcpEditingIndex = index;
    const errorContainer = document.getElementById('mcpErrorContainer');
    errorContainer.innerHTML = '';

    if (index !== null) {
        document.getElementById('mcpModalTitle').textContent = '编辑工具';
        const tool = mcpTools[index];
        document.getElementById('mcpToolName').value = tool.name;
        document.getElementById('mcpToolDescription').value = tool.description;
        document.getElementById('mcpMockResponse').value = tool.mockResponse ? JSON.stringify(tool.mockResponse, null, 2) : '';

        mcpProperties = [];
        const schema = tool.inputSchema;
        if (schema.properties) {
            Object.keys(schema.properties).forEach(key => {
                const prop = schema.properties[key];
                mcpProperties.push({
                    name: key,
                    type: prop.type || 'string',
                    minimum: prop.minimum,
                    maximum: prop.maximum,
                    description: prop.description || '',
                    required: schema.required && schema.required.includes(key)
                });
            });
        }
    } else {
        document.getElementById('mcpModalTitle').textContent = '添加工具';
        document.getElementById('mcpToolForm').reset();
        mcpProperties = [];
    }

    renderMcpProperties();
    document.getElementById('mcpToolModal').style.display = 'block';
}

/**
 * 关闭模态框
 */
function closeMcpModal() {
    document.getElementById('mcpToolModal').style.display = 'none';
    mcpEditingIndex = null;
    document.getElementById('mcpToolForm').reset();
    mcpProperties = [];
    document.getElementById('mcpErrorContainer').innerHTML = '';
}

/**
 * 处理表单提交
 */
function handleMcpSubmit(e) {
    e.preventDefault();
    const errorContainer = document.getElementById('mcpErrorContainer');
    errorContainer.innerHTML = '';

    const name = document.getElementById('mcpToolName').value.trim();
    const description = document.getElementById('mcpToolDescription').value.trim();
    const mockResponseText = document.getElementById('mcpMockResponse').value.trim();

    // 检查名称重复
    const isDuplicate = mcpTools.some((tool, index) =>
        tool.name === name && index !== mcpEditingIndex
    );

    if (isDuplicate) {
        showMcpError('工具名称已存在，请使用不同的名称');
        return;
    }

    // 解析模拟返回结果
    let mockResponse = null;
    if (mockResponseText) {
        try {
            mockResponse = JSON.parse(mockResponseText);
        } catch (e) {
            showMcpError('模拟返回结果不是有效的 JSON 格式: ' + e.message);
            return;
        }
    }

    // 构建 inputSchema
    const inputSchema = {
        type: "object",
        properties: {},
        required: []
    };

    mcpProperties.forEach(prop => {
        const propSchema = { type: prop.type };

        if (prop.description) {
            propSchema.description = prop.description;
        }

        if ((prop.type === 'integer' || prop.type === 'number')) {
            if (prop.minimum !== undefined && prop.minimum !== '') {
                propSchema.minimum = prop.minimum;
            }
            if (prop.maximum !== undefined && prop.maximum !== '') {
                propSchema.maximum = prop.maximum;
            }
        }

        inputSchema.properties[prop.name] = propSchema;

        if (prop.required) {
            inputSchema.required.push(prop.name);
        }
    });

    if (inputSchema.required.length === 0) {
        delete inputSchema.required;
    }

    const tool = { name, description, inputSchema, mockResponse };

    if (mcpEditingIndex !== null) {
        mcpTools[mcpEditingIndex] = tool;
        log(`已更新工具: ${name}`, 'success');
    } else {
        mcpTools.push(tool);
        log(`已添加工具: ${name}`, 'success');
    }

    saveMcpTools();
    renderMcpTools();
    closeMcpModal();
}

/**
 * 显示错误
 */
function showMcpError(message) {
    const errorContainer = document.getElementById('mcpErrorContainer');
    errorContainer.innerHTML = `<div class="mcp-error">${message}</div>`;
}

/**
 * 编辑工具
 */
function editMcpTool(index) {
    openMcpModal(index);
}

/**
 * 删除工具
 */
function deleteMcpTool(index) {
    const isConnected = websocket && websocket.readyState === WebSocket.OPEN;
    if (isConnected) {
        alert('WebSocket 已连接，无法编辑工具');
        return;
    }
    if (confirm(`确定要删除工具 "${mcpTools[index].name}" 吗？`)) {
        const toolName = mcpTools[index].name;
        mcpTools.splice(index, 1);
        saveMcpTools();
        renderMcpTools();
        log(`已删除工具: ${toolName}`, 'info');
    }
}

/**
 * 保存工具
 */
function saveMcpTools() {
    localStorage.setItem('mcpTools', JSON.stringify(mcpTools));
}

/**
 * 获取工具列表
 */
export function getMcpTools() {
    return mcpTools.map(tool => ({
        name: tool.name,
        description: tool.description,
        inputSchema: tool.inputSchema
    }));
}

/**
 * 执行工具调用
 * 优先级: MCP HTTP Bridge (本地 Python 服务) > 模拟返回 > 默认消息
 */
export async function executeMcpTool(toolName, toolArgs) {
    const tool = mcpTools.find(t => t.name === toolName);

    if (!tool) {
        log(`未找到工具: ${toolName}`, 'error');
        return {
            success: false,
            error: `未知工具: ${toolName}`
        };
    }

    // 1️⃣ 优先使用 MCP HTTP Bridge（MR 设备本地 Python 服务）
    const bridgeResult = await executeMcpHttpBridge(toolName, toolArgs);
    if (bridgeResult !== null) {
        log(`工具 ${toolName} 通过 MCP HTTP Bridge 执行`, 'info');
        return bridgeResult;
    }

    // 2️⃣ 如果有模拟返回结果，使用它
    if (tool.mockResponse) {
        // 替换模板变量
        let responseStr = JSON.stringify(tool.mockResponse);

        // 替换 ${paramName} 格式的变量
        if (toolArgs) {
            Object.keys(toolArgs).forEach(key => {
                const regex = new RegExp(`\\$\\{${key}\\}`, 'g');
                responseStr = responseStr.replace(regex, toolArgs[key]);
            });
        }

        try {
            const response = JSON.parse(responseStr);
            log(`工具 ${toolName} 执行成功，返回模拟结果`, 'success');
            return response;
        } catch (e) {
            log(`解析模拟返回结果失败: ${e.message}`, 'error');
            return tool.mockResponse;
        }
    }

    // 3️⃣ 没有 MCP 实现也没有模拟返回，返回默认成功消息
    log(`工具 ${toolName} 执行成功，返回默认结果`, 'success');
    return {
        success: true,
        message: `工具 ${toolName} 执行成功`,
        tool: toolName,
        arguments: toolArgs
    };
}

// 暴露全局方法供 HTML 内联事件调用
window.mcpModule = {
    updateMcpProperty,
    deleteMcpProperty,
    editMcpTool,
    deleteMcpTool
};
