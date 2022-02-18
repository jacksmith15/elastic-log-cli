class ElasticLogError(Exception):
    """Base exception for this library."""


class ElasticLogValidationError(ElasticLogError):
    """An error with user-provided input."""
