# main.py

from datetime import datetime
import streamlit as st
from jinja2 import Template
from fileSaver import SimpleSaver
from postgenerator import PostGenerator
from newsscrapper import GNewsAgent
from data_collection import TLDRNewsFetcher
import io
import zipfile
import requests

# ─── Security Check (Passkey via URL) ────────────────────────────────────────
query_params = st.query_params
user_key = query_params.get("key", None)
required_key = st.secrets["security"]["access_key"]

if user_key != required_key:
    st.error("🔒 Access Denied: Invalid or missing key in URL.")
    st.stop()

# ─── Local Saver & News Setup ───────────────────────────────────────────────
saver = SimpleSaver()
news_agent = GNewsAgent()
tldr_agent = TLDRNewsFetcher()

# ─── Prompt templates ───────────────────────────────────────────────────────
BASE_REQUIREMENTS = """
1. Professional, engaging, attention grabbing.
2. Structure:
   • Hook  
   • 2 ,3 value bullets / paragraphs  
   • Takeaway / insight  
   • CTA
3. Tone: professional, authentic, lightly conversational.
4. No repetition; every sentence adds value.
5. ≤ {word_limit} words.
6. *Do not* include hashtags, links, “thank you”, “sorry”, or emojis beyond 1-2 tasteful ones.
"""

POST_TEMPLATE = """
You are a LinkedIn content strategist.

Craft a high quality post on *{{ topic }}* for *{{ audience }}*.
 
Context:
• Location: {{ location }}
• Scheduled date: {{ post_date }}

{{ requirements }}
"""

IMAGE_TEMPLATE = """
Design a clean, modern, text-free image illustrating *{{ topic }}*.
Style: minimal, bright brand palette; single focal concept; subtle depth.
"""

# ─── Helper functions ───────────────────────────────────────────────────────
def build_post_prompt(topic, audience, location, post_date, word_limit):
    return Template(POST_TEMPLATE).render(
        topic=topic,
        audience=audience,
        location=location,
        post_date=post_date,
        requirements=BASE_REQUIREMENTS.format(word_limit=word_limit),
    )

def build_image_prompt(topic):
    return Template(IMAGE_TEMPLATE).render(topic=topic)

def provider_from_choice(label):
    return "openai" if label.startswith("GPT‑4") else "groq"

# ─── Streamlit Config ───────────────────────────────────────────────────────
st.set_page_config(page_title="🚀 AI LinkedIn Post Generator", layout="wide")

if "history" not in st.session_state:
    st.session_state.history = []
    st.session_state.history_index = -1

# ─── Sidebar Controls ───────────────────────────────────────────────────────
with st.sidebar:
    st.header("Post style")
    word_limit = st.slider("Word limit", 50, 300, 120, step=10)
    model_choice = st.selectbox(
        "AI model",
        ["GPT-4-Turbo", "LLaMA-3-70B"],
    )
    model_provider = provider_from_choice(model_choice)

# ─── Main Interface ─────────────────────────────────────────────────────────
st.title("📢 AI LinkedIn Post Generator")
mode = st.radio("Choose Mode", ["Manual", "Automated", "Specific"], horizontal=True)

def generate_all(post_prompt, image_prompt):
    generator = PostGenerator(model_provider)
    with st.spinner("Generating post text …"):
        post_text = generator.generate_post_text(post_prompt)
    with st.spinner("Generating image …"):
        try:
            image_url = generator.generate_image(image_prompt)
        except Exception as e:
            if "billing_hard_limit_reached" in str(e):
                st.warning("🔒 OpenAI billing limit reached. Image generation is disabled.")
            else:
                st.warning(f"⚠ Error generating image. Reason: {str(e)}")
            image_url = None
    return post_text, image_url

# ───────────────────────── 1. Manual Mode ───────────────────────────────────
if mode == "Manual":
    with st.form("manual_form"):
        st.subheader("Post details")
        topic = st.text_input("🔖 Topic *", max_chars=100)
        audience = st.text_input("🎯 Target audience *")
        location = st.text_input("📍 Location", placeholder="Mumbai, India")
        post_date = st.date_input("📅 Planned publish date", value=datetime.now().date())
        submit_manual = st.form_submit_button("🚀 Generate Content")

    if submit_manual:
        if not topic or not audience:
            st.error("Topic and target audience are required.")
            st.stop()

        post_prompt = build_post_prompt(topic, audience, location or "N/A", post_date.strftime("%B %d %Y"), word_limit)
        image_prompt = build_image_prompt(topic)

        post_text, image_url = generate_all(post_prompt, image_prompt)
        if image_url:
            saver.save_post(post_text, image_url)

        st.session_state.history.append({
            "text": post_text,
            "image_url": image_url,
            "topic": topic,
            "audience": audience,
        })
        st.session_state.history_index = len(st.session_state.history) - 1

        st.success("✅ Post saved to your Downloads folder!")
        st.write(post_text)
        if image_url:
            st.image(image_url)

