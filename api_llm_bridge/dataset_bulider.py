import os
import json
import cv2
import numpy as np
from typing import List


class DatasetManager:
    def __init__(self, target_folder: str, project_name: str):
        self.target_folder = target_folder
        self.project_name = project_name
        self.images_folder = os.path.join(target_folder, 'images')
        self.json_file = os.path.join(target_folder, f'{project_name}.json')

        # 创建必要的目录
        os.makedirs(self.target_folder, exist_ok=True)
        os.makedirs(self.images_folder, exist_ok=True)

        # 如果JSON文件不存在，创建一个空列表
        if not os.path.exists(self.json_file):
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def append_data(self, user_prompt: str, assistant: str, images: List[np.ndarray]):
        # 读取现有数据
        with open(self.json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # # 创建新的数据条目
        # new_entry = {
        #     "messages": [
        #         {"content": f"<image>{user_prompt}", "role": "user"},
        #         {"content": assistant, "role": "assistant"}
        #     ],
        #     "images": []
        # }
        image_tags = '<image>' * len(images)
        new_entry = {
            "messages": [
                {"content": f"{image_tags}{user_prompt}", "role": "user"},
                {"content": assistant, "role": "assistant"}
            ],
            "images": []
        }

        # 保存图像并更新图像路径
        for i, img in enumerate(images):
            img_filename = f"{self.project_name}_{len(data)}_{i}.jpg"
            img_path = os.path.join(self.images_folder, img_filename)
            cv2.imwrite(img_path, img)
            new_entry["images"].append(f"images/{img_filename}")

        # 添加新条目到数据中
        data.append(new_entry)

        # 保存更新后的数据
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_data(self):
        with open(self.json_file, 'r', encoding='utf-8') as f:
            return json.load(f)


# 使用示例
if __name__ == "__main__":
    manager = DatasetManager("path/to/target/folder", "my_project")

    # 假设我们有一些图像数据
    image1 = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    image2 = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

    manager.append_data(
        user_prompt="Who are they?",
        assistant="They're Kane and Gretzka from Bayern Munich.",
        images=[image1, image2]
    )

    # 打印当前数据集内容
    print(manager.get_data())
