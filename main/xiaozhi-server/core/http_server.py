import asyncio
import ssl
from aiohttp import web
from config.logger import setup_logging
from core.api.ota_handler import OTAHandler
from core.api.vision_handler import VisionHandler

TAG = __name__


class SimpleHttpServer:
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logging()
        self.ota_handler = OTAHandler(config)
        self.vision_handler = VisionHandler(config)

    def _get_websocket_url(self, local_ip: str, port: int, use_ssl: bool = False) -> str:
        """获取websocket地址

        Args:
            local_ip: 本地IP地址
            port: 端口号
            use_ssl: 是否使用SSL

        Returns:
            str: websocket地址
        """
        server_config = self.config["server"]
        websocket_config = server_config.get("websocket")

        if websocket_config and "你" not in websocket_config:
            return websocket_config
        else:
            protocol = "wss" if use_ssl else "ws"
            return f"{protocol}://{local_ip}:{port}/xiaozhi/v1/"

    async def start(self):
        try:
            server_config = self.config["server"]
            read_config_from_api = self.config.get("read_config_from_api", False)
            host = server_config.get("ip", "0.0.0.0")
            port = int(server_config.get("http_port", 8003))

            if port:
                app = web.Application()

                if not read_config_from_api:
                    # 如果没有开启智控台，只是单模块运行，就需要再添加简单OTA接口，用于下发websocket接口
                    app.add_routes(
                        [
                            web.get("/xiaozhi/ota/", self.ota_handler.handle_get),
                            web.post("/xiaozhi/ota/", self.ota_handler.handle_post),
                            web.options(
                                "/xiaozhi/ota/", self.ota_handler.handle_options
                            ),
                            # 下载接口，仅提供 data/bin/*.bin 下载
                            web.get(
                                "/xiaozhi/ota/download/{filename}",
                                self.ota_handler.handle_download,
                            ),
                            web.options(
                                "/xiaozhi/ota/download/{filename}",
                                self.ota_handler.handle_options,
                            ),
                        ]
                    )
                # 添加路由
                app.add_routes(
                    [
                        web.get("/mcp/vision/explain", self.vision_handler.handle_get),
                        web.post(
                            "/mcp/vision/explain", self.vision_handler.handle_post
                        ),
                        web.options(
                            "/mcp/vision/explain", self.vision_handler.handle_options
                        ),
                    ]
                )

                # 运行服务
                runner = web.AppRunner(app)
                await runner.setup()
                
                # 检查是否启用SSL
                ssl_config = server_config.get("ssl", {})
                ssl_enabled = ssl_config.get("enabled", False)
                ssl_context = None
                
                if ssl_enabled:
                    cert_file = ssl_config.get("cert_file")
                    key_file = ssl_config.get("key_file")
                    
                    if cert_file and key_file:
                        try:
                            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                            ssl_context.load_cert_chain(cert_file, key_file)
                            self.logger.bind(tag=TAG).info(f"SSL enabled for HTTP server")
                            self.logger.bind(tag=TAG).info(f"Certificate: {cert_file}")
                        except Exception as e:
                            self.logger.bind(tag=TAG).warning(f"Failed to load SSL certificates: {e}")
                            self.logger.bind(tag=TAG).warning("Falling back to HTTP")
                            ssl_enabled = False
                    else:
                        self.logger.bind(tag=TAG).warning("SSL enabled but cert/key files not specified")
                        ssl_enabled = False
                
                site = web.TCPSite(runner, host, port, ssl_context=ssl_context)
                await site.start()

                # 保持服务运行
                while True:
                    await asyncio.sleep(3600)  # 每隔 1 小时检查一次
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"HTTP服务器启动失败: {e}")
            import traceback

            self.logger.bind(tag=TAG).error(f"错误堆栈: {traceback.format_exc()}")
            raise
