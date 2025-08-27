"""
Configuration file for enhanced data models and migration
"""

# Enhanced properties that should be added during migration
ENHANCED_PROPERTIES = {
    'function_analysis', 'class_analysis', 'error_analysis', 'performance_info',
    'semantic_tags', 'quality_score', 'usage_frequency', 'embeddings',
    'confidence_score', 'semantic_similarity', 'functional_similarity'
}

# Default values for enhanced properties
DEFAULT_ENHANCED_VALUES = {
    'quality_score': 0.0,
    'usage_frequency': 0,
    'source_confidence': 1.0,
    'semantic_tags': [],
    'last_updated': None
}

# Migration priorities
MIGRATION_PRIORITIES = {
    'create_constraints': 1,
    'create_indexes': 2,
    'add_enhanced_properties': 3,
    'migrate_node_types': 4,
    'migrate_relation_types': 5
}

# Neo4j constraints to create
NEO4J_CONSTRAINTS = [
    "CREATE CONSTRAINT enhanced_node_id IF NOT EXISTS FOR (n:EnhancedNode) REQUIRE n.node_id IS UNIQUE",
    "CREATE CONSTRAINT function_name IF NOT EXISTS FOR (n:Function) REQUIRE n.name IS NOT NULL",
    "CREATE CONSTRAINT class_name IF NOT EXISTS FOR (n:Class) REQUIRE n.name IS NOT NULL"
]

# Neo4j indexes to create
NEO4J_INDEXES = [
    "CREATE INDEX enhanced_node_type IF NOT EXISTS FOR (n:EnhancedNode) ON (n.node_type)",
    "CREATE INDEX enhanced_node_name IF NOT EXISTS FOR (n:EnhancedNode) ON (n.name)",
    "CREATE INDEX enhanced_quality_score IF NOT EXISTS FOR (n:EnhancedNode) ON (n.quality_score)",
    "CREATE INDEX enhanced_usage_frequency IF NOT EXISTS FOR (n:EnhancedNode) ON (n.usage_frequency)",
    "CREATE INDEX relation_confidence IF NOT EXISTS FOR ()-[r:ENHANCED_RELATION]-() ON (r.confidence_score)",
    "CREATE INDEX semantic_similarity IF NOT EXISTS FOR ()-[r:ENHANCED_RELATION]-() ON (r.semantic_similarity)"
]
