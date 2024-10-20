from rlb.rlb_task import RLBTask, RLBTaskSchema, RLBTaskSchemaType
from rlb import presuppose

SECURITY_WARNING = "您会选择谨慎的避开可能发生碰撞的人和障碍物,并始终相信安全比任务更重要."

############################
# 任务1: 导航并对齐到最近瓶子处 #
############################
_CHECK_FALLBACK_SCHEMA = RLBTaskSchema(
    schema_key="worth_fallback",
    prompt="您认为您前方已经没有空间/过于靠近篮子且无法看到任何需要抓取的瓶子了以至于值得冒险后退一点?",
    schema_type=RLBTaskSchemaType.BOOLEAN,
)

_CHECK_REACHED_SCHEMA = RLBTaskSchema(
    schema_key="reached",
    prompt="您认为您对齐瓶子了吗?",
    schema_type=RLBTaskSchemaType.BOOLEAN,
)

USER_NAVIGATE_TO_BOTTLE_TASK = RLBTask(
    description="任务1: 导航并对齐到最近瓶子处",
    prompt="您正在操控一台机器人,您可以看到一个顶部视角和一个底部视角,"
           "您当前的目标是靠近与您最近的瓶子并控制顶部视角中的机械爪与之对齐."
           f"{SECURITY_WARNING}"
           "如果您看到您前方已经无路可走,不妨尝试后退一点."
           "您只会在前方空间不足的情况下后退来避免发生视野外的碰撞."
           "如果您未能看到瓶子,不妨略微旋转一下."
           "您会仔细观察,并为了安全高效的完成目标而回答以下问题.",
    schema=[
        _CHECK_FALLBACK_SCHEMA,
        _CHECK_REACHED_SCHEMA,
        presuppose.CHASSIS_SCHEMA,
    ],
)

#########################
# 任务2: 控制机械臂对齐瓶子 #
#########################
_CHECK_TOP_ALIGNED = RLBTaskSchema(
    schema_key="top_aligned",
    prompt="从顶部视图看,机械臂对齐瓶子了吗?",
    schema_type=RLBTaskSchemaType.BOOLEAN,
)

_CHECK_BOTTOM_ALIGNED = RLBTaskSchema(
    schema_key="bottom_aligned",
    prompt="从底部视图看,机械臂对齐瓶子了吗?",
    schema_type=RLBTaskSchemaType.BOOLEAN,
)

_CHECK_ARM_ALIGNED_BOTTLE = RLBTaskSchema(
    schema_key="arm_aligned",
    prompt="您认为机械臂已经对齐瓶子以至于可以收起机械爪以抓起瓶子了吗?",
    schema_type=RLBTaskSchemaType.BOOLEAN,
)

USER_ALIGN_TO_BOTTLE_TASK = RLBTask(
    description="任务2: 控制机械臂对齐瓶子",
    prompt="您正在操控一台机器人,您可以看到一个顶部视角和一个底部视角,"
           "其中您可以在您的顶部视角中看到您的机械爪和一个瓶子."
           "您当前的目标是使用机械爪将瓶子夹起,"
           "为了实现目标,您会分别仔细观察顶部视角与底部视角,"
           "移动机械臂并确保机械爪在全部方向上都与瓶子对齐."
           f"{SECURITY_WARNING}"
           "您会仔细观察,并为了安全高效的完成目标而回答以下问题.",
    schema=[
        _CHECK_TOP_ALIGNED,
        _CHECK_BOTTOM_ALIGNED,
        _CHECK_ARM_ALIGNED_BOTTLE,
        presuppose.ARM_SCHEMA,
    ],
)

##############################
# 任务3: 导航并控制机械爪对齐篮子 #
##############################
_CHECK_BASKET = RLBTaskSchema(
    schema_key="can_see_basket",
    prompt="您当前当前可以在视野中看到篮子吗?",
    schema_type=RLBTaskSchemaType.BOOLEAN,
)

