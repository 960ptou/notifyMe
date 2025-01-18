def run_once(func):
    result = None
    has_run = False

    def wrapper(*args, **kwargs):
        nonlocal result, has_run
        if not has_run:
            result = func(*args, **kwargs)
            has_run = True
        return result

    return wrapper


from urllib.parse import urlparse, urljoin
def is_external_link(link, base_url):
    # check if link is different origin from base_url
    # Combine the base URL and the link if it's a relative URL
    full_link = urljoin(base_url, link)
    
    # Extract the base URL components (scheme, domain)
    base_parsed = urlparse(base_url)
    
    # Extract the target link components (scheme, domain)
    full_parsed = urlparse(full_link)
    
    # Check if the domain or scheme is different
    return base_parsed.netloc != full_parsed.netloc or base_parsed.scheme != full_parsed.scheme


from bs4 import BeautifulSoup

def unwrap_tag(soup : BeautifulSoup, tag : str) -> BeautifulSoup:
    for tag in soup.find_all(tag):
        tag.unwrap()
    return soup

def remove_tag(soup : BeautifulSoup, tag : str) -> BeautifulSoup:
    for tag in soup.find_all(tag):
        tag.decompose()
    return soup

def get_internal_links(base_url : str, soup : BeautifulSoup) -> list[list, int]:
    # return all links and number of links
    internal_links = []
    for attr in ["href", "src"]:
        links = soup.find_all(attrs={attr: True})
        for link in links:
            l = link.get(attr)
            if not(is_external_link(l, base_url)):
                internal_links.append(l)
    
    return [internal_links, len(internal_links)]


def remove_external_links(base_url : str, soup : BeautifulSoup) -> BeautifulSoup:
    # Remove all external links from an soup object then return that object
    for attr in ["href", "src"]:
        links = soup.find_all(attrs={attr: True})
        for link in links:
            l = link.get(attr)
            if is_external_link(l, base_url):
                link.decompose()

    return soup


from datetime import datetime, timedelta
import time
def sleep_until_next_interval(interval_minutes: int):
    """
    Sleep until the next nearest interval in minutes (e.g., 15, 30, 45).
    
    Args:
        interval_minutes (int): The interval in minutes to wait for (e.g., 15, 30).
    """
    now = datetime.now()
    intervals_later = now + timedelta(minutes=interval_minutes)
    result_min = (intervals_later.minute // interval_minutes) * interval_minutes
    
    next_time = intervals_later.replace(minute=result_min, second=0, microsecond=0)
    
    sleep_duration = (next_time - now).total_seconds()
    print(f"Sleeping for {sleep_duration} seconds until {next_time}")
    time.sleep(sleep_duration)



def time_difference_description(previous_time: datetime) -> str:
    """
    Compare a previous datetime with the current time and return a human-readable string.
    """
    now = datetime.now()
    delta = now - previous_time

    if delta.days > 30:
        return f"More than 30 days ago @ {previous_time.strftime('%B %d, %Y - (%I:%M %p)')}"
    
    if delta.days >= 1:
        return f"{delta.days} days ago"
    
    if delta.seconds >= 3600:
        hours = delta.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    
    if delta.seconds >= 60:
        minutes = delta.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    
    return "Just now"