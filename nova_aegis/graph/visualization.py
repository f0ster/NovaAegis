"""
Knowledge graph visualization component.
Creates interactive visualizations of research knowledge and connections.
"""
import plotly.graph_objects as go
from typing import List, Dict, Any
import networkx as nx
import structlog
from dataclasses import dataclass
from datetime import datetime

logger = structlog.get_logger()

@dataclass
class VisualNode:
    """Node in visualization graph."""
    id: str
    label: str
    type: str
    confidence: float
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class VisualEdge:
    """Edge in visualization graph."""
    source: str
    target: str
    type: str
    weight: float
    metadata: Dict[str, Any]

class GraphVisualizer:
    """Creates interactive visualizations of knowledge graphs."""
    
    def __init__(self):
        self.logger = logger.bind(component="graph_viz")
        
        # Color schemes
        self.node_colors = {
            "concept": "#1f77b4",  # Blue
            "insight": "#2ca02c",  # Green
            "pattern": "#ff7f0e",  # Orange
            "source": "#d62728"    # Red
        }
        
        self.edge_colors = {
            "relates": "#7f7f7f",      # Gray
            "supports": "#2ca02c",      # Green
            "contradicts": "#d62728",   # Red
            "extends": "#1f77b4"        # Blue
        }
    
    def create_graph_plot(
        self,
        insights: List[Dict[str, Any]]
    ) -> go.Figure:
        """Create interactive graph visualization."""
        try:
            # Extract nodes and edges
            nodes, edges = self._extract_graph_elements(insights)
            
            # Create networkx graph
            G = self._create_networkx_graph(nodes, edges)
            
            # Get layout
            pos = nx.spring_layout(G)
            
            # Create figure
            fig = go.Figure()
            
            # Add edges
            edge_traces = self._create_edge_traces(G, pos)
            for trace in edge_traces:
                fig.add_trace(trace)
            
            # Add nodes
            node_traces = self._create_node_traces(G, pos)
            for trace in node_traces:
                fig.add_trace(trace)
            
            # Update layout
            fig.update_layout(
                showlegend=True,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                annotations=[
                    dict(
                        text="Knowledge Graph",
                        showarrow=False,
                        xref="paper",
                        yref="paper",
                        x=0,
                        y=1.1
                    )
                ],
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            return fig
            
        except Exception as e:
            self.logger.error("visualization_failed", error=str(e))
            raise
    
    def _extract_graph_elements(
        self,
        insights: List[Dict[str, Any]]
    ) -> tuple[List[VisualNode], List[VisualEdge]]:
        """Extract nodes and edges from insights."""
        nodes = []
        edges = []
        
        # Track node IDs to avoid duplicates
        node_ids = set()
        
        for insight in insights:
            # Add insight node
            insight_id = f"insight_{insight['id']}"
            if insight_id not in node_ids:
                nodes.append(VisualNode(
                    id=insight_id,
                    label=insight['description'][:50] + "...",
                    type="insight",
                    confidence=insight.get('confidence', 0.5),
                    timestamp=datetime.now(),
                    metadata=insight
                ))
                node_ids.add(insight_id)
            
            # Add related concepts
            for concept in insight.get('concepts', []):
                concept_id = f"concept_{concept['id']}"
                if concept_id not in node_ids:
                    nodes.append(VisualNode(
                        id=concept_id,
                        label=concept['name'],
                        type="concept",
                        confidence=concept.get('confidence', 0.5),
                        timestamp=datetime.now(),
                        metadata=concept
                    ))
                    node_ids.add(concept_id)
                
                # Add edge
                edges.append(VisualEdge(
                    source=insight_id,
                    target=concept_id,
                    type="relates",
                    weight=concept.get('relevance', 0.5),
                    metadata={}
                ))
            
            # Add patterns
            for pattern in insight.get('patterns', []):
                pattern_id = f"pattern_{pattern['id']}"
                if pattern_id not in node_ids:
                    nodes.append(VisualNode(
                        id=pattern_id,
                        label=pattern['name'],
                        type="pattern",
                        confidence=pattern.get('confidence', 0.5),
                        timestamp=datetime.now(),
                        metadata=pattern
                    ))
                    node_ids.add(pattern_id)
                
                # Add edge
                edges.append(VisualEdge(
                    source=insight_id,
                    target=pattern_id,
                    type="supports",
                    weight=pattern.get('strength', 0.5),
                    metadata={}
                ))
        
        return nodes, edges
    
    def _create_networkx_graph(
        self,
        nodes: List[VisualNode],
        edges: List[VisualEdge]
    ) -> nx.Graph:
        """Create networkx graph from nodes and edges."""
        G = nx.Graph()
        
        # Add nodes
        for node in nodes:
            G.add_node(
                node.id,
                label=node.label,
                type=node.type,
                confidence=node.confidence,
                timestamp=node.timestamp,
                metadata=node.metadata
            )
        
        # Add edges
        for edge in edges:
            G.add_edge(
                edge.source,
                edge.target,
                type=edge.type,
                weight=edge.weight,
                metadata=edge.metadata
            )
        
        return G
    
    def _create_edge_traces(
        self,
        G: nx.Graph,
        pos: Dict[str, tuple]
    ) -> List[go.Scatter]:
        """Create edge traces for visualization."""
        traces = []
        
        # Group edges by type
        edges_by_type = {}
        for edge in G.edges(data=True):
            edge_type = edge[2].get('type', 'relates')
            if edge_type not in edges_by_type:
                edges_by_type[edge_type] = []
            edges_by_type[edge_type].append(edge)
        
        # Create trace for each edge type
        for edge_type, edges in edges_by_type.items():
            x = []
            y = []
            
            for edge in edges:
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                x.extend([x0, x1, None])
                y.extend([y0, y1, None])
            
            traces.append(go.Scatter(
                x=x,
                y=y,
                line=dict(
                    width=1,
                    color=self.edge_colors.get(edge_type, "#7f7f7f")
                ),
                hoverinfo='none',
                mode='lines',
                name=edge_type.title()
            ))
        
        return traces
    
    def _create_node_traces(
        self,
        G: nx.Graph,
        pos: Dict[str, tuple]
    ) -> List[go.Scatter]:
        """Create node traces for visualization."""
        traces = []
        
        # Group nodes by type
        nodes_by_type = {}
        for node in G.nodes(data=True):
            node_type = node[1].get('type', 'concept')
            if node_type not in nodes_by_type:
                nodes_by_type[node_type] = []
            nodes_by_type[node_type].append(node)
        
        # Create trace for each node type
        for node_type, nodes in nodes_by_type.items():
            x = []
            y = []
            text = []
            confidence = []
            
            for node in nodes:
                x.append(pos[node[0]][0])
                y.append(pos[node[0]][1])
                text.append(node[1]['label'])
                confidence.append(node[1]['confidence'])
            
            traces.append(go.Scatter(
                x=x,
                y=y,
                mode='markers',
                hoverinfo='text',
                text=text,
                name=node_type.title(),
                marker=dict(
                    color=self.node_colors.get(node_type, "#1f77b4"),
                    size=10 + 20 * confidence,
                    line=dict(width=2)
                )
            ))
        
        return traces