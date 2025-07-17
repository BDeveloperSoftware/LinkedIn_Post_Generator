from openai import OpenAI as OpenAIClient
from groq import Groq as GroqClient
import streamlit as st
import os

class PostGenerator:
    def _init_(self, model_provider='openai'):
        self.model_provider = model_provider.lower()
        self.OPENAI_API_KEY = st.secrets["api"]["OPENAI_API_KEY"]
        self.GROQ_API_KEY = st.secrets["api"]["GROQ_API_KEY"]
        self.api_key = self.OPENAI_API_KEY if self.model_provider == "openai" else self.GROQ_API_KEY
        self.client = self._init_client()
        self.clint_image = OpenAIClient(api_key=self.OPENAI_API_KEY)

    def _init_client(self):
        if self.model_provider == "openai":
            return OpenAIClient(api_key=self.api_key)
        elif self.model_provider == "LLaMA-3-70B":
            return GroqClient(api_key=self.api_key)
        else:
            raise ValueError("Unsupported model provider")

    def generate_post_text(self, article_prompt):
        model = "gpt-4-turbo" if self.model_provider == "GPT-4-Turbo" else "llama3-70b-8192"
        full_prompt = f"""
                Here is a sample of previous successful LinkedIn posts for inspiration(tone, style, length, etc.):
                {article_prompt}
                At the bottom, add 6-8 relevant hashtags related to the topic (like #AI, #TechTrends). Only put hashtags here, not in the main body.
                """
        messages = [{"role": "user", "content": full_prompt}]
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()

    def generate_image(self, prompt):
        response = self.clint_image.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1792x1024",
            quality="standard",
            n=1
        )
        return response.data[0].url
