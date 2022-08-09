try:
    import boto3
    import botocore
except ImportError as exc:
    raise RuntimeError(
        """AWS dependencies are not installed, please run
    pip install elastic-log-cli[aws]
"""
    ) from exc


__all__ = [
    "boto3",
    "botocore",
]