_CHECK_HOLDING = RLBTaskSchema(
    schema_key="is_holding",
    prompt="您当前可以看到您的机械爪和瓶子吗?您的机械爪仍然抓着瓶子吗?",
    schema_type=RLBTaskSchemaType.BOOLEAN,
)

_CHECK_ALIGNED_BASKET = RLBTaskSchema(
    schema_key="aligned_basket",
    prompt="您认为您的机械爪已经对齐篮子以至于您松开夹爪可以使瓶子准确地落入篮子?",
    schema_type=RLBTaskSchemaType.BOOLEAN,
)

USER_NAVIGATE_TO_BASKET_TASK = RLBTask(
    description="任务3: 导航并控制机械爪对齐篮子",
    prompt="您正在操控一台机器人,您可以看到一个顶部视角和一个底部视角,"
           "其中您可以在您的顶部视角中看到您的机械爪和一个篮子."
           "您当前的目标是控制机器人使得篮子与机械爪和瓶子对齐,"
           "为了实现目标,您会分别仔细观察顶部视角与底部视角,"
           "移动机械臂并确保机械爪在全部方向上都与篮子对齐."
           f"{SECURITY_WARNING}"
           "您会仔细观察,并为了安全高效的完成目标而回答以下问题.",
    schema=[
        _CHECK_BASKET,
        _CHECK_HOLDING,
        _CHECK_ALIGNED_BASKET,
        presuppose.CHASSIS_SCHEMA,
    ],
)

######################
# 任务4: 将瓶子放入篮子 #
######################
_CHECK_LINE_UP_ALIGNED = RLBTaskSchema(
    schema_key="line_up_aligned",
    prompt="您认为您的机械爪在前后范围内已经对齐篮子以至于可以将瓶子放入篮子了吗?",
    schema_type=RLBTaskSchemaType.BOOLEAN,
)

_CHECK_LEFT_RIGHT_ALIGNED = RLBTaskSchema(
    schema_key="left_right_aligned",
    prompt="您认为您的机械爪在左右范围内已经对齐篮子以至于可以将瓶子放入篮子了吗?",
    schema_type=RLBTaskSchemaType.BOOLEAN,
)

USER_PUT_TO_BASKET_TASK = RLBTask(
    description="任务4: 将瓶子放入篮子",
    prompt="您正在操控一台机器人,您可以看到一个顶部视角和一个底部视角,"
           "其中您可以在您的顶部视角中看到您的机械爪和篮子."
           "您应当注意到您的爪子上夹着一个瓶子."
           "您当前的目标是使用机械臂将机械爪与瓶子对齐篮子,"
           "使得当机械爪松开时瓶子可以准确落入篮子."
           "为了实现目标,您会分别仔细观察顶部视角与底部视角,"
           "移动机械臂并确保机械爪在全部方向上都与篮子对齐."
           f"{SECURITY_WARNING}"
           "您会仔细观察,并为了安全高效的完成目标而回答以下问题.",
    schema=[
        _CHECK_LINE_UP_ALIGNED,
        _CHECK_LEFT_RIGHT_ALIGNED,
        presuppose.ARM_SCHEMA,
    ]
)

USER_TASK_LIST = [
    USER_NAVIGATE_TO_BOTTLE_TASK,
    USER_ALIGN_TO_BOTTLE_TASK,
    USER_NAVIGATE_TO_BASKET_TASK,
    USER_PUT_TO_BASKET_TASK,
]

_IS_LINE_UP_ALIGNED = RLBTaskSchema(
    schema_key="line_up_aligned",
    prompt="您认为俯视图中的机械爪在前后范围内已经对齐瓶子了吗?",
    schema_type=RLBTaskSchemaType.BOOLEAN,
)

_IS_LEFT_RIGHT_ALIGNED = RLBTaskSchema(
    schema_key="left_right_aligned",
    prompt="您认为俯视图中的机械爪在左右范围内已经对齐瓶子了吗?",
    schema_type=RLBTaskSchemaType.BOOLEAN,
)

