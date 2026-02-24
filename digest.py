import anthropic
from bs4 import BeautifulSoup
import cloudscraper
import feedparser
import requests

import argparse
from datetime import date, datetime, timedelta
import os
import sys


def get_urls_hackernews():
    limit = 10
    urls = []
    feed_url = 'https://news.ycombinator.com/'
    soup = BeautifulSoup(requests.get(feed_url).content, 'html.parser')
    links = soup.select('span.titleline > a')
    for link in links:
        title = str(link).split('>')[1].split('<')[0]
        urls.append((link['href'], "Hacker News", title))
    return urls[0:limit]

def get_urls_devto():
    limit = 5
    urls = []
    feed_url = 'https://dev.to/top/day'
    soup = BeautifulSoup(requests.get(feed_url).content, 'html.parser')
    links = soup.find_all('a', class_='crayons-story__hidden-navigation-link')
    for link in links:
        if 'href' in link.attrs:
            title = str(link).split('>')[1].split('<')[0]
            urls.append((link['href'], "Dev.To", title))
    return urls[0:limit]

def get_urls_pweekly():
    url = 'https://www.pythonweekly.com'
    archiveurls = []
    post_urls = []
    scraper = cloudscraper.create_scraper()
    html_content = scraper.get(url).text
    soup = BeautifulSoup(html_content, 'html.parser')
    links = soup.find_all('a')
    for l in links:
        if l.get('href').startswith('/p/python-weekly-issue-'):
            archiveurls.append(l.get('href'))
    latest_archive = url + sorted(list(set(archiveurls)), reverse=True)[0]
    new_content = scraper.get(latest_archive).text
    new_soup = BeautifulSoup(new_content, 'html.parser')
    new_links = new_soup.find_all('a', class_='link')

    ignore_list = ['youtube.com', 'meetup.com', 'github.com', 'ubscrib']
    full_list = [link for link in new_links]
    C = [x for x in full_list if any(b in str(x).lower() for b in ignore_list)]
    nn_links = set(full_list) - set(C)
    for link in nn_links:
        title = str(link).split('>')[1].split('<')[0]
        if title:
            post_urls.append((link.get('href').split('?')[0],'Python Weekly', title))
    urls = post_urls
    return urls

def get_urls_rss(feed_url, days_back):
    """Get recent posts from RSS feed"""
    d = feedparser.parse(feed_url)
    source = d.feed.title
    cutoff = datetime.now() - timedelta(days=days_back)
    urls = []
    for entry in d.entries:
        pub_date = datetime(*entry.published_parsed[:6])
        if pub_date > cutoff:
            urls.append((entry.link.split('?')[0], source, entry.title))
    return urls

def get_urls_news_sources():
    """Collect URLs from HackerNews, SlashDot, etc."""
    urls = []
    day = datetime.now().weekday()
    if day in(0, 2, 4):  # Monday, Wednesday, Friday
        urls.extend(get_urls_rss('https://stackoverflow.blog/feed', 2))
        urls.extend(get_urls_hackernews())
    elif day in(1, 3):  # Tuesday, Thursday
        urls.extend(get_urls_rss('https://feed.infoq.com/', 4))
        urls.extend(get_urls_rss('https://www.developer-tech.com/feed/', 4))
    elif day == 5:  # Saturday
        urls.extend(get_urls_devto())
        urls.extend(get_urls_pweekly())
        urls.extend(get_urls_rss('https://techcrunch.com/feed/', 7))
    else:
        urls.extend(get_urls_rss('https://lucumr.pocoo.org/feed.xml', 7))
        urls.extend(get_urls_rss('https://techblog.wikimedia.org/feed/', 7))
        urls.extend(get_urls_rss('https://simonwillison.net/atom/everything/', 7))
    return urls

def get_urls(args):
    # Single URL mode
    if args.url:
        return [(args.url, 'SOURCE')]

    # File mode
    if args.file:
        with open(args.file, 'r') as f:
            return [(line.strip(), "SOURCE") for line in f if line.strip()]

    urls = get_urls_news_sources()
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
        pass
    else:
        print(f"FAILED ON {url}")
    return article_text

def summarize(text):
    """Summarize article using Claude"""
    client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",  # approx. cost .05 - .10 per day
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
        print(f"Processing {url[0]}")
        try:
            article_text = scrape_article(url[0])
            if 'Enable JavaScript and cookies to continue' in article_text:
                pass
            else:
                if url[1] == 'Developer Tech News':
                    summary = 'links only'
                else:
                    summary = summarize(article_text)
                summaries.append({
                    'url': url[0],
                    'source': url[1],
                    'title': url[2],
                    'summary': summary
                })
        except Exception as e:
            print(f"Error processing {url}: {e}")
            import traceback
            traceback.print_exc()

    print(f"Successfully processed {len(summaries)} articles")

    if args.url or args.file:
        print(summaries)
    else:
        today = date.today().strftime("%Y-%m-%d")
        filepath = f"summaries/{today}.md"

        print(f"About to write to: {filepath}")
        print(f"Summaries count: {len(summaries)}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Directory exists: {os.path.exists('summaries/')}")

        # Create directory if it doesn't exist
        os.makedirs('summaries', exist_ok=True)

        with open(f"summaries/{today}.md", 'w') as f:
            header = f"# Tech Digest - {today}\n\n"
            print(f"Writing header: {header}")
            f.write(header)
            if summaries:
                for item in summaries:
                    f.write(f"### {item['title']} - ({item['source']})\n\n")
                    f.write(f"{item['url']}\n\n")
                    f.write(f"{item['summary']}\n\n")
                    f.write("---\n\n")
            else:
                f.write("---\n\n")
                f.write(f"No summaries for {today}\n\n")
        print(f"File written. Size: {os.path.getsize(filepath)} bytes")

if __name__ == "__main__":
    main()
