"""
Composable query builders for Nebula Graph operations.
Each component handles a specific part of query construction.
"""
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from datetime import datetime

@dataclass
class QueryPart:
    """A part of a Nebula Graph query."""
    content: str
    params: Dict[str, Any] = None

    def __str__(self) -> str:
        return self.content

class MatchBuilder:
    """Builds MATCH clause components."""
    
    @staticmethod
    def vertex(tag: str, alias: str) -> QueryPart:
        return QueryPart(f"({alias}:{tag})")
    
    @staticmethod
    def edge(edge_type: str, depth: int = 1) -> QueryPart:
        return QueryPart(f"-[e:{edge_type}*1..{depth}]->")
    
    @staticmethod
    def path(start_alias: str, edge: str, end_alias: str) -> QueryPart:
        return QueryPart(f"({start_alias}){edge}({end_alias})")

class WhereBuilder:
    """Builds WHERE clause components."""
    
    @staticmethod
    def equals(field: str, value: Any) -> QueryPart:
        return QueryPart(f"{field} == '{value}'")
    
    @staticmethod
    def in_list(field: str, values: List[Any]) -> QueryPart:
        return QueryPart(f"{field} IN {values}")
    
    @staticmethod
    def greater_than(field: str, value: float) -> QueryPart:
        return QueryPart(f"{field} > {value}")
    
    @staticmethod
    def combine_and(conditions: List[QueryPart]) -> QueryPart:
        parts = [str(c) for c in conditions if c.content.strip()]
        if not parts:
            return QueryPart("")
        return QueryPart(f"({' AND '.join(parts)})")

class WithBuilder:
    """Builds WITH clause components."""
    
    @staticmethod
    def alias(expr: str, alias: str) -> QueryPart:
        return QueryPart(f"{expr} AS {alias}")
    
    @staticmethod
    def combine(parts: List[QueryPart]) -> QueryPart:
        return QueryPart(", ".join(str(p) for p in parts))

class VectorBuilder:
    """Builds vector operation components."""
    
    @staticmethod
    def dot_product(vec1: str, vec2: str) -> QueryPart:
        return QueryPart(
            f"reduce(dot = 0.0, i IN range(0, size({vec1})-1) | "
            f"dot + {vec1}[i] * {vec2}[i])"
        )
    
    @staticmethod
    def vector_magnitude(vec: str) -> QueryPart:
        return QueryPart(
            f"sqrt(reduce(norm = 0.0, i IN range(0, size({vec})-1) | "
            f"norm + {vec}[i] * {vec}[i]))"
        )
    
    @staticmethod
    def cosine_similarity(vec1: str, vec2: str) -> QueryPart:
        dot = VectorBuilder.dot_product(vec1, vec2)
        mag1 = VectorBuilder.vector_magnitude(vec1)
        mag2 = VectorBuilder.vector_magnitude(vec2)
        return QueryPart(f"({dot}) / ({mag1} * {mag2})")

class ReturnBuilder:
    """Builds RETURN clause components."""
    
    @staticmethod
    def fields(*fields: str) -> QueryPart:
        return QueryPart(", ".join(fields))
    
    @staticmethod
    def distinct(*fields: str) -> QueryPart:
        return QueryPart(f"DISTINCT {', '.join(fields)}")

class OrderBuilder:
    """Builds ORDER BY clause components."""
    
    @staticmethod
    def asc(field: str) -> QueryPart:
        return QueryPart(f"{field} ASC")
    
    @staticmethod
    def desc(field: str) -> QueryPart:
        return QueryPart(f"{field} DESC")

class LimitBuilder:
    """Builds LIMIT clause."""
    
    @staticmethod
    def limit(n: int) -> QueryPart:
        return QueryPart(f"LIMIT {n}")

class QueryBuilder:
    """Combines query parts into complete queries."""
    
    def __init__(self):
        self.parts: List[QueryPart] = []
    
    def match(self, part: QueryPart) -> 'QueryBuilder':
        self.parts.append(QueryPart(f"MATCH {part}"))
        return self
    
    def where(self, part: QueryPart) -> 'QueryBuilder':
        if part.content.strip():
            self.parts.append(QueryPart(f"WHERE {part}"))
        return self
    
    def with_(self, part: QueryPart) -> 'QueryBuilder':
        self.parts.append(QueryPart(f"WITH {part}"))
        return self
    
    def return_(self, part: QueryPart) -> 'QueryBuilder':
        self.parts.append(QueryPart(f"RETURN {part}"))
        return self
    
    def order_by(self, part: QueryPart) -> 'QueryBuilder':
        self.parts.append(QueryPart(f"ORDER BY {part}"))
        return self
    
    def limit(self, n: int) -> 'QueryBuilder':
        self.parts.append(LimitBuilder.limit(n))
        return self
    
    def build(self) -> str:
        return " ".join(str(part) for part in self.parts)

# Example usage:
def build_similarity_search(embedding: List[float], limit: int = 10) -> str:
    return (QueryBuilder()
        .match(MatchBuilder.vertex("Code", "c"))
        .with_(WithBuilder.combine([
            WithBuilder.alias("c", "c"),
            WithBuilder.alias("c.embedding", "emb")
        ]))
        .with_(WithBuilder.combine([
            WithBuilder.alias("c", "c"),
            WithBuilder.alias("emb", "emb"),
            WithBuilder.alias(str(embedding), "query")
        ]))
        .with_(WithBuilder.combine([
            WithBuilder.alias("c", "c"),
            WithBuilder.alias(
                str(VectorBuilder.cosine_similarity("emb", "query")),
                "similarity"
            )
        ]))
        .order_by(OrderBuilder.desc("similarity"))
        .limit(limit)
        .return_(ReturnBuilder.fields("c", "similarity"))
        .build())

def build_related_search(
    vid: str,
    relation_type: Optional[str],
    depth: int
) -> str:
    where_conditions = [WhereBuilder.equals("c1.vid", vid)]
    if relation_type:
        where_conditions.append(WhereBuilder.equals("e.relation_type", relation_type))
    
    return (QueryBuilder()
        .match(MatchBuilder.path(
            "c1",
            str(MatchBuilder.edge("RELATES_TO", depth)),
            "c2"
        ))
        .where(WhereBuilder.combine_and(where_conditions))
        .return_(ReturnBuilder.distinct("c2", "e.weight AS relevance"))
        .order_by(OrderBuilder.desc("relevance"))
        .build())