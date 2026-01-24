"""
Vector database configuration for pgvector.

Provides configuration options for pgvector index types and distance metrics.
This enables flexibility in choosing the optimal index and similarity measure
for different use cases.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class VectorIndexType(str, Enum):
    """
    Supported pgvector index types.

    - HNSW: Hierarchical Navigable Small World graphs.
            Better query performance, higher memory usage.
            Recommended for production workloads.

    - IVFFLAT: Inverted File with Flat compression.
               Faster build time, lower memory usage.
               Better for smaller datasets or when memory is constrained.

    - NONE: No index (brute-force search).
            Only recommended for very small datasets.
    """

    HNSW = "hnsw"
    IVFFLAT = "ivfflat"
    NONE = "none"


class DistanceMetric(str, Enum):
    """
    Supported distance metrics for similarity search.

    - COSINE: Cosine distance (1 - cosine similarity).
              Best for normalized embeddings (most embedding models).
              Use <=> operator in pgvector.

    - L2: Euclidean distance (L2 norm).
          Suitable for non-normalized embeddings.
          Use <-> operator in pgvector.

    - INNER_PRODUCT: Negative inner product.
                     For embeddings trained with dot product similarity.
                     Use <#> operator in pgvector.
    """

    COSINE = "cosine"
    L2 = "l2"
    INNER_PRODUCT = "inner_product"


# Mapping of distance metrics to pgvector operators
DISTANCE_OPERATORS = {
    DistanceMetric.COSINE: "<=>",
    DistanceMetric.L2: "<->",
    DistanceMetric.INNER_PRODUCT: "<#>",
}

# Mapping of distance metrics to pgvector index ops classes
INDEX_OPS_CLASSES = {
    DistanceMetric.COSINE: {
        VectorIndexType.HNSW: "vector_cosine_ops",
        VectorIndexType.IVFFLAT: "vector_cosine_ops",
    },
    DistanceMetric.L2: {
        VectorIndexType.HNSW: "vector_l2_ops",
        VectorIndexType.IVFFLAT: "vector_l2_ops",
    },
    DistanceMetric.INNER_PRODUCT: {
        VectorIndexType.HNSW: "vector_ip_ops",
        VectorIndexType.IVFFLAT: "vector_ip_ops",
    },
}


class HNSWConfig(BaseModel):
    """
    HNSW index configuration parameters.

    These parameters control the trade-off between index build time,
    query speed, and recall quality.
    """

    # Maximum number of connections per node (higher = better recall, more memory)
    m: int = Field(default=16, ge=2, le=100)

    # Size of the dynamic candidate list during construction
    # Higher values improve recall during construction but slow down indexing
    ef_construction: int = Field(default=64, ge=4, le=1000)


class IVFFlatConfig(BaseModel):
    """
    IVFFlat index configuration parameters.

    The number of lists should typically be rows/1000 for datasets up to 1M rows
    and sqrt(rows) for larger datasets.
    """

    # Number of inverted lists (clusters)
    # More lists = faster search but lower recall
    lists: int = Field(default=100, ge=1, le=10000)


class VectorConfig(BaseModel):
    """
    Complete vector configuration combining index type, distance metric,
    and index-specific parameters.
    """

    index_type: VectorIndexType = Field(default=VectorIndexType.HNSW)
    distance_metric: DistanceMetric = Field(default=DistanceMetric.COSINE)
    embedding_dimensions: int = Field(default=1536)

    # Index-specific configurations
    hnsw: HNSWConfig = Field(default_factory=HNSWConfig)
    ivfflat: IVFFlatConfig = Field(default_factory=IVFFlatConfig)

    def get_distance_operator(self) -> str:
        """Get the pgvector operator for the configured distance metric."""
        return DISTANCE_OPERATORS[self.distance_metric]

    def get_ops_class(self) -> Optional[str]:
        """Get the index ops class for the current configuration."""
        if self.index_type == VectorIndexType.NONE:
            return None
        return INDEX_OPS_CLASSES[self.distance_metric][self.index_type]

    def get_index_parameters(self) -> dict:
        """Get the index-specific parameters for index creation."""
        if self.index_type == VectorIndexType.HNSW:
            return {
                "m": self.hnsw.m,
                "ef_construction": self.hnsw.ef_construction,
            }
        elif self.index_type == VectorIndexType.IVFFLAT:
            return {
                "lists": self.ivfflat.lists,
            }
        return {}


# Default configuration instance
default_vector_config = VectorConfig()
