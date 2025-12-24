#!/usr/bin/env python3
"""
测试小智ESP32服务器的WebSocket连接
"""
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://192.168.0.115:8000/xiaozhi/v1/"
    
    try:
        print(f"正在连接到 {uri}...")
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket连接成功!")
            
            # 发送测试消息
            test_message = {
                "type": "ping",
                "timestamp": "test"
            }
            await websocket.send(json.dumps(test_message))
            print(f"📤 发送: {test_message}")
            
            # 等待响应
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📥 收到: {response}")
            except asyncio.TimeoutError:
                print("⏱️  5秒内未收到响应（服务器可能不响应ping）")
            
            print("\n保持连接10秒，监听消息...")
            try:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    print(f"📥 收到消息: {message}")
            except asyncio.TimeoutError:
                print("✅ 测试完成")
                
    except ConnectionRefusedError:
        print("❌ 连接被拒绝 - 请检查服务是否运行")
    except Exception as e:
        print(f"❌ 错误: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