# ───────────────────────── 2. Automated Mode ────────────────────────────────
elif mode == "Automated":
    st.header("Automated Mode · curate a news article")

    if st.button("🔍 Fetch latest tech / business news"):
        with st.spinner("Fetching news …"):
            raw_news = news_agent.fetch_news()
            filtered_news = news_agent.filter_news_by_priority(raw_news)

        flat = [(f"[{cat}] {art['title'][:80]}…", art) for cat, arts in filtered_news.items() for art in arts]

        if flat:
            st.session_state.news_options = flat
            st.session_state.selected_news = 0
        else:
            st.warning("No relevant news found today.")

    if "news_options" in st.session_state:
        titles = [row[0] for row in st.session_state.news_options]
        sel_idx = st.selectbox("Select article", range(len(titles)), format_func=lambda i: titles[i])
        article = st.session_state.news_options[sel_idx][1]

        with st.expander("Preview article"):
            st.write("*Title:*", article["title"])
            st.write("*Summary:*", article.get("summary", "N/A"))
            st.write("*Source:*", article.get("source", "N/A"))

        with st.form("auto_form"):
            audience = st.text_input("🎯 Target audience *")
            location = st.text_input("📍 Location", placeholder="Remote / Global")
            submit_auto = st.form_submit_button("🚀 Generate Post")

        if submit_auto:
            if not audience:
                st.error("Target audience is required.")
                st.stop()

            topic = article["title"]
            summary = article.get("summary", "")
            post_prompt = build_post_prompt(topic, audience, location, datetime.now().strftime("%B %d %Y"), word_limit)
            post_prompt += f"\n\nOriginal article summary: {summary}"
            image_prompt = build_image_prompt(topic)

            post_text, image_url = generate_all(post_prompt, image_prompt)
            if image_url:
                saver.save_post(post_text, image_url)

            st.session_state.history.append({
                "text": post_text,
                "image_url": image_url,
                "topic": topic,
                "audience": audience,
            })
            st.session_state.history_index = len(st.session_state.history) - 1

            st.success("✅ Post saved to your Downloads folder!")
            st.write(post_text)
            if image_url:
                st.image(image_url)

elif mode == "TLDR Scraper":
    st.header("TLDR Mode · TLDR newsletter bulk‑posts")

    with st.form("tldr_form"):
        audience = st.text_input("🎯 Target audience *")
        location = st.text_input("📍 Location", placeholder="Global")
        submit_tldr = st.form_submit_button("🔄 Generate from TLDR")

    if submit_tldr:
        if not audience:
            st.error("Target audience is required.")
            st.stop()

        with st.spinner("Fetching TLDR…"):
            stories = tldr_agent.get_stories()

        if not stories:
            st.warning("No stories available.")
            st.stop()

        generator = PostGenerator(model_provider)
        post_list = []

        for i, story in enumerate(stories, 1):
            topic = story.get("title") or story.get("text", "")[:60]
            summary = story.get("summary", story.get("text", ""))

            post_prompt = build_post_prompt(topic, audience, location, datetime.now().strftime("%B %d %Y"), word_limit)
            post_prompt += f"\n\nStory summary: {summary}"
            image_prompt = build_image_prompt(topic)

            post_text = generator.generate_post_text(post_prompt)
            try:
                image_url = generator.generate_image(image_prompt)
            except Exception as e:
                st.warning(f"⚠ Error generating image for {topic}: {str(e)}")
                image_url = None

            post_list.append({
                "index": i,
                "topic": topic,
                "post_text": post_text,
                "image_url": image_url,
            })

            with st.expander(f"📄 Post #{i}: {topic}", expanded=False):
                st.markdown(post_text)
                if image_url:
                    st.image(image_url)


        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            for post in post_list:
                folder = f"TLDR_Posts/Post_{post['index']}"
                topic_clean = post["topic"].replace(" ", "_")[:40]

                # Add post text
                txt_path = f"{folder}/Post_{post['index']}_{topic_clean}.txt"
                zipf.writestr(txt_path, post["post_text"])

                # Add image if valid
                if post["image_url"]:
                    try:
                        resp = requests.get(post["image_url"], timeout=10)
                        if resp.status_code == 200:
                            img_path = f"{folder}/Post_{post['index']}_{topic_clean}.png"
                            zipf.writestr(img_path, resp.content)
                    except Exception as e:
                        st.warning(f"⚠ Image fetch failed for post {post['index']}: {e}")

        zip_buffer.seek(0)
        st.download_button(
            label="📦 Download All Posts + Images (ZIP)",
            data=zip_buffer,
            file_name="TLDR_Posts_Bundle.zip",
            mime="application/zip"
        )

        st.success("All TLDR posts saved!")



if st.session_state.history:
    st.markdown("### 📄 Session History")
    i = st.session_state.history_index
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅ Previous") and i > 0:
            st.session_state.history_index -= 1
    with col2:
        if st.button("Next ➡") and i < len(st.session_state.history) - 1:
            st.session_state.history_index += 1

    record = st.session_state.history[st.session_state.history_index]
    st.text_area("📄 Post Text", value=record["text"], height=250)
    if record["image_url"]:
        st.image(record["image_url"], width=500)
