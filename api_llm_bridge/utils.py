import time
from typing import Optional, Callable
import asyncio

import cv2
import numpy as np
import aioconsole


async def safe_input(prompt: str = "> ", timeout: float = 0.1):
    while True:
        t = time.time()
        resout = await aioconsole.ainput(prompt)
        if time.time() - t > timeout:
            break
        print("内部错误,请重试")

    return resout

class AioImshow:
    def __init__(self, exit_key: int = 27, exit_callback: Optional[Callable] = None):
        self.cv2_task: Optional[asyncio.Task] = None
        self.exit_key = exit_key
        self.windows = {}
        self.exit_callback = exit_callback

    async def imshow(self, title: str, img: np.ndarray):

        if self.cv2_task is None:
            self.cv2_task = asyncio.create_task(self._cv2_loop())

        self.windows[title] = img
        cv2.imshow(title, img)

    async def destroy(self, title: str = None):
        if self.exit_callback:
            self.exit_callback()
        if title:
            if title in self.windows:
                cv2.destroyWindow(title)
                del self.windows[title]
        else:
            cv2.destroyAllWindows()
            self.windows.clear()

        if not self.windows and self.cv2_task:
            self.cv2_task.cancel()
            self.cv2_task = None

    async def _cv2_loop(self):
        while True:
            if cv2.waitKey(1) & 0xFF == self.exit_key:
                await self.destroy()
                break
            await asyncio.sleep(0)