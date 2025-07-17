# file_saver.py

import requests
import streamlit as st
import io
import zipfile

class SimpleSaver:
    def _init_(self):
        pass  # No local saving

    def save_post(self, post_text, image_url=None):
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            # Add post text to zip
            zip_file.writestr("LinkedIn_Post.txt", post_text)

            # Add image to zip if valid
            if image_url and isinstance(image_url, str) and image_url.startswith("http"):
                try:
                    response = requests.get(image_url, timeout=10)
                    if response.status_code == 200:
                        zip_file.writestr("Image.png", response.content)
                    else:
                        st.warning(f"⚠ Image download failed: status code {response.status_code}")
                except Exception as e:
                    st.warning(f"⚠ Exception while downloading image: {e}")
            else:
                st.info("ℹ No valid image URL provided. Image not included.")

        zip_buffer.seek(0)

        st.download_button(
            label="📦 Download Post + Image (ZIP)",
            data=zip_buffer,
            file_name="LinkedIn_Post_Package.zip",
            mime="application/zip"
        )
