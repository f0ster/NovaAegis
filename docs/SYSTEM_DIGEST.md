# NovaAegis System Digest

## Key Code References

### Intelligence Core
```python
# research_engine.py (329 lines)
class ResearchEngine:
    async def execute_step(self, step: str, context: Dict[str, Any]):
        # collect -> process -> analyze -> synthesize
        if step.startswith("collect"): return self._execute_collection()
        elif step.startswith("process"): return self._execute_processing()
        elif step.startswith("analyze"): return self._execute_analysis()
        elif step.startswith("synthesize"): return self._execute_synthesis()

# code_analyzer.py (314 lines)
class CodeAnalyzer:
    def analyze_code(self, code: str, language: str) -> CodeAnalysis:
        metrics = self._calculate_metrics(code, language)
        insights = self._generate_insights(code, language, metrics)
        structure = self._analyze_structure(code, language)
        return CodeAnalysis(metrics=metrics, insights=insights, structure=structure)

# companion.py (259 lines)
class ExplorationCompanion:
    async def perceive(self, stimulus: Any, context: Dict[str, Any]):
        perception = Perception(stimulus=stimulus, context=context)
        await self.perception_stream.put(perception)
```

### Knowledge Management
```python
# knowledge_store.py (274 lines)
class KnowledgeStore:
    async def add_pattern(self, name: str, code_template: str, description: str):
        pattern = CodePattern(name=name, template=code_template)
        self._pattern_cache[pattern.id] = pattern
        self.graph.add_node(pattern.id, type="pattern", data=pattern.to_dict())

# schema.py (271 lines)
class SchemaManager:
    async def init_schema(self):
        await self._create_tags([
            TagSchema(name="Code", properties={"language": "string", "embedding": "list<double>"}),
            TagSchema(name="Category", properties={"name": "string"})
        ])
        await self._create_edges([
            EdgeSchema(name="RELATES_TO", properties={"weight": "double"}),
            EdgeSchema(name="BELONGS_TO", properties={"confidence": "double"})
        ])
```

### Learning System
```python
# parameter_store.py (287 lines)
class ParameterStore:
    async def optimize_parameters(self, metrics: Dict[str, float]):
        adjustments = self._calculate_adjustments(metrics)
        for param, adjustment in adjustments.items():
            self.state.current_values[param] = max(
                self.parameters[param].min_value,
                min(self.parameters[param].max_value, current + adjustment)
            )

# llm_interface.py (208 lines)
class LLMInterface:
    def _initialize_llm(self) -> LLMProvider:
        if torch.cuda.is_available():
            vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
            return LocalQuantizedLLM(config) if vram >= 24 else CloudLLM(config)
```

### Query System
```python
# query_builder.py (195 lines)
def build_similarity_search(embedding: List[float], limit: int = 10) -> str:
    return (QueryBuilder()
        .match(MatchBuilder.vertex("Code", "c"))
        .with_(WithBuilder.alias(
            str(VectorBuilder.cosine_similarity("c.embedding", "query")),
            "similarity"
        ))
        .order_by(OrderBuilder.desc("similarity"))
        .limit(limit)
        .build())
```

## Processing Flow
1. Input -> Companion.perceive()
2. Perception -> Research Engine steps
3. Analysis -> Knowledge Store updates
4. Learning -> Parameter optimization
5. Response -> Action generation

## Key Checkpoints
- research_engine.py:execute_step(): Main execution flow
- companion.py:_process_perceptions(): Input processing
- knowledge_store.py:add_pattern(): Pattern storage
- parameter_store.py:optimize_parameters(): Learning updates
- schema.py:init_schema(): Knowledge structure