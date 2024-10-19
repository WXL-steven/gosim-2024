import asyncio
from typing import List, Dict, Optional
import numpy as np
from PIL import Image
import cv2
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info


class Qwen2VLGenerator:
    def __init__(
            self,
            model_path: str = "qwen/qwen-vl-base",
            lora_path: Optional[str] = None
    ):
        self.model_path = model_path
        self.lora_path = lora_path
        self.model = None
        self.processor = None

    async def load(self):
        if self.model is None:
            self.model = await asyncio.to_thread(self._load_model)
        if self.processor is None:
            self.processor = await asyncio.to_thread(AutoProcessor.from_pretrained, self.model_path)

    def _load_model(self):
        try:
            import flash_attn as _
            model = Qwen2VLForConditionalGeneration.from_pretrained(
                self.model_path,
                torch_dtype="auto",
                device_map="auto",
                attn_implementation="flash_attention_2",
            )
        except (ImportError, ModuleNotFoundError):
            model = Qwen2VLForConditionalGeneration.from_pretrained(
                self.model_path,
                torch_dtype="auto",
                device_map="auto",
            )

        if self.lora_path:
            model.load_adapter(self.lora_path)

        return model

    async def _preprocess_images(self, frames: List[np.ndarray]) -> Dict[str, Image.Image]:
        def convert_image(idx: int, frame: np.ndarray) -> tuple:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)
            return (str(idx), pil_image)

        tasks = [asyncio.to_thread(convert_image, idx, frame) for idx, frame in enumerate(frames)]
        results = await asyncio.gather(*tasks)
        return dict(results)

    async def generate(self, frames: List[np.ndarray], question: str) -> str:
        if self.model is None or self.processor is None:
            await self.load()

        processed_frames = await self._preprocess_images(frames)

        messages = [
            {
                "role": "user",
                "content": [
                               {
                                   "type": "image",
                                   "image": image,
                               }
                               for image in processed_frames.values()
                           ]
                           + [
                               {"type": "text", "text": question},
                           ],
            }
        ]

        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = await asyncio.to_thread(
            self.processor,
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
        inputs = inputs.to("cuda")

        generated_ids = await asyncio.to_thread(
            self.model.generate,
            **inputs,
            max_new_tokens=128
        )
        generated_ids_trimmed = [
            out_ids[len(in_ids):]
            for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        output_text = await asyncio.to_thread(
            self.processor.batch_decode,
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )

        return output_text[0]


async def main():
    # 使用 LoRA 权重
    # generator = Qwen2VLGenerator(lora_path="path/to/your/lora/weights")
    # /home/steven/Documents/Models/Qwen2-VL-2B-Instruct
    generator = Qwen2VLGenerator(
                    model_path="/home/steven/Documents/Models/Qwen2-VL-2B-Instruct",
                    lora_path=None
                )

    # 不使用 LoRA 权重
    # generator = Qwen2VLGenerator()

    # 可以选择在这里预加载模型
    # await generator.load()

    image = cv2.imread(r"./image.jpeg")
    result = await generator.generate([image], "您在这些/张图像中(分别)看到了什么内容？")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
