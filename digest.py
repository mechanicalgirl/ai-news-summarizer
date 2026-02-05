import anthropic
from bs4 import BeautifulSoup
import feedparser
import requests

import argparse
from datetime import date, datetime, timedelta
import os
import sys

def get_urls(args):
    # Single URL mode
    if args.url:
        return [args.url]

    # File mode
    if args.file:
        with open(args.file, 'r') as f:
            return [line.strip() for line in f if line.strip()]

    # Default: get urls from regular news sources
    urls = get_urls_news_sources()
    return urls

def get_urls_hackernews(limit):
    return urls

def get_urls_slashdot(limit):
    return urls

def get_urls_slashdot():
    days_back = 1
    feed_url = 'https://rss.slashdot.org/Slashdot/slashdotMain'
    feed = feedparser.parse(feed_url)
    cutoff = datetime.now() - timedelta(days=days_back)
    original_urls = []
    for entry in feed.entries:
        pub_date = datetime(*entry.updated_parsed[:6])
        if pub_date > cutoff:
            original_urls.append(entry.link)
    urls = [url.split('?')[0] for url in original_urls]
    return urls

def get_urls_hackernews():
    limit = 5
    feed_url = 'https://news.ycombinator.com/'
    soup = BeautifulSoup(requests.get(feed_url).content, 'html.parser')
    links = soup.select('span.titleline > a')
    urls = [link['href'] for link in links]
    return urls[0:limit]

def get_urls_devto():
    limit = 5
    url = 'https://dev.to/top/day'
    soup = BeautifulSoup(requests.get(url).content, 'html.parser')
    elements= soup.find_all('a', class_='crayons-story__hidden-navigation-link')
    hrefs = [element['href'] for element in elements if 'href' in element.attrs]
    urls = [h for h in hrefs]
    return urls[0:limit]

def get_urls_rss(feed_url, days_back):
    """Get recent posts from RSS feed"""
    feed = feedparser.parse(feed_url)
    cutoff = datetime.now() - timedelta(days=days_back)
    urls = []
    for entry in feed.entries:
        pub_date = datetime(*entry.published_parsed[:6])
        if pub_date > cutoff:
            urls.append(entry.link)
    return urls

def get_urls_news_sources():
    """Collect URLs from HackerNews, SlashDot, etc."""
    urls = []
    urls.extend(get_urls_hackernews())
    # urls.extend(get_urls_slashdot())
    # urls.extend(get_urls_devto())
    # urls.extend(get_urls_rss('https://simonwillison.net/atom/everything/', 2))
    # urls.extend(get_urls_rss('https://techblog.wikimedia.org/feed/', 2))
    return urls

def scrape_article(url):
    """Scrape article text from URL"""
    article_text = ""
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    for script in soup(['script', 'style']):
        script.extract()
    text = soup.get_text()
    article_text = '\n'.join(line.strip() for line in text.splitlines() if line)

    if article_text:
        # print(article_text.encode('utf-8'))
        # print(article_text)
        pass
    else:
        print(f"FAILED ON {url}")
    return article_text

def summarize(text):
    """Summarize article using Claude"""
    client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"Summarize this article in 1-2 concise paragraphs:\n\n{text[:10000]}"
        }]
    )
    return message.content[0].text

def main():
    """Determine which URLs to process based on command line args"""
    parser = argparse.ArgumentParser(description='Scrape and summarize articles')
    parser.add_argument('--url', help='Single URL to process')
    parser.add_argument('--file', help='Text file with URLs (one per line)')
    args = parser.parse_args()

    urls = get_urls(args)
    summaries = []

    for url in urls:
        print(f"Processing {url}")
        try:
            article_text = scrape_article(url)
            if 'Enable JavaScript and cookies to continue' in article_text:
                pass
            else:
                summary = summarize(article_text)
                summaries.append({
                    'url': url,
                    'summary': summary
                })
        except Exception as e:
            print(f"Error processing {url}: {e}")

    if args.url or args.file:
        print(summaries)
    else:
        today = date.today().strftime("%Y-%m-%d")
        with open(f"summaries/{today}.md", 'w') as f:
            f.write(f"# Tech Digest - {today}\n\n")
            for item in summaries:
                f.write(f"## {item['url']}\n\n")
                f.write(f"{item['summary']}\n\n")
                f.write("---\n\n")

if __name__ == "__main__":
    main()
