from typing import List, Dict, Optional
import asyncio
from playwright.async_api import async_playwright, Browser, Page
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
from datetime import datetime

from models import ResearchResult, Tag
from database import DatabaseManager, AsyncDatabaseManager

logger = logging.getLogger(__name__)

class CodeResearcher:
    """Automated code research and documentation gathering"""
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.db_manager = AsyncDatabaseManager()
        
    async def __aenter__(self):
        """Setup browser context"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup browser context"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()

    async def search_github(self, query: str, language: Optional[str] = None) -> List[Dict]:
        """Search GitHub for code examples"""
        results = []
        page = await self.context.new_page()
        
        # Construct search URL with language filter if specified
        search_url = f"https://github.com/search?q={query}"
        if language:
            search_url += f"+language:{language}"
        search_url += "&type=code"
        
        await page.goto(search_url)
        await page.wait_for_selector(".code-list")
        
        # Extract code results
        code_elements = await page.query_selector_all(".code-list-item")
        for element in code_elements:
            try:
                code_url = await element.query_selector(".f4 a")
                code_url = await code_url.get_attribute("href")
                code_url = urljoin("https://github.com", code_url)
                
                code_preview = await element.query_selector(".blob-code-inner")
                code_text = await code_preview.inner_text()
                
                repo_info = await element.query_selector(".f4")
                repo_text = await repo_info.inner_text()
                
                results.append({
                    "url": code_url,
                    "code_preview": code_text,
                    "repository": repo_text,
                    "source": "github"
                })
            except Exception as e:
                logger.error(f"Error extracting GitHub result: {e}")
                
        await page.close()
        return results

    async def search_stack_overflow(self, query: str, tags: Optional[List[str]] = None) -> List[Dict]:
        """Search Stack Overflow for relevant questions and answers"""
        results = []
        page = await self.context.new_page()
        
        # Construct search URL
        search_url = f"https://stackoverflow.com/search?q={query}"
        if tags:
            search_url += f"+[{'] ['.join(tags)}]"
            
        await page.goto(search_url)
        await page.wait_for_selector(".question-summary")
        
        # Extract question results
        questions = await page.query_selector_all(".question-summary")
        for question in questions:
            try:
                title_element = await question.query_selector(".question-hyperlink")
                title = await title_element.inner_text()
                url = await title_element.get_attribute("href")
                url = urljoin("https://stackoverflow.com", url)
                
                votes = await question.query_selector(".vote-count-post")
                vote_count = await votes.inner_text()
                
                results.append({
                    "url": url,
                    "title": title,
                    "votes": int(vote_count),
                    "source": "stackoverflow"
                })
            except Exception as e:
                logger.error(f"Error extracting Stack Overflow result: {e}")
                
        await page.close()
        return results

    async def extract_code_blocks(self, page: Page) -> List[str]:
        """Extract code blocks from a page"""
        # Get page content
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find all code blocks
        code_blocks = []
        
        # Check for pre/code elements
        for code in soup.find_all('code'):
            if code.parent.name == 'pre':
                code_blocks.append(code.get_text())
                
        # Check for GitHub-style code blocks
        for block in soup.find_all('div', class_='highlight'):
            code_blocks.append(block.get_text())
            
        return code_blocks

    async def analyze_documentation(self, url: str) -> Dict:
        """Analyze documentation page for relevant information"""
        page = await self.context.new_page()
        await page.goto(url)
        
        # Extract main content
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Remove navigation, headers, footers
        for elem in soup.find_all(['nav', 'header', 'footer']):
            elem.decompose()
            
        # Extract text content
        main_content = soup.get_text()
        
        # Extract code examples
        code_blocks = await self.extract_code_blocks(page)
        
        # Extract API endpoints if present
        api_endpoints = []
        for pre in soup.find_all('pre'):
            if any(method in pre.text.lower() for method in ['get', 'post', 'put', 'delete']):
                api_endpoints.append(pre.text)
                
        await page.close()
        
        return {
            "url": url,
            "content": main_content,
            "code_examples": code_blocks,
            "api_endpoints": api_endpoints
        }

    async def save_research_result(self, project_id: int, result: Dict):
        """Save research result to database"""
        async with self.db_manager.get_async_db() as db:
            # Create tags
            tags = []
            if "tags" in result:
                for tag_name in result["tags"]:
                    tag = await db.execute(
                        "SELECT * FROM tags WHERE name = :name",
                        {"name": tag_name}
                    )
                    tag = tag.first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.add(tag)
                    tags.append(tag)
            
            # Create research result
            research_result = ResearchResult(
                project_id=project_id,
                url=result["url"],
                title=result.get("title"),
                content_summary=result.get("content"),
                code_blocks=result.get("code_examples", []),
                relevance_score=result.get("relevance", 0),
                tags=tags
            )
            
            db.add(research_result)
            await db.commit()
            
            return research_result

    async def research_topic(self, query: str, project_id: int, 
                           sources: List[str] = None) -> List[Dict]:
        """Comprehensive research on a topic"""
        if sources is None:
            sources = ["github", "stackoverflow", "documentation"]
            
        results = []
        
        # Parallel execution of searches
        tasks = []
        if "github" in sources:
            tasks.append(self.search_github(query))
        if "stackoverflow" in sources:
            tasks.append(self.search_stack_overflow(query))
            
        search_results = await asyncio.gather(*tasks)
        
        # Flatten results
        for source_results in search_results:
            results.extend(source_results)
            
        # Save results to database
        for result in results:
            await self.save_research_result(project_id, result)
            
        return results

    @staticmethod
    def extract_code_pattern(code: str) -> Optional[Dict]:
        """Extract reusable code pattern from example"""
        # Remove comments and empty lines
        code_lines = [line for line in code.split('\n') 
                     if line.strip() and not line.strip().startswith('//')]
        
        if not code_lines:
            return None
            
        # Analyze code structure
        pattern = {
            "imports": [],
            "functions": [],
            "classes": [],
            "usage_example": ""
        }
        
        current_section = None
        
        for line in code_lines:
            if line.startswith('import ') or line.startswith('from '):
                pattern["imports"].append(line)
            elif 'class ' in line:
                pattern["classes"].append(line)
                current_section = "class"
            elif 'def ' in line or 'function ' in line:
                pattern["functions"].append(line)
                current_section = "function"
            elif current_section:
                if current_section == "class":
                    pattern["classes"][-1] += '\n' + line
                elif current_section == "function":
                    pattern["functions"][-1] += '\n' + line
                    
        return pattern if any(pattern.values()) else None