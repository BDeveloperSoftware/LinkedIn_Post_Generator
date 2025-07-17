import requests
import streamlit as st
from datetime import datetime, timedelta

class GNewsAgent:
    PRIORITY_CATEGORIES = {
        "medical": ["medical", "health", "medicine", "hospital", "doctor", "covid", "vaccine"],
        "defence": ["defence", "military", "army", "navy", "airforce", "weapon", "war", "security"],
        "ai_ml_dl": ["artificial intelligence", "AI", "machine learning", "deep learning", "neural network", "data science"],
        "technology": ["tech", "technology", "innovation", "startup", "software", "hardware"]
    }

    def __init__(self):
        self.api_key = st.secrets["api"]["GNEWS_API_KEY"]
        self.base_url = "https://gnews.io/api/v4/"

    def fetch_news(self, location=None, from_date=None, to_date=None, max_results=10):
        today = datetime.now()
        one_week_ago = today - timedelta(days=7)

        params = {
            "token": self.api_key,
            "lang": "en",
            "max": max_results,
            "from": one_week_ago.strftime("%Y-%m-%d"),
            "to": today.strftime("%Y-%m-%d"),
        }

        url = self.base_url + "search"

        if location:
            params["q"] = location
        else:
            # Target relevant categories only
            params["q"] = "technology OR medical OR defence OR AI OR machine learning"

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("articles", [])

    def categorize_article(self, article):
        title = article.get("title", "").lower()
        description = article.get("description", "").lower()
        content = title + " " + description

        for category, keywords in self.PRIORITY_CATEGORIES.items():
            if any(kw.lower() in content for kw in keywords):
                return category
        return None

    def filter_news_by_priority(self, articles):
        filtered = {category: [] for category in self.PRIORITY_CATEGORIES}
        for article in articles:
            category = self.categorize_article(article)
            if category:
                filtered[category].append(article)
        return filtered

