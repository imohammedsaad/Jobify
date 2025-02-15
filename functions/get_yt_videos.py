def replace_youtube_videos_with_links(search_query):
    """
    A simplified version that returns a formatted YouTube search URL
    instead of making API calls.
    
    Args:
        search_query (str): The search term for YouTube videos
        
    Returns:
        str: A direct link to YouTube search results
    """
    # Create a search-friendly URL by replacing spaces with plus signs
    search_query = search_query.replace(' ', '+')
    youtube_search_url = f"https://www.youtube.com/results?search_query={search_query}"
    
    return {
        "message": "Click the link below to view relevant videos:",
        "search_url": youtube_search_url
    }
