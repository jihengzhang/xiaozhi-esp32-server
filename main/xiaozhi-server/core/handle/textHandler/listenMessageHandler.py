import time
import asyncio
from typing import Dict, Any

from core.handle.receiveAudioHandle import startToChat
from core.handle.helloHandle import checkWakeupWords
from core.handle.reportHandle import enqueue_asr_report
from core.handle.sendAudioHandle import (
    send_stt_message,
    send_tts_message,
    sendAudioMessage,
)
from core.handle.textMessageHandler import TextMessageHandler
from core.handle.textMessageType import TextMessageType
from core.utils.util import remove_punctuation_and_length
from core.providers.asr.dto.dto import InterfaceType
from core.providers.tts.dto.dto import SentenceType
from core.utils.util import audio_to_data

TAG = __name__

class ListenTextMessageHandler(TextMessageHandler):
    """Listen消息处理器"""

    @property
    def message_type(self) -> TextMessageType:
        return TextMessageType.LISTEN

    async def handle(self, conn, msg_json: Dict[str, Any]) -> None:
        if "mode" in msg_json:
            conn.client_listen_mode = msg_json["mode"]
            conn.logger.bind(tag=TAG).debug(
                f"客户端拾音模式：{conn.client_listen_mode}"
            )
        if msg_json["state"] == "start":
            conn.client_have_voice = True
            conn.client_voice_stop = False
            # 首次进入 listen 时立即播报问候，避免等待后续唤醒词
            enable_greeting = conn.config.get("enable_greeting", True)
            # 记录是否已播报过问候，便于排查（用 info 方便看到）
            conn.logger.bind(tag=TAG).info(
                f"listen start greeting check: enable_greeting={enable_greeting}, already_played={getattr(conn, 'greeting_played', False)}"
            )
            if enable_greeting and not getattr(conn, "greeting_played", False):
                conn.greeting_played = True
                conn.logger.bind(tag=TAG).info("listen start greeting: play preset audio")
                try:
                    # 优先使用预设音频，避免TTS延迟；文件不存在则回退TTS
                    opus_packets = None
                    preset_path = "config/assets/wakeup_words_short.wav"
                    try:
                        opus_packets = await audio_to_data(preset_path, use_cache=False)
                        conn.logger.bind(tag=TAG).info(
                            f"listen start greeting: using preset {preset_path}"
                        )
                    except Exception as e:
                        conn.logger.bind(tag=TAG).warning(
                            f"listen start greeting: preset missing/fail ({e}), fallback to tts"
                        )

                    if opus_packets is None and conn.tts:
                        tts_result = await asyncio.to_thread(conn.tts.to_tts, "你好")
                        opus_packets = tts_result

                    if opus_packets:
                        conn.logger.bind(tag=TAG).info("listen start greeting: send FIRST")
                        await sendAudioMessage(
                            conn, SentenceType.FIRST, opus_packets, "你好"
                        )
                        conn.logger.bind(tag=TAG).info("listen start greeting: send LAST")
                        await sendAudioMessage(conn, SentenceType.LAST, [], None)
                except Exception as e:
                    conn.logger.bind(tag=TAG).warning(f"greeting play failed: {e}")
        elif msg_json["state"] == "stop":
            conn.client_have_voice = True
            conn.client_voice_stop = True
            if conn.asr.interface_type == InterfaceType.STREAM:
                # 流式模式下，发送结束请求
                asyncio.create_task(conn.asr._send_stop_request())
            else:
                # 非流式模式：直接触发ASR识别
                if len(conn.asr_audio) > 0:
                    asr_audio_task = conn.asr_audio.copy()
                    conn.asr_audio.clear()
                    conn.reset_vad_states()

                    if len(asr_audio_task) > 0:
                        await conn.asr.handle_voice_stop(conn, asr_audio_task)
        elif msg_json["state"] == "detect":
            conn.client_have_voice = False
            conn.asr_audio.clear()
            if "text" in msg_json:
                conn.last_activity_time = time.time() * 1000
                original_text = msg_json["text"]  # 保留原始文本
                filtered_len, filtered_text = remove_punctuation_and_length(
                    original_text
                )

                # 识别是否是唤醒词（对配置同样去除标点和空格以对齐检测结果）
                normalized_wakeup_words = [
                    remove_punctuation_and_length(word)[1]
                    for word in conn.config.get("wakeup_words", [])
                ]
                is_wakeup_words = filtered_text in normalized_wakeup_words
                # 是否开启唤醒词回复
                enable_greeting = conn.config.get("enable_greeting", True)

                if is_wakeup_words and not enable_greeting:
                    # 如果是唤醒词，且关闭了唤醒词回复，就不用回答
                    await send_stt_message(conn, original_text)
                    await send_tts_message(conn, "stop", None)
                    conn.client_is_speaking = False
                elif is_wakeup_words:
                    conn.logger.bind(tag=TAG).info(
                        f"wakeup detected, enable_greeting={enable_greeting}"
                    )
                    # 优先播放即时唤醒音（成功返回 True 时已发送音频并补充对话）
                    if await checkWakeupWords(conn, original_text):
                        conn.logger.bind(tag=TAG).info("wakeup audio played via cache/TTS")
                        return

                    conn.just_woken_up = True
                    # 上报纯文字数据（复用ASR上报功能，但不提供音频数据）
                    enqueue_asr_report(conn, "你好", [])
                    await startToChat(conn, "你好")
                else:
                    conn.just_woken_up = True
                    # 上报纯文字数据（复用ASR上报功能，但不提供音频数据）
                    enqueue_asr_report(conn, original_text, [])
                    # 否则需要LLM对文字内容进行答复
                    await startToChat(conn, original_text)