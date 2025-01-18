from utils import unwrap_tag, remove_tag, get_internal_links, remove_external_links

def find_element_with_most_direct_text(url, soup):
    soup = remove_external_links(url, soup)
    soup = unwrap_tag(soup, "p")
    soup = remove_tag(soup, "script")
    soup = remove_tag(soup, "style")
    max_text_length = 0
    max_text_element = None

    for element in soup.find_all(True):  # Find all tags
        direct_text = element.find_all(string=True, recursive=False)  # Get only direct text, not child elements' text
        combined_text = ''.join(direct_text).strip()
        if len(combined_text) > max_text_length:
            max_text_length = len(combined_text)
            max_text_element = element

    return [max_text_element.text , max_text_length]


def apply_extraction(url, soup):
    # NOTE: recommend to use the soup.body from calling the function as head often contain scripts that will mess this up

    # since there are only 2 things now, it will be an if else

    total_site_text_len = len(soup.text)

    max_text, max_text_len = find_element_with_most_direct_text(url, soup)

    result = []

    # if is content based
    if max_text_len >= total_site_text_len * 0.3:
        result = [max_text, max_text_len]
    else:
        all_internal_links, all_internal_links_len = get_internal_links(url, soup)
        result = [all_internal_links, all_internal_links_len]
    # [test-able-content, content-length]
    return result


def comparer(previous, now):
    if isinstance(previous, list):
        return set(previous) == set(now)

    elif isinstance(previous, str):
        return previous == now

    else:
        raise NotImplementedError(f"Comparer for {type(previous)} class is not implemented")
    

def quick_extract(content) -> callable:
    # get extraction function based on content type
    if isinstance(content, list):
        return get_internal_links

    elif isinstance(content, str):
        return find_element_with_most_direct_text

    else:
        raise NotImplementedError(f"quick_extract for {type(content)} class is not implemented")