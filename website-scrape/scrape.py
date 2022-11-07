"""
This script contains the code for the WebSite class that scrapes the BBC news website for
the content of the Top 10 news articles.
"""
import requests
from bs4 import BeautifulSoup as bS
import re


class WebSite:
    """
    Use Beautiful Soup to scrape the most read BBC news articles
    """
    def __init__(self, url: str):
        """
        Get most read links and parse for content and title
        :param url: str of url
        """
        article = requests.get(url)
        self.headlines = bS(article.content, "html.parser")
        self.links = self.get_links()
        self.news = self.get_content()

    def get_links(self) -> list:
        """
        Scrape the most read links from the BBC news website
        :return: list of https url links
        """
        most_read = self.headlines.find_all('li', attrs={'data-entityid': re.compile('most-popular-read.*')})
        return ['https://bbc.com' + str(i.find('a')['href'].strip()) for i in most_read]

    def get_content(self) -> list:
        """
        Parses content from html body
        :return: JSON object containing title and body
        """
        content = []
        for i in self.links:
            article = requests.get(i)
            story = bS(article.content, "html.parser")
            body = self.get_body(story)
            title = self.get_title(story)
            content.append({i: {
                                'title': title,
                                'body': ''.join(body)}})
        return content

    @staticmethod
    def get_body(story) -> list:
        """
        Parse main article text
        :param story: HTML content of page
        :return: List of article text
        """
        body = story.find_all(class_=re.compile(".*RichTextContainer.*"))
        return [p.text for p in body if p.find_all("p")]

    @staticmethod
    def get_title(story) -> str:
        """
        Parse tile of text
        :param story: HTML content of page
        :return: str Title
        """
        return story.find(id=re.compile("main-heading")).text
