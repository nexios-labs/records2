"""
DEPRECATED: This file has been replaced by core.py with full async support.

The old sync Record and RecordCollection classes have been replaced with:
- AsyncRecord: Enhanced record with Pydantic integration
- AsyncRecordCollection: Async collection with streaming capabilities
- QueryBuilder: Advanced query building with type safety
- Database: Fully async database with connection pooling

Import from records2.core instead.
"""

# This file is kept for backward compatibility but should not be used
# All functionality has been moved to the new async architecture

import warnings

warnings.warn(
    "records2.record is deprecated. Use records2.core for the new async API.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from core for backward compatibility (will be removed in future versions)
try:
    from .core import AsyncRecord as Record, AsyncRecordCollection as RecordCollection
except ImportError:
    # Fallback if core is not available
    pass
