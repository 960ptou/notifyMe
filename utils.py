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


from datetime import datetime
# import time
# def sleep_until_next_interval(interval_minutes: int):
#     """
#     Sleep until the next nearest interval in minutes (e.g., 15, 30, 45).
    
#     Args:
#         interval_minutes (int): The interval in minutes to wait for (e.g., 15, 30).
#     """
#     now = datetime.now()
#     intervals_later = now + timedelta(minutes=interval_minutes)
#     result_min = (intervals_later.minute // interval_minutes) * interval_minutes
    
#     next_time = intervals_later.replace(minute=result_min, second=0, microsecond=0)
    
#     sleep_duration = (next_time - now).total_seconds()
#     print(f"Sleeping for {sleep_duration} seconds until {next_time}")
#     time.sleep(sleep_duration)



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


def get_local_ip() -> str:
    # https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib?page=1&tab=scoredesc#tab-top
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    result = s.getsockname()[0]
    s.close()
    return result




import datetime as dt

def repeating_times(allowed_time_range : range, repeat_freq_hr : int = 0, repeat_freq_min : int = 0):
    repeat_freq_min += repeat_freq_hr * 60 
    assert repeat_freq_min > 0, "Frequency of 0 minutes, invalid"
    assert repeat_freq_min < 1440, "Frequency > 1 day, Invalid for now"

    start = allowed_time_range.start * 60
    for _ in range(1440 // repeat_freq_min):
        yield start // 60, start % 60 # yield (hour, minute)
        start += repeat_freq_min
        if start > 1440:
            start = start % 1440


def time_iterator(allowed_time_range : range, repeat_time : tuple[int, int]):

    # repeat_time : (hour , minute)

    all_times = repeating_times(allowed_time_range, *repeat_time)

    # filter out all times of the day out of the allowed time range    
    def _filter_fn(time):
        hr, minute = time
        # assume range object is time ordered -> 23,0,1,2,3 => ends at 3 start at 23
        if hr == allowed_time_range.stop: # ending hr
            return minute == 0

        if hr in allowed_time_range:
            return True
        
        return False

    # sorting to allow morning (0:00) -> end (23:xx)
    filtered_time = sorted(list(filter(_filter_fn, all_times)), key=lambda t : t[0]*60+t[1])


    current_date = datetime.now()
    # initial day starting from the middle
    for hour, minute in filtered_time:
        if ((hour - current_date.hour) * 60 + (minute - current_date.minute)) > 0:
            yield current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # repeating
    while True:
        current_date += dt.timedelta(days=1)
        for hour, minute in filtered_time:
            yield current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

        
        
def hour_range(start, end):
    from itertools import chain
    # 24 hour standard
    class chainRange:
        def __init__(self, chain_obj, start, end):
            self.chain_obj = chain_obj
            self.start = start
            self.stop = end

        def __iter__(self):
            return self.chain_obj

    if start > end:
        chain_obj = chain(range(start, 24), range(0, end))
        return chainRange(chain_obj, start, end)
    
    return range(start, end)