_IS_UP_DOWN_ALIGNED = RLBTaskSchema(
    schema_key="up_down_aligned",
    prompt="您认为前视图中的机械爪在上下范围内已经对齐瓶子了吗?",
    schema_type=RLBTaskSchemaType.BOOLEAN,
)

BOTTLE_ALIGNMENT_TASK = RLBTask(
    description="任务0: 将机械爪与瓶子对齐",
    prompt="为了将机械爪对齐瓶子,您会分别观察俯视图与前视图中机械爪与瓶子的位置,"
           "并控制机械臂执行一种操作,使得机械爪与瓶子更加对齐.",
    schema=[
        _IS_LINE_UP_ALIGNED,
        _IS_LEFT_RIGHT_ALIGNED,
        _IS_UP_DOWN_ALIGNED,
        presuppose.ARM_SCHEMA,
    ]
)

NEW_TASK_LIST = [BOTTLE_ALIGNMENT_TASK]

"""
TASKS_EXAMPLE = [
    {
        "name": "任务1: 导航并对齐到最近瓶子处",
        "prompt": "您正在操控一台机器人,您可以看到一个顶部视角和一个底部视角,"
                  "您当前的目标是靠近与您最近的瓶子并控制顶部视角中的机械爪与之对齐."
                  f"{SECURITY_WARNING}"
                  "如果您看到您前方已经无路可走,不妨尝试后退一点."
                  "您只会在前方空间不足的情况下后退来避免发生视野外的碰撞."
                  "如果您未能看到瓶子,不妨略微旋转一下."
                  "您会仔细观察,并为了安全高效的完成目标而回答以下问题.",
        "schema": [
            {
                "key": "reached",
                "prompt": "您看到您的机械爪对齐瓶子了吗?",
                "type": "boolean",
            },
            {
                "key": "action",
                "template": "chassis"
            }
        ]
    },
    {
        "name": "任务2: 使用机械爪抓取瓶子",
        "prompt": "您正在操控一台机器人,您可以看到一个顶部视角和一个底部视角,"
                  "其中您可以在您的顶部视角中看到您的机械爪和一个瓶子."
                  "您当前的目标是使用机械爪将瓶子夹起,"
                  "为了实现目标,您会分别仔细观察顶部视角与底部视角,"
                  "移动机械臂并确保机械爪在全部方向上都与瓶子对齐."
                  f"{SECURITY_WARNING}"
                  "您会仔细观察,并为了安全高效的完成目标而回答以下问题.",
        "schema": [
            {
                "key": "aligned_from_top",
                "prompt": "从顶部视角看,您的机械爪对齐瓶子了吗?",
                "type": "boolean",
            },
            {
                "key": "aligned_from_bottom",
                "prompt": "从底部视角看,您的机械爪对齐瓶子了吗?",
                "type": "boolean",
            },
            {
                "key": "completely_aligned",
                "prompt": "您认为您的机械爪已经足够对齐瓶子以至于可以进行准确的抓取吗?",
                "type": "boolean",
            },
            {
                "key": "action",
                "template": "arm"
            }
        ]
    },
    {
        "name": "任务3: 前往篮子以放置瓶子",
        "prompt": "您正在操控一台机器人,您可以看到一个顶部视角和一个底部视角,"
                  "其中您可以看到您的顶部视角中您的机械爪正抓着一个瓶子."
                  "您当前的目标是控制机器人到达可以松手就将瓶子丢入篮子的位置."
                  f"{SECURITY_WARNING}"
                  "您会仔细观察,并为了安全高效的完成目标而回答以下问题.",
        "schema": [
            {
                "key": "reached",
                "prompt": "您看到篮子了吗?",
                "type": "boolean",
            },
            {
                "key": "is_holding",
                "prompt": "您当前可以看到您的机械爪和瓶子吗?您的机械爪仍然抓着瓶子吗?",
                "type": "boolean",
            },
            {
                "key": "aligned",
                "prompt": "您认为您已经使机械爪对齐了篮子以至于当您释放机械爪时瓶子可以顺利落入篮子?",
            },
            {
                "key": "action",
                "template": "chassis"
            }
        ]
    }
]
"""
