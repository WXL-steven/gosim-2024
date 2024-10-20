import asyncio
import json
from typing import Optional

import httpx
import numpy as np

from rlb import DoarRobotAPIClient
from rlb.llm_runner import Qwen2VLGenerator

from recorder import safe_input
from tasks import (USER_NAVIGATE_TO_BASKET_TASK,
                   USER_ALIGN_TO_BOTTLE_TASK,
                   USER_NAVIGATE_TO_BOTTLE_TASK,
                   BOTTLE_ALIGNMENT_TASK)


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
        img_max_length: Optional[int] = 640
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


async def process(
        ip: str,
        port: int = 11451,
        model_path: str = "Qwen/Qwen2-VL-2B-Instruct",
        lora_path: Optional[str] = None,
        simulate_llm: bool = False
) -> None:
    robot = DoarRobotAPIClient()
    await robot.connect(ip, port)

    llm: Optional[Qwen2VLGenerator] = None  # For static analysis
    if not simulate_llm:
        llm = Qwen2VLGenerator(model_path=model_path, lora_path=lora_path)
        await llm.load()

    current_task = BOTTLE_ALIGNMENT_TASK
    retry_count = 0
    user_prompt = current_task.to_prompt()
    try:
        while True:
            try:
                img_prompt = await get_all_images(robot)
                retry_count = 0
            except httpx.TimeoutException:
                if retry_count < 5:
                    retry_count += 1
                    print(f"TimeoutException: {ip}:{port}, retry {retry_count}/5")
                    continue
                else:
                    print(f"TimeoutException: {ip}:{port}")
                    raise

            if not simulate_llm:
                response = await llm.generate(frames=img_prompt, question=user_prompt)
            else:
                print(f"\n模拟请求:\n{user_prompt}")
                response = await safe_input("请输入模拟响应> ")

            try:
                json_response = json.loads(response)
            except json.decoder.JSONDecodeError:
                print(f"JSONDecodeError: {response},\noriginal output: \n{response}")
                continue

            arm_action = json_response.get("arm_action")
            chassis_action = json_response.get("chassis_action")
            if arm_action is not None or arm_action != "" or arm_action != "task_finish":
                print(f"解析到机械臂指令: <{arm_action}>")
                if await input_boolean(prompt=f"是否执行([y]/n)> ", default=True):
                    status = await robot.arm_parse_prompt(arm_action)
                    print(f"执行结果: {status}")

            if chassis_action is not None or chassis_action != "" or chassis_action != "task_finish":
                print(f"解析到底盘指令: <{chassis_action}>")
                if await input_boolean(prompt=f"是否执行([y]/n)> ", default=True):
                    status = await robot.chassis_parse_prompt(chassis_action)
                    print(f"执行结果: {status}")

            if current_task is USER_NAVIGATE_TO_BOTTLE_TASK:
                if json_response.get("reached") == True and chassis_action == "task_finish":
                    print(f"指出任务 {current_task.name} 完成")
                    if input_boolean(prompt="是否进入下一个任务([y]/n)> ", default=True):
                        current_task = USER_ALIGN_TO_BOTTLE_TASK

            if current_task is USER_ALIGN_TO_BOTTLE_TASK:
                if json_response.get("arm_aligned") == True \
                    and arm_action == "task_finish":
                    print(f"指出任务 {current_task.name} 完成")
                    if input_boolean(prompt="是否进入下一个任务([y]/n)> ", default=True):
                        current_task = USER_NAVIGATE_TO_BASKET_TASK
                    if input_boolean(prompt="是否执行机械爪抓取([y]/n)> ", default=True):
                        status = await robot.arm_hold()
                        print(f"执行结果: {status}")
                    if input_boolean(prompt="是否执行机械臂Go Home([y]/n)> ", default=True):
                        status = await robot.arm_go_home()
                        print(f"执行结果: {status}")

            if current_task is USER_NAVIGATE_TO_BASKET_TASK:
                if json_response.get("aligned_basket") == True \
                        and chassis_action == "task_finish":
                    print(f"指出任务 {current_task.name} 完成")
                    if input_boolean(prompt="是否进入下一个任务([y]/n)> ", default=True):
                        current_task = USER_NAVIGATE_TO_BOTTLE_TASK
                elif not json_response.get("is_holding"):
                    print(f"指出物品掉落")
                    if input_boolean(prompt="是否返回首个任务([y]/n)> ", default=True):
                        current_task = USER_NAVIGATE_TO_BOTTLE_TASK

            if current_task is BOTTLE_ALIGNMENT_TASK:
                if json_response.get("arm_aligned"):
                    if input_boolean(prompt="是否执行机械爪抓取([y]/n)> ", default=True):
                        status = await robot.arm_hold()
                        print(f"执行结果: {status}")
                    if input_boolean(prompt="是否松开机械爪([y]/n)> ", default=True):
                        status = await robot.arm_release()
                        print(f"执行结果: {status}")

    except (asyncio.CancelledError, KeyboardInterrupt):
        await robot.chassis_stop()
    finally:
        await robot.disconnect()

if __name__ == "__main__":
    IP = "192.168.99.124"
    PORT = 11451

    asyncio.run(process(ip=IP, port=PORT))
