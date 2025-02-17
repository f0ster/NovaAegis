"""Seed database with initial React patterns and components"""
import asyncio
from typing import List, Dict
import json
from datetime import datetime

from .database import AsyncDatabaseManager
from .domain.knowledge_models import CodePattern, Tag

INITIAL_PATTERNS: List[Dict] = [
    {
        "name": "Functional Component",
        "description": "Modern React functional component with hooks",
        "language": "javascript",
        "framework": "react",
        "template": """
import React, { useState, useEffect } from 'react';

interface {{name}}Props {
    // Add props here
}

const {{name}}: React.FC<{{name}}Props> = (props) => {
    // Add state hooks here
    const [state, setState] = useState();

    // Add effects here
    useEffect(() => {
        // Effect logic
    }, []);

    return (
        <div>
            {/* Component JSX */}
        </div>
    );
};

export default {{name}};
""",
        "metadata": {
            "complexity": "low",
            "type": "component",
            "usage_examples": ["pages", "features", "layouts"],
            "best_practices": [
                "Keep components focused and single-responsibility",
                "Use TypeScript for better type safety",
                "Implement proper prop validation"
            ]
        }
    },
    {
        "name": "Custom Hook",
        "description": "Reusable React hook pattern",
        "language": "javascript",
        "framework": "react",
        "template": """
import { useState, useEffect } from 'react';

interface {{name}}Options {
    // Add options here
}

export const {{name}} = (options: {{name}}Options) => {
    // Add state
    const [state, setState] = useState();

    // Add effect
    useEffect(() => {
        // Effect logic
    }, []);

    // Return values and functions
    return {
        state,
        // Add other returns
    };
};
""",
        "metadata": {
            "complexity": "medium",
            "type": "hook",
            "usage_examples": ["state management", "side effects", "data fetching"],
            "best_practices": [
                "Follow the Rules of Hooks",
                "Keep hooks composable",
                "Handle cleanup in useEffect"
            ]
        }
    },
    {
        "name": "Context Provider",
        "description": "React Context provider pattern",
        "language": "javascript",
        "framework": "react",
        "template": """
import React, { createContext, useContext, useState } from 'react';

interface {{name}}ContextType {
    // Add context values here
}

const {{name}}Context = createContext<{{name}}ContextType | undefined>(undefined);

export const {{name}}Provider: React.FC = ({ children }) => {
    // Add state and functions
    const [state, setState] = useState();

    const value = {
        state,
        // Add other values
    };

    return (
        <{{name}}Context.Provider value={value}>
            {children}
        </{{name}}Context.Provider>
    );
};

export const use{{name}} = () => {
    const context = useContext({{name}}Context);
    if (context === undefined) {
        throw new Error('use{{name}} must be used within a {{name}}Provider');
    }
    return context;
};
""",
        "metadata": {
            "complexity": "high",
            "type": "context",
            "usage_examples": ["theme", "auth", "localization"],
            "best_practices": [
                "Keep context value memoized",
                "Split contexts by domain",
                "Consider performance implications"
            ]
        }
    },
    {
        "name": "Data Fetching Component",
        "description": "React component with data fetching pattern",
        "language": "javascript",
        "framework": "react",
        "template": """
import React, { useState, useEffect } from 'react';

interface {{name}}Props {
    endpoint: string;
}

interface Data {
    // Define data type
}

const {{name}}: React.FC<{{name}}Props> = ({ endpoint }) => {
    const [data, setData] = useState<Data | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch(endpoint);
                if (!response.ok) throw new Error('Network response was not ok');
                const result = await response.json();
                setData(result);
                setError(null);
            } catch (err) {
                setError(err instanceof Error ? err : new Error('An error occurred'));
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [endpoint]);

    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error.message}</div>;
    if (!data) return null;

    return (
        <div>
            {/* Render data */}
        </div>
    );
};

export default {{name}};
""",
        "metadata": {
            "complexity": "medium",
            "type": "component",
            "usage_examples": ["API integration", "data display", "async operations"],
            "best_practices": [
                "Handle loading and error states",
                "Use proper TypeScript types",
                "Implement proper error boundaries"
            ]
        }
    }
]

INITIAL_TAGS = [
    "react",
    "component",
    "hook",
    "context",
    "typescript",
    "data-fetching",
    "state-management",
    "performance",
    "accessibility",
    "testing"
]

async def seed_database():
    """Seed database with initial patterns and tags"""
    db = AsyncDatabaseManager()
    async with db.get_async_db() as session:
        # Create tags
        tags = {}
        for tag_name in INITIAL_TAGS:
            tag = Tag(name=tag_name)
            session.add(tag)
            tags[tag_name] = tag
        
        # Create patterns
        for pattern in INITIAL_PATTERNS:
            code_pattern = CodePattern(
                name=pattern["name"],
                description=pattern["description"],
                language=pattern["language"],
                framework=pattern["framework"],
                template=pattern["template"],
                pattern_metadata=pattern.get("metadata"),
                created_at=datetime.now()
            )
            
            # Add relevant tags based on pattern type from metadata
            pattern_type = pattern.get("metadata", {}).get("type")
            if pattern_type == "component":
                code_pattern.tags = [tags["react"], tags["component"]]
            elif pattern_type == "hook":
                code_pattern.tags = [tags["react"], tags["hook"]]
            elif pattern_type == "context":
                code_pattern.tags = [tags["react"], tags["context"], tags["state-management"]]
                
            session.add(code_pattern)
        
        await session.commit()

if __name__ == "__main__":
    asyncio.run(seed_database())