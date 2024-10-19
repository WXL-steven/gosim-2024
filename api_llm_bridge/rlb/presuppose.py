from .rlb_task import RLBTaskSchema, RLBTaskSchemaType


ARM_SCHEMA = RLBTaskSchema(
    schema_key="action",
    prompt="为了完成任务,您决定向什么方向移动机械爪?或是您觉得一切已经就绪了?",
    schema_type=RLBTaskSchemaType.CHOICE,
    choice=["forward", "backward", "turn_left", "turn_right", "down", "up", "task_finish"],
    presuppose_name="ARM_SCHEMA",
)

CHASSIS_SCHEMA = RLBTaskSchema(
    schema_key="action",
    prompt="为了完成任务,您决定向什么方向移动机器人?或是您觉得一切已经就绪了?",
    schema_type=RLBTaskSchemaType.CHOICE,
    choice=["forward", "backward", "turn_left", "turn_right", "task_finish"],
    presuppose_name="CHASSIS_SCHEMA",
)
