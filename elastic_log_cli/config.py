from functools import cache
from typing import Literal, Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    elasticsearch_url: str = Field(
        description=(
            "URL of the Elasticsearch cluster containing logs. You can also provide an Elastic Cloud ID by "
            "prefixing with it `cloud:`."
        )
    )

    elasticsearch_username: Optional[str] = Field(
        description="Username for the Elasticsearch cluster containing logs."
    )

    elasticsearch_password: Optional[str] = Field(
        description="Password for the Elasticsearch cluster containing logs."
    )

    elasticsearch_auth_mode: Literal["basicauth", "apikey"] = Field(
        "basicauth",
        description=(
            "Whether to authenticate using Basic Auth or an API Key. If using `apikey`, provide as follows:\n"
            "\n"
            "```\n"
            "ELASTICSEARCH_USERNAME=${APIKEY_NAME}\n"
            "ELASTICSEARCH_PASSWORD=${APIKEY_KEY}\n"
            "```"
        ),
    )

    elasticsearch_timeout: int = Field(40, description="How long to wait on Elasticsearch requests.")


@cache
def get_settings():
    return Settings()
