import asyncio
import base64
from typing import Optional, List

import httpx
import numpy as np
import cv2

class DoarRobotAPIClient:
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    async def connect(self, server_ip, server_port=11451):
        self._client = httpx.AsyncClient(
            base_url=f"http://{server_ip}:{server_port}"
        )

    async def disconnect(self):
        if self._client:
            await self._client.aclose()

    async def ping(self) -> str:
        response = await self._client.get("/ping")
        return response.text

    async def get_camera_list(self) -> List[str]:
        response = await self._client.get("/camera/list")
        data = response.json()
        return data["nodes"]

    async def get_camera_image(self, camera_node_name: str, quality: int = 90,
                               max_length: Optional[int] = None, encoding: str = "utf-8") -> Optional[np.ndarray]:
        params = {
            "quality": quality,
            "encoding": encoding
        }
        if max_length:
            params["max_length"] = max_length

        response = await self._client.get(f"/camera/node/{camera_node_name}", params=params)
        base64_img = response.json().get("image")
        if base64_img:
            img_data = base64.b64decode(base64_img)
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return img
        else:
            return None

    async def arm_move(self, prompt: str) -> str:
        response = await self._client.post(f"/arm/{prompt}")
        return response.text

    async def chassis_move(self, prompt: str) -> str:
        response = await self._client.post(f"/chassis/{prompt}")
        return response.text

    # Arm movement convenience methods
    async def arm_forward(self) -> str:
        return await self.arm_move("forward")

    async def arm_backward(self) -> str:
        return await self.arm_move("backward")

    async def arm_turn_left(self) -> str:
        return await self.arm_move("turn_left")

    async def arm_turn_right(self) -> str:
        return await self.arm_move("turn_right")

    async def arm_down(self) -> str:
        return await self.arm_move("down")

    async def arm_up(self) -> str:
        return await self.arm_move("up")

    async def arm_hold(self) -> str:
        return await self.arm_move("hold")

    async def arm_release(self) -> str:
        return await self.arm_move("release")

    async def arm_set_home(self) -> str:
        return await self.arm_move("set_home")

    async def arm_go_home(self) -> str:
        return await self.arm_move("go_home")

    # Chassis movement convenience methods
    async def chassis_forward(self) -> str:
        return await self.chassis_move("forward")

    async def chassis_backward(self) -> str:
        return await self.chassis_move("backward")

    async def chassis_turn_left(self) -> str:
        return await self.chassis_move("turn_left")

    async def chassis_turn_right(self) -> str:
        return await self.chassis_move("turn_right")

    async def chassis_stop(self) -> str:
        return await self.chassis_move("stop")

    async def chassis_parse_prompt(self, prompt: str) -> str:
        prompt_func_map = {
            "forward": self.chassis_forward,
            "backward": self.chassis_backward,
            "turn_left": self.chassis_turn_left,
            "turn_right": self.chassis_turn_right,
            "stop": self.chassis_stop,
        }

        target_func = prompt_func_map.get(prompt.lower())
        if target_func:
            return await target_func()
        else:
            return "Error: prompt not found"

    async def arm_parse_prompt(self, prompt: str) -> str:
        prompt_func_map = {
            "forward": self.arm_forward,
            "backward": self.arm_backward,
            "turn_left": self.arm_turn_left,
            "turn_right": self.arm_turn_right,
            "down": self.arm_down,
            "up": self.arm_up,
            "hold": self.arm_hold,
            "release": self.arm_release,
            "set_home": self.arm_set_home,
            "go_home": self.arm_go_home
        }

        target_func = prompt_func_map.get(prompt.lower())
        if target_func:
            return await target_func()
        else:
            return "Error: prompt not found"


async def _test():
    client = DoarRobotAPIClient()
    await client.connect("192.168.99.124", 11451)

    try:
        while True:
            available_cameras = await client.get_camera_list()

            # 并行请求
            tasks = []
            for camera in available_cameras:
                tasks.append(client.get_camera_image(camera, quality=JPEG_QUALITY, max_length=IMG_MAX_LENGTH))

            # 等待所有请求完成
            results = await asyncio.gather(*tasks)

            # 处理结果
            for camera, image in zip(available_cameras, results):
                if image is not None:
                    cv2.imshow(f"Camera: {camera}", image)

            # 检查是否按下 'q' 键退出
            key = cv2.waitKey(1)
            key = key & 0xFF
            if key == 27:
                break
            elif key == ord('w'):
                await client.chassis_forward()
            elif key == ord('s'):
                await client.chassis_backward()
            elif key == ord('a'):
                await client.chassis_turn_left()
            elif key == ord('d'):
                await client.chassis_turn_right()
            elif key == ord(' '):
                await client.chassis_stop()

            elif key == ord('q'):
                await client.arm_release()
            elif key == ord('e'):
                await client.arm_hold()
            elif key == ord('i'):
                await client.arm_forward()
            elif key == ord('k'):
                await client.arm_backward()
            elif key == ord("u"):
                await client.arm_up()
            elif key == ord("o"):
                await client.arm_down()
            elif key == ord("j"):
                await client.arm_turn_left()
            elif key == ord("l"):
                await client.arm_turn_right()
            elif key == ord("z"):
                await client.arm_set_home()
            elif key == ord("x"):
                await client.arm_go_home()

            await asyncio.sleep(0)

    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        await client.disconnect()
        # 关闭所有OpenCV窗口
        cv2.destroyAllWindows()

if __name__ == "__main__":
    JPEG_QUALITY = 80
    IMG_MAX_LENGTH = 320

    asyncio.run(_test())
