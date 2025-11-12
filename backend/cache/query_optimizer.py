"""
Query Optimizer for Project AEGIS
Optimizes database queries, provides query analysis, and performance improvements
"""

import time
import logging
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from functools import wraps
from contextlib import contextmanager

from sqlalchemy import text, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.sql import select, func
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

@dataclass
class QueryMetrics:
    """Query performance metrics"""
    query_hash: str
    query_text: str
    execution_count: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    rows_returned: int
    last_executed: datetime
    tables_accessed: List[str]
    indexes_used: List[str]

@dataclass
class QueryOptimization:
    """Query optimization suggestion"""
    query_hash: str
    optimization_type: str  # index, query_rewrite, join_optimization, etc.
    suggestion: str
    estimated_improvement: str
    priority: str  # low, medium, high
    implementation_sql: Optional[str]

class QueryAnalyzer:
    """Analyzes SQL queries for performance issues"""

    def __init__(self, engine: Engine):
        self.engine = engine
        self.query_metrics: Dict[str, QueryMetrics] = {}
        self.optimization_suggestions: Dict[str, List[QueryOptimization]] = {}

    def get_query_hash(self, query_text: str) -> str:
        """Generate consistent hash for normalized query"""
        # Normalize query by removing parameters and extra whitespace
        normalized = ' '.join(query_text.lower().split())
        normalized = normalized.replace('%s', '?')
        normalized = normalized.replace('%(.*?)s', '?')

        return hashlib.md5(normalized.encode()).hexdigest()

    @contextmanager
    def profile_query(self, query_text: str):
        """Context manager to profile query execution"""
        query_hash = self.get_query_hash(query_text)
        start_time = time.time()
        rows_returned = 0

        try:
            yield

        except Exception as e:
            logger.error(f"Query profiling error: {e}")
            raise

        finally:
            execution_time = time.time() - start_time

            # Update metrics
            if query_hash not in self.query_metrics:
                self.query_metrics[query_hash] = QueryMetrics(
                    query_hash=query_hash,
                    query_text=query_text,
                    execution_count=0,
                    total_time=0.0,
                    avg_time=0.0,
                    min_time=float('inf'),
                    max_time=0.0,
                    rows_returned=0,
                    last_executed=datetime.utcnow(),
                    tables_accessed=[],
                    indexes_used=[]
                )

            metrics = self.query_metrics[query_hash]
            metrics.execution_count += 1
            metrics.total_time += execution_time
            metrics.avg_time = metrics.total_time / metrics.execution_count
            metrics.min_time = min(metrics.min_time, execution_time)
            metrics.max_time = max(metrics.max_time, execution_time)
            metrics.last_executed = datetime.utcnow()
            metrics.rows_returned = rows_returned

            # Analyze for optimizations
            self._analyze_query(query_hash, query_text)

    def _analyze_query(self, query_hash: str, query_text: str):
        """Analyze query for optimization opportunities"""
        suggestions = []

        # Check for missing indexes
        index_suggestions = self._suggest_indexes(query_text)
        suggestions.extend(index_suggestions)

        # Check for query pattern issues
        pattern_suggestions = self._analyze_query_patterns(query_text)
        suggestions.extend(pattern_suggestions)

        # Check for join optimizations
        join_suggestions = self._analyze_joins(query_text)
        suggestions.extend(join_suggestions)

        # Check for pagination issues
        pagination_suggestions = self._analyze_pagination(query_text)
        suggestions.extend(pagination_suggestions)

        if suggestions:
            self.optimization_suggestions[query_hash] = suggestions

    def _suggest_indexes(self, query_text: str) -> List[QueryOptimization]:
        """Suggest indexes for query optimization"""
        suggestions = []

        # Look for WHERE clauses that could benefit from indexes
        query_lower = query_text.lower()

        # Simple pattern matching for common WHERE patterns
        if 'where' in query_lower:
            if 'join' in query_lower:
                # Foreign key columns should be indexed
                suggestions.append(QueryOptimization(
                    query_hash=self.get_query_hash(query_text),
                    optimization_type='index',
                    suggestion='Add index on foreign key columns used in joins',
                    estimated_improvement='50-80%',
                    priority='high',
                    implementation_sql='-- Add indexes on foreign key columns'
                ))

            if 'order by' in query_lower and 'limit' in query_lower:
                # ORDER BY with LIMIT can benefit from composite index
                suggestions.append(QueryOptimization(
                    query_hash=self.get_query_hash(query_text),
                    optimization_type='composite_index',
                    suggestion='Add composite index for ORDER BY + LIMIT queries',
                    estimated_improvement='30-60%',
                    priority='medium',
                    implementation_sql='-- Create composite index matching ORDER BY clause'
                ))

        return suggestions

    def _analyze_query_patterns(self, query_text: str) -> List[QueryOptimization]:
        """Analyze query patterns for issues"""
        suggestions = []
        query_lower = query_text.lower()

        # Check for SELECT *
        if 'select *' in query_lower:
            suggestions.append(QueryOptimization(
                query_hash=self.get_query_hash(query_text),
                optimization_type='query_rewrite',
                suggestion='Avoid SELECT *, specify only needed columns',
                estimated_improvement='10-30%',
                priority='medium',
                implementation_sql='-- Replace SELECT * with specific columns'
            ))

        # Check for subqueries that could be JOINs
        if 'select' in query_lower and query_lower.count('select') > 1:
            if 'in (select' in query_lower or 'exists (select' in query_lower:
                suggestions.append(QueryOptimization(
                    query_hash=self.get_query_hash(query_text),
                    optimization_type='query_rewrite',
                    suggestion='Consider rewriting subqueries as JOINs',
                    estimated_improvement='20-50%',
                    priority='high',
                    implementation_sql='-- Rewrite subqueries as JOINs'
                ))

        # Check for missing LIMIT clauses
        if 'select' in query_lower and 'limit' not in query_lower and 'insert' not in query_lower:
            suggestions.append(QueryOptimization(
                query_hash=self.get_query_hash(query_text),
                optimization_type='pagination',
                suggestion='Add LIMIT clause to prevent large result sets',
                estimated_improvement='Memory usage reduction',
                priority='medium',
                implementation_sql='-- Add LIMIT clause to query'
            ))

        return suggestions

    def _analyze_joins(self, query_text: str) -> List[QueryOptimization]:
        """Analyze JOIN clauses for optimization"""
        suggestions = []
        query_lower = query_text.lower()

        if 'join' in query_lower:
            # Check for missing join conditions
            if 'on' not in query_lower and 'using' not in query_lower:
                suggestions.append(QueryOptimization(
                    query_hash=self.get_query_hash(query_text),
                    optimization_type='join_optimization',
                    suggestion='Add explicit JOIN conditions',
                    estimated_improvement='Performance improvement',
                    priority='high',
                    implementation_sql='-- Add proper ON clause for JOINs'
                ))

            # Check for multiple JOINs without proper ordering
            join_count = query_lower.count('join')
            if join_count > 3:
                suggestions.append(QueryOptimization(
                    query_hash=self.get_query_hash(query_text),
                    optimization_type='join_optimization',
                    suggestion='Consider breaking complex multi-join queries',
                    estimated_improvement='Complexity reduction',
                    priority='medium',
                    implementation_sql='-- Break into smaller queries or use subqueries'
                ))

        return suggestions

    def _analyze_pagination(self, query_text: str) -> List[QueryOptimization]:
        """Analyze pagination for optimization"""
        suggestions = []
        query_lower = query_text.lower()

        if 'limit' in query_lower and 'offset' in query_lower:
            # Large OFFSET values are inefficient
            if 'offset' in query_lower:
                suggestions.append(QueryOptimization(
                    query_hash=self.get_query_hash(query_text),
                    optimization_type='pagination',
                    suggestion='Consider keyset pagination for large OFFSET values',
                    estimated_improvement='50-90% for large offsets',
                    priority='high',
                    implementation_sql='-- Use WHERE id > last_id ORDER BY id LIMIT N'
                ))

        return suggestions

    def get_slow_queries(self, threshold_ms: float = 1000.0) -> List[QueryMetrics]:
        """Get queries slower than threshold"""
        return [
            metrics for metrics in self.query_metrics.values()
            if metrics.avg_time * 1000 > threshold_ms
        ]

    def get_frequent_queries(self, min_executions: int = 10) -> List[QueryMetrics]:
        """Get frequently executed queries"""
        return [
            metrics for metrics in self.query_metrics.values()
            if metrics.execution_count >= min_executions
        ]

    def get_optimization_suggestions(self, query_hash: str = None) -> List[QueryOptimization]:
        """Get optimization suggestions for specific query or all queries"""
        if query_hash:
            return self.optimization_suggestions.get(query_hash, [])

        all_suggestions = []
        for suggestions in self.optimization_suggestions.values():
            all_suggestions.extend(suggestions)

        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        all_suggestions.sort(key=lambda x: priority_order.get(x.priority, 3))

        return all_suggestions

    def get_query_plan(self, query_text: str) -> Dict[str, Any]:
        """Get execution plan for query (PostgreSQL specific)"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query_text}")
                )
                plan = result.fetchone()[0]

                return {
                    'execution_plan': plan,
                    'query_text': query_text,
                    'analyzed_at': datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"Failed to get query plan: {e}")
            return {
                'error': str(e),
                'query_text': query_text,
                'analyzed_at': datetime.utcnow().isoformat()
            }

class QueryOptimizer:
    """Main query optimization manager"""

    def __init__(self, engine: Engine):
        self.engine = engine
        self.analyzer = QueryAnalyzer(engine)
        self._optimization_cache = {}
        self._cache_ttl = 300  # 5 minutes

    def analyze_and_optimize(self, query_text: str) -> Dict[str, Any]:
        """Analyze query and provide optimization suggestions"""
        query_hash = self.analyzer.get_query_hash(query_text)

        # Check cache
        cache_key = f"optimization_{query_hash}"
        if cache_key in self._optimization_cache:
            cached_result, timestamp = self._optimization_cache[cache_key]
            if (datetime.utcnow() - timestamp).total_seconds() < self._cache_ttl:
                return cached_result

        # Get query metrics
        metrics = self.analyzer.query_metrics.get(query_hash)

        # Get optimization suggestions
        suggestions = self.analyzer.get_optimization_suggestions(query_hash)

        # Get query plan
        query_plan = self.analyzer.get_query_plan(query_text)

        # Generate analysis
        analysis = {
            'query_hash': query_hash,
            'query_text': query_text,
            'metrics': metrics.__dict__ if metrics else None,
            'suggestions': [s.__dict__ for s in suggestions],
            'query_plan': query_plan,
            'performance_score': self._calculate_performance_score(metrics, suggestions),
            'analyzed_at': datetime.utcnow().isoformat()
        }

        # Cache result
        self._optimization_cache[cache_key] = (analysis, datetime.utcnow())

        return analysis

    def _calculate_performance_score(self, metrics: Optional[QueryMetrics],
                                   suggestions: List[QueryOptimization]) -> float:
        """Calculate performance score (0-100)"""
        if not metrics:
            return 50.0  # Neutral score for new queries

        score = 100.0

        # Penalize slow queries
        if metrics.avg_time > 1.0:  # > 1 second
            score -= 30
        elif metrics.avg_time > 0.5:  # > 500ms
            score -= 15
        elif metrics.avg_time > 0.1:  # > 100ms
            score -= 5

        # Penalize high frequency slow queries
        if metrics.execution_count > 100 and metrics.avg_time > 0.1:
            score -= 20

        # Penalize missing optimization suggestions
        high_priority_suggestions = [s for s in suggestions if s.priority == 'high']
        score -= len(high_priority_suggestions) * 10

        medium_priority_suggestions = [s for s in suggestions if s.priority == 'medium']
        score -= len(medium_priority_suggestions) * 5

        return max(0.0, min(100.0, score))

    def create_recommended_indexes(self) -> List[Dict[str, Any]]:
        """Generate SQL for recommended indexes based on query analysis"""
        index_suggestions = []

        # Analyze all slow queries for index opportunities
        slow_queries = self.analyzer.get_slow_queries()

        for query_metrics in slow_queries:
            query_hash = query_metrics.query_hash
            suggestions = self.analyzer.get_optimization_suggestions(query_hash)

            index_sugs = [s for s in suggestions if s.optimization_type in ['index', 'composite_index']]

            for suggestion in index_sugs:
                index_suggestions.append({
                    'query_hash': query_hash,
                    'query_text': query_metrics.query_text,
                    'avg_time_ms': query_metrics.avg_time * 1000,
                    'execution_count': query_metrics.execution_count,
                    'suggestion': suggestion.__dict__
                })

        return index_suggestions

    def get_database_statistics(self) -> Dict[str, Any]:
        """Get database performance statistics"""
        try:
            with self.engine.connect() as conn:
                # Get table sizes
                table_stats = conn.execute(text("""
                    SELECT
                        schemaname,
                        tablename,
                        n_tup_ins as inserts,
                        n_tup_upd as updates,
                        n_tup_del as deletes,
                        n_live_tup as live_tuples,
                        n_dead_tup as dead_tuples,
                        last_vacuum,
                        last_autovacuum,
                        last_analyze,
                        last_autoanalyze
                    FROM pg_stat_user_tables
                    ORDER BY n_live_tup DESC
                """)).fetchall()

                # Get index usage
                index_stats = conn.execute(text("""
                    SELECT
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan as index_scans,
                        idx_tup_read as tuples_read,
                        idx_tup_fetch as tuples_fetched
                    FROM pg_stat_user_indexes
                    ORDER BY idx_scan DESC
                """)).fetchall()

                # Get database size
                db_size = conn.execute(text("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as size
                """)).fetchone()

                return {
                    'database_size': db_size.size if db_size else 'Unknown',
                    'table_statistics': [dict(row._mapping) for row in table_stats],
                    'index_statistics': [dict(row._mapping) for row in index_stats],
                    'query_cache_size': len(self._optimization_cache),
                    'analyzed_queries': len(self.analyzer.query_metrics),
                    'generated_at': datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"Failed to get database statistics: {e}")
            return {
                'error': str(e),
                'generated_at': datetime.utcnow().isoformat()
            }

    def clear_cache(self):
        """Clear optimization cache"""
        self._optimization_cache.clear()
        logger.info("Query optimization cache cleared")

    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report"""
        slow_queries = self.analyzer.get_slow_queries()
        frequent_queries = self.analyzer.get_frequent_queries()
        all_suggestions = self.analyzer.get_optimization_suggestions()

        # Group suggestions by priority
        priority_groups = {}
        for suggestion in all_suggestions:
            priority = suggestion.priority
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(suggestion)

        return {
            'summary': {
                'total_queries_analyzed': len(self.analyzer.query_metrics),
                'slow_queries_count': len(slow_queries),
                'frequent_queries_count': len(frequent_queries),
                'optimization_suggestions_count': len(all_suggestions),
                'high_priority_suggestions': len(priority_groups.get('high', [])),
                'medium_priority_suggestions': len(priority_groups.get('medium', [])),
                'low_priority_suggestions': len(priority_groups.get('low', []))
            },
            'slow_queries': [q.__dict__ for q in slow_queries[:10]],  # Top 10
            'frequent_queries': [q.__dict__ for q in frequent_queries[:10]],  # Top 10
            'suggestions_by_priority': {
                priority: [s.__dict__ for s in suggestions[:10]]  # Top 10 per priority
                for priority, suggestions in priority_groups.items()
            },
            'database_statistics': self.get_database_statistics(),
            'generated_at': datetime.utcnow().isoformat()
        }

# Query monitoring decorator
def monitor_query(engine: Engine):
    """Decorator to monitor and analyze SQL queries"""
    optimizer = QueryOptimizer(engine)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # This is a simplified version - in practice, you'd need to
            # integrate with SQLAlchemy events or session instrumentation
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                return result

            finally:
                execution_time = time.time() - start_time
                if execution_time > 0.1:  # Log slow queries
                    logger.warning(f"Slow query detected: {func.__name__} took {execution_time:.3f}s")

        return wrapper
    return decorator

# Global query optimizer instance (will be initialized with engine)
query_optimizer: Optional[QueryOptimizer] = None

def initialize_query_optimizer(engine: Engine):
    """Initialize global query optimizer"""
    global query_optimizer
    query_optimizer = QueryOptimizer(engine)
    logger.info("Query optimizer initialized")

# Export components
__all__ = [
    'QueryOptimizer',
    'QueryAnalyzer',
    'QueryMetrics',
    'QueryOptimization',
    'query_optimizer',
    'initialize_query_optimizer',
    'monitor_query'
]