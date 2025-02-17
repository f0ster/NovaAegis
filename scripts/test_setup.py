"""
Test complete setup of NovaAegis's exploration environment.
Verifies Docker, database, and browser automation.
"""
import asyncio
import structlog
from sqlalchemy import text
from nova_aegis.nova_aegis import NovaAegis
from nova_aegis.database import get_db
from nova_aegis.browser_pilot import BrowserPilot
from nova_aegis.knowledge_store import KnowledgeStore

logger = structlog.get_logger()

async def test_database():
    """Test database connection and tables."""
    logger.info("Testing database connection...")
    
    async with get_db() as db:
        # Test connection
        result = await db.execute(text("SELECT 1"))
        assert result.scalar() == 1
        
        # Test schemas
        result = await db.execute(text("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name IN ('knowledge', 'research')
        """))
        schemas = [row[0] for row in result]
        assert 'knowledge' in schemas
        assert 'research' in schemas
        
        # Test tables
        result = await db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema IN ('knowledge', 'research')
        """))
        tables = [row[0] for row in result]
        assert 'papers' in tables
        assert 'concepts' in tables
        assert 'relationships' in tables
        assert 'patterns' in tables
        assert 'tasks' in tables
        assert 'visual_states' in tables
        
        logger.info("Database setup verified")

async def test_browser_automation():
    """Test browser pilot functionality."""
    logger.info("Testing browser automation...")
    
    knowledge_store = KnowledgeStore()
    browser = BrowserPilot(knowledge_store)
    
    try:
        # Test browser launch
        await browser.start()
        assert browser.is_ready
        
        # Test navigation
        await browser.navigate("https://huggingface.co/papers")
        assert "huggingface.co" in browser.current_url
        
        # Test screenshot capture
        screenshot = await browser.capture_screenshot()
        assert screenshot is not None
        assert len(screenshot) > 0
        
        # Test visual state tracking
        visual_state = browser.get_visual_state()
        assert visual_state is not None
        assert visual_state.screenshot is not None
        assert visual_state.html_snapshot is not None
        
        logger.info("Browser automation verified")
        
    finally:
        await browser.cleanup()

async def test_exploration_companion():
    """Test complete exploration workflow."""
    logger.info("Testing exploration companion...")
    
    nova_aegis = NovaAegis()
    await nova_aegis.start_session()
    
    try:
        # Test research request
        response = await nova_aegis.process_request(
            "Research recent HuggingFace papers about LLM architectures"
        )
        assert response is not None
        assert "message" in response
        
        # Wait for initial processing
        companion = nova_aegis.companion
        browser = companion.browser_pilot
        
        while browser.is_processing:
            status = browser.get_job_status()
            logger.info(
                "Research progress",
                papers=status.papers_processed,
                indexed=status.indexed_count
            )
            await asyncio.sleep(1)
            
            if status.papers_processed >= 3:
                break
        
        # Verify knowledge building
        knowledge = companion.knowledge
        papers = knowledge.get_papers()
        assert len(papers) >= 3
        
        # Verify graph construction
        graph = knowledge.get_knowledge_graph()
        assert len(graph.nodes) > 0
        assert len(graph.edges) > 0
        
        # Test understanding
        understanding = companion.get_understanding()
        assert understanding.confidence > 0.5
        assert len(understanding.key_concepts) > 0
        
        logger.info("Exploration companion verified")
        
    finally:
        await nova_aegis.end_session()

async def main():
    """Run complete setup verification."""
    try:
        logger.info("Starting setup verification...")
        
        # Test database
        await test_database()
        
        # Test browser automation
        await test_browser_automation()
        
        # Test exploration companion
        await test_exploration_companion()
        
        logger.info("Setup verification complete!")
        
    except Exception as e:
        logger.error("Setup verification failed", error=str(e))
        raise

if __name__ == "__main__":
    asyncio.run(main())