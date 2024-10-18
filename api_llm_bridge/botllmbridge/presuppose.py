MARKER = "BOT_LLM_BRIDGE_PADDING_MARKER"

CHOICE_PADDING = "您必须从以下选项中选择一种操作:\n<BOT_LLM_BRIDGE_PADDING_MARKER>"

TEMPLATES = {
    "chassis": {
        "prompt": "您准备朝向哪个方向导航?",
        "type": "choice",
        "choice": ["forward", "backward", "turn_left", "turn_right", "task_finish"],
    },
    "arm": {
        "prompt": "您准备向什么方向移动机械爪?",
        "type": "choice",
        "choice": ["forward", "backward", "turn_left", "turn_right", "down", "up", "task_finish"],
    },
}
