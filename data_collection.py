import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta

class TLDRNewsFetcher:
    def __init__(self):
        self.latest_weekday = self.get_latest_weekday()
        self.formatted_date = self.latest_weekday.strftime("%Y-%m-%d")
        self.readable_date = self.latest_weekday.strftime("%A, %B %d, %Y")
        self.tldr_url = f"https://tldr.tech/tech/{self.formatted_date}"
        self.stories = []

    def get_latest_weekday(self):
        day = date.today() - timedelta(days=1)
        while day.weekday() >= 5:
            day -= timedelta(days=1)
        return day

    def fetch_tldr_content(self, url):
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch TLDR content: {response.status_code}")
        return response.text
    
    def parse_articles(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        articles = soup.find_all('article')
        stories = []
        for article in articles:
            story_text = article.get_text(separator='\n').strip()
            story_links = [a['href'] for a in article.find_all('a', href=True)]
            if story_text:
                stories.append({
                    'text': story_text,
                    'links': story_links,
                    'date': self.readable_date,
                    'url': self.tldr_url
                })
        return stories

    def get_stories(self):
        """Returns the list of stories."""
        try:
            html = self.fetch_tldr_content(self.tldr_url)
            self.stories = self.parse_articles(html)
            return self.stories
        except Exception as e:
            print(f"[ERROR] {e}")
            return []
