import base64
from typing import List, Optional

import cv2
import numpy as np
from openai import AsyncOpenAI


class AioOAISession:
    def __init__(self, base_url: str, api_key: str):
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)

    def _encode_image(self, image: np.ndarray, quality: int = 99) -> str:
        _, encoded = cv2.imencode('.jpg', image, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        return base64.b64encode(encoded).decode("utf-8")

    async def complete(self,
                       system_prompt: str,
                       user_prompt: str,
                       prompt_images: Optional[List[np.ndarray]] = None,
                       jpeg_quality: int = 99,
                       seed: int = 0,
                       temperature: float = 0,
                       top_p: float = 0.5,
                       model: str = "gpt-4o",
                       max_completion_tokens: int = 2048) -> str:

        # 构造用户内容列表
        user_content = [{"type": "text", "text": user_prompt}]

        if prompt_images:
            for image in prompt_images:
                base64_image = self._encode_image(image, jpeg_quality)
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                })

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        completion = await self.client.chat.completions.create(
            seed=seed,
            temperature=temperature,
            top_p=top_p,
            model=model,
            messages=messages,
            max_tokens=max_completion_tokens
        )

        print(f"Tokens used: {completion.usage.prompt_tokens} + {completion.usage.completion_tokens} + "
              f"{completion.usage.total_tokens}")
        print(f"References: "
              f"${completion.usage.prompt_tokens / 1000 * 0.00250:.2f}"
              f" + "
              f"${completion.usage.completion_tokens / 1000 * 0.01000:.2f}"
              f" = "
              f"${completion.usage.prompt_tokens / 1000 * 0.00250 + completion.usage.completion_tokens / 1000 * 0.01000:.2f}")

        return completion.choices[0].message.content


# 使用示例
import asyncio


async def main():
    BASE_URL = "https://apic.ohmygpt.com/v1"
    API_KEY = "sk-***"

    analyzer = AioOAISession(BASE_URL, API_KEY)

    SYSTEM_PROMPT = "Your system prompt here"
    USER_PROMPT = "Your user prompt here"

    # 读取图像
    image1 = cv2.imread(r"path_to_image1.jpg")
    image2 = cv2.imread(r"path_to_image2.jpg")

    result = await analyzer.complete(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=USER_PROMPT,
        prompt_images=[image1, image2],
        jpeg_quality=99,
        seed=0,
        temperature=0,
        top_p=0.5,
        model="gpt-4o",
        max_completion_tokens=2048
    )

    print(result)


if __name__ == "__main__":
    asyncio.run(main())
