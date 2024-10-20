import asyncio
import json
from typing import Optional

import httpx
import numpy as np

from rlb import DoarRobotAPIClient

from oai_session import AioOAISession
from utils import AioImshow, safe_input

async def input_boolean(prompt: str, default: bool) -> bool:
    command = await safe_input(prompt)
    if command is None or len(command) < 1:
        return default
    if command.lower()[0] == "y":
        return True
    else:
        return False


async def get_all_images(
        client: DoarRobotAPIClient,
        jpeg_quality: int = 80,
        img_max_length: Optional[int] = 320
) -> list[np.ndarray]:
    available_cameras = await client.get_camera_list()

    # 并行请求
    tasks = []
    for camera in available_cameras:
        tasks.append(client.get_camera_image(
            camera,
            quality=jpeg_quality,
            max_length=img_max_length
        ))

    # 等待所有请求完成
    results = await asyncio.gather(*tasks)

    images = []
    # 处理结果
    for camera, image in zip(available_cameras, results):
        if image is not None:
            images.append(image)

    return images

# ROUTE_TO_BOTTLE_SYS = ""
SYSTEM_PROMPT = ("您作为一个谨慎睿智的机器人控制员,负责检查来自于机器人手臂和底盘摄像头所传入的数据.\n"
                 "每次收到任务和图像,您都会客观的认真仔细详尽的分析图像的内容,"
                 "获取与任务相关的数据,并填充到表单中.\n"
                 "除了客观的描述状态,您还会对之前提到的全部情况进行主观分析,判断情况/事件对于任务执行的影响.\n"
                 "您会以不含任何格式的纯JSON格式返回信息与操作,"
                 "您不会使用MarkDown代码块将您需要输出的JSON表单包裹.\n"
                 "您会小心谨慎的进行操作,避免与人或其他物体发生碰撞,您始终将安全放在首位.")
ROUTE_TO_BOTTLE_USR = """
请查阅最新图像数据!
您当前的任务流是: 
1. 找到与您最接近的瓶子,切记不要离开太远
2. 控制小车前往您所确定的瓶子,请优先朝向瓶子,再向前靠近
3. 如果您觉得您与瓶子已经足够靠近,以至于您可以在顶部摄像头中看到,那么请告知我任务完成

您需要以以下格式填充表单:
{
  "top_view_description": "[string] 客观详尽的描述您在顶部摄像头视图中看到了什么.",
  "top_view_insight": "[string] 关于顶部视图您的见解,顶部视图中的内容与任务的详细联系.",
  "bottom_view_description": "[string] 客观详尽的描述您在底部摄像头视图中看到了什么.",
  "bottom_view_insight": "[string] 关于底部视图您的见解,底部视图中的内容与任务的详细联系.",
  "bottle_description": "[string] 客观详尽的描述您所找到的瓶子的特点.或者您还没有找到瓶子?",
  "chassis_action": "[specified string] 您需要从以下单元中选取一个作为此键的值,决定了机器人在下一个步骤中如何行动.应当与任务相关.可用选项: "forward", "backward", "turn_left", "turn_right", "task_finish""
}
"""

HOLD_BOTTLE_USR = """
请查看最新图像数据!
您当前的任务流是: 
1. 确认您面前有一个或多个瓶子
2. 选择并描述您希望抓取的瓶子
3. 建议您先下降高度到靠近地面,避免视觉差导致的定位问题,同时可以使用底部摄像头辅助定位
4. 如果您看到机械爪没有抓到瓶子但是却处于闭合状态,则松开机械爪
5. 综合两个视角的内容,当您认为机械爪已经与瓶子对齐后您可以闭合机械爪
6. 当您确认您已经抓住瓶子后,请告知我任务完成

0. 如果您认为手臂摄像头不处于俯视图(而是平视)请输入up
0. 您可以借助机械爪与瓶身的视觉交汇来确定机械爪与瓶身的相对位置

您需要以以下格式填充表单:
{
  "top_view_description": "[string] 客观详尽的描述您在顶部摄像头视图中看到了什么.",
  "top_view_insight": "[string] 关于顶部视图您的见解,顶部视图中的内容与任务的详细联系.",
  "bottom_view_description": "[string] 客观详尽的描述您在底部摄像头视图中看到了什么.",
  "bottom_view_insight": "[string] 关于底部视图您的见解,底部视图中的内容与任务的详细联系.",
  "bottle_description": "[string] 客观详尽的描述您所希望抓取的目标瓶子的特点.",
  "line_up_attitude": "[string] 您对机械爪与瓶身的前后相对位置的见解.",
  "left_right_attitude": "[string] 您对机械爪与瓶身的左右相对位置的见解.",
  "arm_action": "[specified string] 您需要从以下单元中选取一个作为此键的值,决定了机械臂在下一个步骤中如何行动.应当与任务相关.可用选项: "forward", "backward", "turn_left", "turn_right", "down", "up", "hold", "release", "task_finish""
}
"""

