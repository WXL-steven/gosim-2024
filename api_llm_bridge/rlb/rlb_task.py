import enum
import json
from typing import Optional

CHOICE_PADDING = "您必须从以下选项中选择一种操作:"
PROMPT_SCHEMA_PADDING = "您需要根据以下格式以JSON填写表单:"


class RLBTaskSchemaType(enum.Enum):
    CHOICE = "Specified String"
    TEXT = "String"
    BOOLEAN = "Boolean"
    INT = "Integer"


class RLBTaskSchema:
    def __init__(
            self,
            schema_key: str,
            prompt: str,
            schema_type: RLBTaskSchemaType,
            choice: Optional[list[str]] = None,
            choice_padding: str = "您必须且只能从以下选项中选择一种操作来填写该键:",
            presuppose_name: str = "",
    ):
        self.schema_key = schema_key
        self.prompt = prompt
        self.schema_type = schema_type
        self.choice_padding = choice_padding
        self.presuppose_name = presuppose_name
        if schema_type != RLBTaskSchemaType.CHOICE:
            self.choice = None
        elif choice is None or len(choice) == 0:
            raise ValueError("For SchemaType.CHOICE, choice must be provided")
        else:
            self.choice = choice

    def to_serializable(self) -> dict[str, any]:
        if self.schema_type == RLBTaskSchemaType.CHOICE:
            serializable = {
                self.schema_key: f"[{self.schema_type.value}]: {self.prompt}"
                                 f"{self.choice_padding}"
                                 f"{','.join(self.choice)}"}
        else:
            serializable = {
                self.schema_key: f"[{self.schema_type.value}]: {self.prompt}"
            }

        return serializable


class RLBTask:
    def __init__(
            self,
            description: str,
            prompt: str,
            schema: list[RLBTaskSchema],
            prompt_schema_padding: str = PROMPT_SCHEMA_PADDING,
    ):
        self.description = description
        self.prompt = prompt
        self.schema = schema
        self.ps_padding = prompt_schema_padding

        self.schema_prompts_dict = {}
        for schema in self.schema:
            self.schema_prompts_dict.update(schema.to_serializable())

        self.schema_prompts = json.dumps(self.schema_prompts_dict)

    def to_prompt(self) -> str:
        return f"{self.prompt}\n{self.ps_padding}\n{self.schema_prompts_dict}"

    def prefill_response(self, schema_values: dict[str, any]) -> str:
        serializable = {}
        for schema in self.schema:
            current_key = schema.schema_key
            current_value = schema_values.get(current_key, None)

            if current_value is None:
                raise ValueError(f"No value provided for key: {current_key}")

            if schema.schema_type == RLBTaskSchemaType.CHOICE:
                if current_value not in schema.choice:
                    raise ValueError(f"Invalid value: {current_value} for key: {current_key}."
                                     f"Only {schema.choice} are allowed.")

            if schema.schema_type == RLBTaskSchemaType.BOOLEAN:
                if not isinstance(current_value, bool):
                    raise ValueError(f"Invalid value: {current_value} for key: {current_key}."
                                     f"Only boolean values are allowed.")

            if schema.schema_type == RLBTaskSchemaType.INT:
                if not isinstance(current_value, int):
                    raise ValueError(f"Invalid value: {current_value} for key: {current_key}."
                                     f"Only integer values are allowed.")

            serializable[current_key] = current_value

        return json.dumps(serializable)


def _test():
    check_reached = RLBTaskSchema(
        schema_key="reached",
        prompt="您看到您的机械爪对齐瓶子了吗?",
        schema_type=RLBTaskSchemaType.BOOLEAN,
    )

    print(check_reached.to_serializable())

    chassis_action = RLBTaskSchema(
        schema_key="action",
        prompt="您为了完成任务,您决定向什么方向移动?或是您觉得一切已经就绪了?",
        schema_type=RLBTaskSchemaType.CHOICE,
        choice=["forward", "backward", "turn_left", "turn_right", "task_finish"],
    )

    print(chassis_action.to_serializable())

    reach_bottle_task = RLBTask(
        description="任务1: 靠近并对齐瓶子",
        prompt="您正在操控一台机器人,您可以看到一个顶部视角和一个底部视角,"
               "您当前的目标是靠近与您最近的瓶子并控制顶部视角中的机械爪与之对齐."
               "您会选择谨慎的避开可能发生碰撞的人和障碍物,并始终相信安全比任务更重要."
               "如果您看到您前方已经无路可走,不妨尝试后退一点."
               "您只会在前方空间不足的情况下后退来避免发生视野外的碰撞."
               "如果您未能看到瓶子,不妨略微旋转一下."
               "您会仔细观察,并为了安全高效的完成目标而回答以下问题.",
        schema=[check_reached, chassis_action],
    )

    print()
    print(reach_bottle_task.to_prompt())

    example_values = {
        "reached": False,
        "action": "forward",
    }

    print()
    print(reach_bottle_task.prefill_response(example_values))


if __name__ == "__main__":
    _test()
