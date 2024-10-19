import asyncio
import os
import time

import aioconsole

from rlb import RLBTask, RLBTaskSchema, RLBTaskSchemaType, DoarRobotAPIClient
from dataset_bulider import DatasetManager
from utils import AioImshow, safe_input

async def record(
        tasks: list[RLBTask],
        ip: str,
        port: int = 11451,
        save_dir: str = r"./records",
        project_name: str = "elb_example",
):
    # save_dir = f"{save_dir}/{project_name}"
    save_dir = os.path.join(save_dir, project_name)

    client = DoarRobotAPIClient()
    await client.connect(ip, port)

    dataset_manager = DatasetManager(target_folder=save_dir, project_name=project_name)

    displayer = AioImshow()

    args_history: dict[str, any] = {
        "step": 0
    }

    try:
        while True:
            available_cameras = await client.get_camera_list()

            current_images = []

            # 并行请求
            r_tasks = []
            for camera in available_cameras:
                r_tasks.append(client.get_camera_image(camera, quality=JPEG_QUALITY, max_length=IMG_MAX_LENGTH))

            # 等待所有请求完成
            results = await asyncio.gather(*r_tasks)

            # 处理结果
            for camera, image in zip(available_cameras, results):
                if image is not None:
                    current_images.append(image)
                    await displayer.imshow(f"Camera: {camera}", image)

            print(f"\n当前阶段为总共{len(tasks)}个阶段中的"
                  f"[{args_history.get('step', '不可用')}]:" ,end="")
            while True:
                last_input_at = time.time()
                result = await aioconsole.ainput("> ")
                if time.time() - last_input_at > 1:
                    break
                print("内部错误,请重试")
            if result is None or result == "":
                result = args_history.get("step", 1)
            try:
                args_history["step"] = result
                result = int(result)
                if result < 1:
                    # 视作用户主动退出
                    raise KeyboardInterrupt
                current_task: RLBTask = tasks[result - 1]
            except (ValueError, IndexError):
                print("您输入的数据无效")
                continue

            task_description = current_task.description
            user_prompt = current_task.to_prompt()
            print()
            print(f"您选择的任务为: {task_description}, "
                  f"含有 {len(current_task.schema)} 个参数,请配置参数.")

            schema_args = {}
            arm_prompt = None
            choice_prompt = None
            for i, schema in enumerate(current_task.schema):
                schema: RLBTaskSchema
                history = args_history.get(
                    f"step{i + 1}_{schema.schema_key}",
                    None
                )
                history = str(history) if history is not None else None
                _available_choices = ','.join(schema.choice) + '\n' \
                    if schema.schema_type == RLBTaskSchemaType.CHOICE \
                    else ''
                print(f"-----\n"
                      f"正在接收第 {i + 1} 个参数, 参数名为: {schema.schema_key}, "
                      f"目标类型为: {schema.schema_type.name}:\n"
                      f"{schema.prompt}\n"
                      f"可用选项为: {_available_choices}"
                      f"[{history or '无历史'}] ", end="")
                # while True:
                #     last_input_at = time.time()
                #     result = await aioconsole.ainput("> ")
                #     if time.time() - last_input_at > 1:
                #         break
                #     print("内部错误,请重试")
                result = await safe_input()

                if result is None or result == "":
                    result = history

                try:
                    if schema.schema_type == RLBTaskSchemaType.BOOLEAN:
                        result = str(result).lower() == "true"
                    elif schema.schema_type == RLBTaskSchemaType.INT:
                        result = int(result)
                    elif schema.schema_type == RLBTaskSchemaType.CHOICE:
                        result = str(result).strip()
                        if result not in schema.choice:
                            raise ValueError(f"您输入的数据不在可用选项中")

                        if schema.presuppose_name == "ARM_SCHEMA":
                            print(f"识别此命令为机械臂控制: {result}")
                            arm_prompt = result
                        elif schema.presuppose_name == "CHASSIS_SCHEMA":
                            print(f"识别此命令为底盘控制: {result}")
                            choice_prompt = result
                    else:
                        result = str(result)

                    print(f"解析为: {type(result)}: {result}")

                    args_history[f"step{i + 1}_{schema.schema_key}"] = result

                    schema_args[schema.schema_key] = result

                except ValueError:
                    print("您输入的数据无效")
                    continue

            try:
                assistant_response = current_task.prefill_response(schema_args)
            except ValueError as e:
                print(f"无法生成记录,本次操作将不会被记录,原因：{e}")
                continue

            print(f"\n生成完成:\n"
                  f"User Prompt> \n{user_prompt}\n"
                  f"Assistant Response> \n{assistant_response}\n")

            dataset_manager.append_data(
                user_prompt=user_prompt,
                assistant=assistant_response,
                images=current_images
            )

            if arm_prompt is not None:
                print(f"您希望执行你输入的机械臂命令<{arm_prompt}>或是覆写其吗?")
            print(f"在此处执行机械臂命令[{arm_prompt}]", end="")
            result = await safe_input()
            if result is None or result == "":
                result = arm_prompt
            if result is not None and result != "task_finish":
                print(await client.arm_parse_prompt(result))
                await asyncio.sleep(3)

            if choice_prompt is not None:
                print(f"您希望执行你输入的底盘命令<{choice_prompt}>或是覆写其吗?")
            print(f"在此处执行底盘命令[{choice_prompt}]", end="")
            # while True:
            #     last_input_at = time.time()
            #     result = await aioconsole.ainput("> ")
            #     if time.time() - last_input_at > 1:
            #         break
            #     print("内部错误,请重试")
            result = await safe_input()
            if result is None or result == "":
                result = choice_prompt
            if result is not None and result != "task_finish":
                print(await client.chassis_parse_prompt(result))
                await asyncio.sleep(3)


    except (KeyboardInterrupt, asyncio.exceptions.CancelledError):
        pass
    finally:
        await displayer.destroy()
        await client.disconnect()


if __name__ == "__main__":
    from tasks import USER_TASK_LIST

    JPEG_QUALITY = 80
    IMG_MAX_LENGTH = 320
    SAVE_DIR = r"./recorded_dataset"
    PROJECT_NAME = "user_project"

    asyncio.run(record(USER_TASK_LIST, "192.168.99.124", save_dir=SAVE_DIR, project_name=PROJECT_NAME))