async def process(
        ip: str,
        base_url: str,
        api_key: str,
        port: int = 11451,
        dont_verify: bool = False,
        dont_verify_action: bool = False
) -> None:
    robot = DoarRobotAPIClient()
    await robot.connect(ip, port)

    llm: AioOAISession = AioOAISession(
        base_url=base_url,
        api_key=api_key
    )

    displayer = AioImshow()

    current_task = 1
    retry_count = 0
    try:
        while True:
            try:
                img_prompt = await get_all_images(robot)
                for i, img in enumerate(img_prompt):
                    await displayer.imshow(title=f"Image_{i}", img=img)
                retry_count = 0
            except httpx.TimeoutException:
                if retry_count < 5:
                    retry_count += 1
                    print(f"TimeoutException: {ip}:{port}, retry {retry_count}/5")
                    continue
                else:
                    print(f"TimeoutException: {ip}:{port}")
                    raise

            if current_task == 1:
                user_prompt = ROUTE_TO_BOTTLE_USR
            elif current_task == 2:
                user_prompt = HOLD_BOTTLE_USR
            else:
                raise ValueError("current task not found")

            response = await llm.complete(
                system_prompt=GLOBAL_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                prompt_images=img_prompt,
            )

            print(f"Get Original Response: \n{response}")

            try:
                json_response = json.loads(response)
                print(f"Get JSON Response: \n{json_response}")
            except json.decoder.JSONDecodeError as e:
                print(f"JSONDecodeError: {e},\noriginal output: \n{response}")
                continue

            arm_action = json_response.get("arm_action")
            chassis_action = json_response.get("chassis_action")
            print(f"chassis_action: {chassis_action}")
            if arm_action is not None and arm_action != "" and arm_action != "task_finish":
                print(f"解析到机械臂指令: <{arm_action}>")
                if arm_action == "turn_left":
                    arm_action = "turn_right"
                elif arm_action == "turn_right":
                    arm_action = "turn_left"
                elif arm_action == "forward":
                    arm_action = "backward"
                elif arm_action == "backward":
                    arm_action = "forward"
                if dont_verify_action or await input_boolean(prompt=f"是否执行([y]/n)> ", default=True):
                    status = await robot.arm_parse_prompt(arm_action)
                    print(f"执行结果: {status}")
                    await asyncio.sleep(3)

            if chassis_action is not None and chassis_action != "" and chassis_action != "task_finish":
                print(f"解析到底盘指令: <{chassis_action}>")
                if dont_verify_action or await input_boolean(prompt=f"是否执行([y]/n)> ", default=True):
                    status = await robot.chassis_parse_prompt(chassis_action)
                    print(f"执行结果: {status}")
                    await asyncio.sleep(3)

            if chassis_action == "task_finish" or arm_action == "task_finish":
                print("任务被标记为完成")
                if dont_verify or await input_boolean(prompt="是否执行下一个任务([y]/n)> ", default=True) or dont_verify:
                    current_task += 1
                    continue

            if not dont_verify:
                if not await input_boolean(prompt="继续执行([y]/n)> ", default=True):
                    raise asyncio.CancelledError

    except (asyncio.CancelledError, KeyboardInterrupt):
        await robot.chassis_stop()
    finally:
        await robot.disconnect()

if __name__ == "__main__":
    import os

    IP = "192.168.99.124"
    PORT = 11451
    BASE_URL = "https://apic.ohmygpt.com/v1"
    GLOBAL_SYSTEM_PROMPT = ("您正在操控一台机器人,您可以看到一个顶部视角和一个底部视角,"
                            "")

    api_key = os.getenv("OAI_API_KEY")

    asyncio.run(
        process(
            api_key=api_key,
            base_url=BASE_URL,
            ip=IP,
            port=PORT,
            dont_verify=True,
            dont_verify_action=True
        )
    )
