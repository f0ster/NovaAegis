"""Step definitions for knowledge refinement behavior tests."""
import pytest
from pytest_bdd import scenario, given, when, then, parsers
import asyncio
from datetime import datetime
from typing import List, Dict, Any
import structlog
from langchain.chat_models import ChatOpenAI

from nova_aegis.research_engine import ResearchEngine
from nova_aegis.tuning.confidence_crew import ConfidenceCrew
from nova_aegis.graph.schema import SchemaManager

logger = structlog.get_logger()

# Shared test context
class Context:
    def __init__(self):
        self.engine = None
        self.crew = None
        self.schema = None
        self.research_results = []
        self.metrics_history = []
        self.knowledge_graph = None

@pytest.fixture
def context():
    return Context()

# Scenarios
@scenario('../features/knowledge_refinement.feature', 'Learning from Research Results')
def test_learning():
    """Test learning from research results."""
    pass

@scenario('../features/knowledge_refinement.feature', 'Adapting to Feedback')
def test_feedback():
    """Test feedback adaptation."""
    pass

@scenario('../features/knowledge_refinement.feature', 'Building Domain Understanding')
def test_domain_understanding():
    """Test domain understanding building."""
    pass

# Background steps
@given("the research engine is initialized")
async def init_engine(context):
    """Initialize research engine."""
    context.engine = ResearchEngine()
    await context.engine.initialize()

@given("the confidence crew is ready")
def init_crew(context):
    """Initialize confidence crew."""
    llm = ChatOpenAI()  # Use actual LLM
    context.crew = ConfidenceCrew(llm)

@given("the knowledge graph is empty")
async def init_graph(context):
    """Initialize empty knowledge graph."""
    context.schema = SchemaManager(space_name="test_knowledge")
    await context.schema.init_schema()

# When steps
@when(parsers.parse('I research "{topic}"'))
async def research_topic(context, topic):
    """Perform research on a topic."""
    results = await context.engine.research_code(
        query=topic,
        min_relevance=0.5  # Start with lower threshold
    )
    context.research_results = results
    
    # Store real metrics
    context.metrics_history.append({
        "topic": topic,
        "results_count": len(results),
        "relevant_count": len([r for r in results if r.is_relevant]),
        "timestamp": datetime.now()
    })

@when("I analyze the research results")
async def analyze_results(context):
    """Analyze research results."""
    for result in context.research_results:
        # Real analysis
        analysis = await context.engine.analyze_code(result.code_segment)
        await context.engine.store_analysis(result.id, analysis)
        
        # Update graph with real relationships
        for pattern in analysis.patterns:
            await context.engine.store_relationship(
                result.id,
                pattern.id,
                "IMPLEMENTS",
                confidence=pattern.confidence
            )

@when(parsers.parse('I receive feedback that {feedback}'))
async def receive_feedback(context, feedback):
    """Process feedback about results."""
    # Adjust confidence based on real feedback
    await context.crew.tune_parameters(
        metrics=context.metrics_history,
        feedback=feedback
    )

@when("I research multiple related topics", target_fixture="topic_results")
async def research_topics(context, topics_table):
    """Research multiple related topics."""
    results = {}
    for topic, relevance in topics_table:
        topic_results = await context.engine.research_code(
            query=topic,
            min_relevance=0.7 if relevance == "high" else 0.5
        )
        results[topic] = topic_results
        
        # Allow real knowledge accumulation
        await asyncio.sleep(1)
    return results

# Then steps
@then(parsers.parse('I should find at least {count:d} code examples'))
def verify_result_count(context, count):
    """Verify minimum result count."""
    assert len(context.research_results) >= count

@then("store them in the knowledge graph")
async def verify_storage(context):
    """Verify results are stored."""
    for result in context.research_results:
        stored = await context.engine.get_stored_result(result.id)
        assert stored is not None
        assert stored.code_segment == result.code_segment

@then("calculate initial confidence scores")
async def verify_confidence_scores(context):
    """Verify confidence scores are calculated."""
    for result in context.research_results:
        assert result.confidence > 0
        assert result.confidence <= 1.0

@then("I should identify common patterns")
async def verify_pattern_identification(context):
    """Verify pattern identification."""
    patterns = await context.engine.find_common_patterns(
        context.research_results
    )
    assert len(patterns) > 0

@then("update relationship confidences")
async def verify_confidence_updates(context):
    """Verify relationship confidences are updated."""
    # Check real confidence changes
    old_confidences = [r.confidence for r in context.research_results]
    
    # Allow time for updates
    await asyncio.sleep(1)
    
    updated_results = await context.engine.get_results(
        [r.id for r in context.research_results]
    )
    new_confidences = [r.confidence for r in updated_results]
    
    assert new_confidences != old_confidences

@then("the average confidence should increase")
async def verify_confidence_increase(context):
    """Verify average confidence increases."""
    initial_avg = context.metrics_history[0]["confidence_avg"]
    current_avg = context.metrics_history[-1]["confidence_avg"]
    assert current_avg > initial_avg

@then("I should get fewer but more relevant results")
async def verify_result_quality(context):
    """Verify result quality improves."""
    old_metrics = context.metrics_history[-2]
    new_metrics = context.metrics_history[-1]
    
    assert new_metrics["results_count"] <= old_metrics["results_count"]
    assert new_metrics["relevant_count"] / new_metrics["results_count"] > \
           old_metrics["relevant_count"] / old_metrics["results_count"]

@then("I should identify domain relationships")
async def verify_domain_relationships(context, topic_results):
    """Verify domain relationships are identified."""
    relationships = await context.engine.find_domain_relationships(
        list(topic_results.keys())
    )
    assert len(relationships) > 0

@then("build a topic hierarchy")
async def verify_topic_hierarchy(context, topic_results):
    """Verify topic hierarchy is built."""
    hierarchy = await context.engine.build_topic_hierarchy(
        list(topic_results.keys())
    )
    assert len(hierarchy.nodes) > 0
    assert len(hierarchy.edges) > 0

@then("calculate topic relevance scores")
async def verify_topic_relevance(context, topic_results):
    """Verify topic relevance scores."""
    scores = await context.engine.calculate_topic_relevance(
        list(topic_results.keys())
    )
    assert all(0 <= score <= 1 for score in scores.values())