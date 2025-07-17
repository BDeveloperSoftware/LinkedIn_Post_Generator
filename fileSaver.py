# file_saver.py

import os
from datetime import datetime
import requests
from uuid import uuid4

class SimpleSaver:
    def __init__(self):
        self.download_dir = os.path.join(os.path.expanduser("~"), "Downloads")

    def save_post(self, post_text, image_url=None):
        folder_name = f"Post_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid4())[:8]}"
        folder_path = os.path.join(self.download_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        # Save post text
        text_path = os.path.join(folder_path, "LinkedIn_Post.txt")
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(post_text)

        # Save image only if valid URL is provided
        if image_url and isinstance(image_url, str) and image_url.startswith("http"):
            try:
                response = requests.get(image_url, timeout=10)
                if response.status_code == 200:
                    image_path = os.path.join(folder_path, "Image.png")
                    with open(image_path, "wb") as f:
                        f.write(response.content)
                else:
                    print(f"⚠️ Image download failed: status code {response.status_code}")
            except Exception as e:
                print(f"⚠️ Exception while downloading image: {e}")
        else:
            print("ℹ️ No valid image URL provided. Skipping image save.")
