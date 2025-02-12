import requests
import openai
import plugins
from plugins import *
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from datetime import datetime, timedelta


@plugins.register(name="huilv",
                  desc="query huilv",
                  version="1.0",
                  author="cc",
                  desire_priority=90)

class HuilvQuery(Plugin):
    content = None
    conversation_history = []  # 保存会话历史
    last_interaction_time = None

    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info(f"[{__class__.__name__}] inited")

    def get_help_text(self, **kwargs):
        help_text = f"发送【汇率 源目汇率】获取汇率信息\n" \
                    f"例如：【汇率 CNYUSD】获取人民币兑美元的实时汇率\n"
        return help_text

    def on_handle_context(self, e_context: EventContext):
        if e_context['context'].type != ContextType.TEXT:
            return
        self.content = e_context["context"].content.strip()

        if self.content.split()[0] in ["汇率"]:
            logger.info(f"[{__class__.__name__}] 收到消息: {self.content}")
            parts = self.content.split()
            if len(parts) < 2:
                reply = Reply()
                reply.type = ReplyType.ERROR
                reply.content = "格式错误，请发送：汇率 源目汇率。示例：cc CNYUSD "
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS
                return
            exchangetype = parts[1]
            reply = Reply()
            result = self.get_real_huilv_info(exchangetype)
            if result:
                reply.type = ReplyType.TEXT
                reply.content = result
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS
            else:
                error_message = "格式错误，请发送：汇率 源目汇率。示例：cc CNYUSD "
                reply.type = ReplyType.ERROR
                reply.content = error_message
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS

    def get_real_huilv_info(self, exchangetype):
        url = f"http://10.10.200.251:50001/exchange_rate/real?exchangetype={exchangetype}"
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.get(url=url, headers=headers, timeout=3)
            if response.status_code == 200:
                json_data = response.json()
                now = datetime.now()
                formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"接口返回的数据：{json_data}")
                return f'{formatted_time}_{exchangetype}:\n{json_data}'
            else:
                logger.error(f"主接口请求失败: {response.text}")
                raise Exception('request failed')
        except Exception as e:
            logger.error(f"接口异常：{e}")
        logger.error("所有接口都挂了,无法获取")
        return None



if __name__ == "__main__":
    huilv_query_plugin = HuilvQuery()
    result = huilv_query_plugin.get_ticket_info("汇率 CNYUSD")
    if result:
        print("获取到的汇率信息：", result)
    else:
        print("获取失败")