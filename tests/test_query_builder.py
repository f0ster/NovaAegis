"""Tests for Nebula Graph query builder components."""
import pytest
from nova_aegis.graph.query_builder import (
    QueryBuilder,
    MatchBuilder,
    WhereBuilder,
    WithBuilder,
    VectorBuilder,
    ReturnBuilder,
    OrderBuilder,
    LimitBuilder,
    QueryPart
)

def test_query_part():
    """Test basic query part creation."""
    part = QueryPart("test content", {"param": "value"})
    assert str(part) == "test content"
    assert part.params == {"param": "value"}

class TestMatchBuilder:
    def test_vertex(self):
        """Test vertex pattern building."""
        result = MatchBuilder.vertex("Code", "c")
        assert str(result) == "(c:Code)"
    
    def test_edge(self):
        """Test edge pattern building."""
        result = MatchBuilder.edge("RELATES_TO", 2)
        assert str(result) == "-[e:RELATES_TO*1..2]->"
    
    def test_path(self):
        """Test path pattern building."""
        result = MatchBuilder.path("c1", "-[e:RELATES_TO]->", "c2")
        assert str(result) == "(c1)-[e:RELATES_TO]->(c2)"

class TestWhereBuilder:
    def test_equals(self):
        """Test equals condition."""
        result = WhereBuilder.equals("c.language", "python")
        assert str(result) == "c.language == 'python'"
    
    def test_in_list(self):
        """Test in list condition."""
        result = WhereBuilder.in_list("tag", ["python", "async"])
        assert str(result) == "tag IN ['python', 'async']"
    
    def test_greater_than(self):
        """Test greater than condition."""
        result = WhereBuilder.greater_than("score", 0.5)
        assert str(result) == "score > 0.5"
    
    def test_combine_and(self):
        """Test AND combination of conditions."""
        conditions = [
            WhereBuilder.equals("language", "python"),
            WhereBuilder.greater_than("score", 0.5)
        ]
        result = WhereBuilder.combine_and(conditions)
        assert str(result) == "(language == 'python' AND score > 0.5)"
    
    def test_combine_empty(self):
        """Test combining empty conditions."""
        result = WhereBuilder.combine_and([])
        assert str(result) == ""

class TestVectorBuilder:
    def test_dot_product(self):
        """Test dot product calculation."""
        result = VectorBuilder.dot_product("vec1", "vec2")
        assert "reduce" in str(result)
        assert "vec1[i] * vec2[i]" in str(result)
    
    def test_vector_magnitude(self):
        """Test vector magnitude calculation."""
        result = VectorBuilder.vector_magnitude("vec")
        assert "sqrt" in str(result)
        assert "reduce" in str(result)
    
    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        result = VectorBuilder.cosine_similarity("vec1", "vec2")
        assert "sqrt" in str(result)
        assert "reduce" in str(result)

class TestQueryBuilder:
    def test_simple_query(self):
        """Test building simple query."""
        query = (QueryBuilder()
            .match(MatchBuilder.vertex("Code", "c"))
            .return_(ReturnBuilder.fields("c"))
            .build())
        assert query == "MATCH (c:Code) RETURN c"
    
    def test_complex_query(self):
        """Test building complex query with multiple parts."""
        query = (QueryBuilder()
            .match(MatchBuilder.vertex("Code", "c"))
            .where(WhereBuilder.equals("c.language", "python"))
            .with_(WithBuilder.alias("c", "code"))
            .return_(ReturnBuilder.fields("code"))
            .order_by(OrderBuilder.desc("code.score"))
            .limit(10)
            .build())
        
        expected = (
            "MATCH (c:Code) "
            "WHERE c.language == 'python' "
            "WITH c AS code "
            "RETURN code "
            "ORDER BY code.score DESC "
            "LIMIT 10"
        )
        assert query == expected

def test_similarity_search():
    """Test building similarity search query."""
    embedding = [0.1, 0.2, 0.3]
    query = build_similarity_search(embedding, limit=5)
    
    assert "MATCH (c:Code)" in query
    assert "WITH c, c.embedding AS emb" in query
    assert "similarity" in query
    assert "ORDER BY similarity DESC" in query
    assert "LIMIT 5" in query

def test_related_search():
    """Test building related code search query."""
    query = build_related_search(
        vid="code123",
        relation_type="SIMILAR_TO",
        depth=2
    )
    
    assert "MATCH" in query
    assert "RELATES_TO*1..2" in query
    assert "c1.vid == 'code123'" in query
    assert "e.relation_type == 'SIMILAR_TO'" in query
    assert "ORDER BY relevance DESC" in query

def test_query_composition():
    """Test composing multiple query parts."""
    # Build vertex match
    vertex = MatchBuilder.vertex("Code", "c")
    
    # Build conditions
    conditions = [
        WhereBuilder.equals("c.language", "python"),
        WhereBuilder.greater_than("c.score", 0.8)
    ]
    where = WhereBuilder.combine_and(conditions)
    
    # Build return with ordering
    returns = ReturnBuilder.fields("c.id", "c.score")
    order = OrderBuilder.desc("c.score")
    
    # Compose full query
    query = (QueryBuilder()
        .match(vertex)
        .where(where)
        .return_(returns)
        .order_by(order)
        .limit(5)
        .build()
    )
    
    expected = (
        "MATCH (c:Code) "
        "WHERE (c.language == 'python' AND c.score > 0.8) "
        "RETURN c.id, c.score "
        "ORDER BY c.score DESC "
        "LIMIT 5"
    )
    assert query == expected

def test_empty_where():
    """Test query building with empty where clause."""
    query = (QueryBuilder()
        .match(MatchBuilder.vertex("Code", "c"))
        .where(WhereBuilder.combine_and([]))
        .return_(ReturnBuilder.fields("c"))
        .build()
    )
    
    assert query == "MATCH (c:Code) RETURN c"