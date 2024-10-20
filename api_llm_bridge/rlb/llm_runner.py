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
            model_path: str = "Qwen/Qwen2-VL-2B-Instruct",
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

    async def generate(
            self,
            frames: List[np.ndarray],
            question: str,
            max_new_token: int = 1024,
            temperature: float = 0,
    ) -> str:
        if self.model is None or self.processor is None:
            await self.load()

        if max_new_token < 128:
            max_new_token = 128

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
            max_new_tokens=max_new_token,
            temperature=temperature + 1e-6,
            do_sample=temperature <= 0.0
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
                    lora_path="/home/steven/Documents/LLaMA-Factory/saves/qwen2_vl-2b/lora/sft/checkpoint-180"
                )

    # 不使用 LoRA 权重
    # generator = Qwen2VLGenerator()

    # 可以选择在这里预加载模型
    await generator.load()

    image1 = cv2.imread(r"/home/steven/Documents/LLaMA-Factory/data/steven_qwen_vl_lora_prj/images/user_project_63_0.jpg")
    image2 = cv2.imread(r"/home/steven/Documents/LLaMA-Factory/data/steven_qwen_vl_lora_prj/images/user_project_63_1.jpg")
    result = await generator.generate([image1, image2], "您正在操控一台机器人,您可以看到一个顶部视角和一个底部视角,其中您可以在您的顶部视角中看到您的机械爪和一个篮子.您当前的目标是使用机械爪将篮子夹起,为了实现目标,您会分别仔细观察顶部视角与底部视角,移动机械臂并确保机械爪在全部方向上都与篮子对齐.您会选择谨慎的避开可能发生碰撞的人和障碍物,并始终相信安全比任务更重要.您会仔细观察,并为了安全高效的完成目标而回答以下问题.\n您需要根据以下格式以JSON填写表单:\n{'can_see_basket': '[Boolean]: 您当前当前可以在视野中看到篮子吗?', 'is_holding': '[Boolean]: 您当前可以看到您的机械爪和瓶子吗?您的机械爪仍然抓着瓶子吗?', 'aligned_basket': '[Boolean]: 您认为您的机械爪已经对齐篮子以至于您松开夹爪可以使瓶子准确地落入篮子?', 'chassis_action': '[Specified String]: 为了完成任务,您决定向什么方向移动机器人?或是您觉得一切已经就绪了?您必须且只能从以下选项中选择一种操作来填写该键:forward,backward,turn_left,turn_right,task_finish'}")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
