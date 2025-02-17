"""Example of async data fetching pattern."""
import aiohttp
import asyncio
from typing import List, Dict, Any

async def fetch_data(url: str) -> Dict[str, Any]:
    """Fetch data from URL with error handling."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise ValueError(f"API error: {response.status}")
            return await response.json()

async def process_urls(urls: List[str]) -> List[Dict[str, Any]]:
    """Process multiple URLs concurrently."""
    tasks = [fetch_data(url) for url in urls]
    return await asyncio.gather(*tasks)

# Example usage
if __name__ == "__main__":
    urls = [
        "https://api.example.com/data/1",
        "https://api.example.com/data/2"
    ]
    results = asyncio.run(process_urls(urls))
    print(results)