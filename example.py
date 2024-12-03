from playwright.sync_api import sync_playwright
from YoutubeBackendCrawler import YoutubeBackendCrawler
from datetime import datetime, timedelta

channels = [
    'channel_1',
    'channel_2',
    'channel_3', #channel with paid members
]

print(f'Executing Date: {crawl_date}')

with sync_playwright() as playwright:
    # bq_client = bigquery.Client()
    for i, channel in enumerate(channels):
        print(channel)
        if i==0:
            crawler = YoutubeBackendCrawler(channel)
            crawler.setup_browser(playwright, headless=True)
            crawler.login()        
        else:
            crawler.switch_channel(channel)

        # Crawl Unique Viewers (monthly run)
        count = crawler.get_unique_viewers()

        # Crawl Channel Subscribers
        count = crawler.get_channel_subscribers()

        # Crawl Channel Members
        if channel=='channel_3':
            count = crawler.get_channel_members()

    crawler.logout()
