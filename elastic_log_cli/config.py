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

    elasticsearch_username: Optional[str] = Field(description="Username for the Elasticsearch cluster containing logs.")

    elasticsearch_password: Optional[str] = Field(description="Password for the Elasticsearch cluster containing logs.")

    elasticsearch_auth_mode: Literal["basicauth", "apikey", "awssigv4"] = Field(
        "basicauth",
        description=(
            """Specify which authentication mode you are using.

The default behaviour is `basicauth`, which encodes the username and password using HTTP Basic Auth.

You may also set this to `apikey`, in which case the API Keys should be provided as follows:

```
ELASTICSEARCH_USERNAME=${APIKEY_NAME}
ELASTICSEARCH_PASSWORD=${APIKEY_KEY}
```

Finally, if you are using [Amazon OpenSearch Service](https://aws.amazon.com/opensearch-service/) with [AWS Signature V4](https://docs.aws.amazon.com/general/latest/gr/signature-version-4.html) auth, then set this to `awssigv4`. AWS credentials will be read from the environment and used to sign your requests.
"""
        ),
    )

    elasticsearch_timeout: int = Field(40, description="How long to wait on Elasticsearch requests.")

    elasticsearch_index: str = Field("filebeat-*", description="The index to target. Globs are supported.")

    elasticsearch_timestamp_field: str = Field(
        "@timestamp", description="The field which denotes the timestamp in the indexed logs."
    )

    @property
    def is_cloud(self):
        return self.elasticsearch_url.startswith("cloud:")


@cache
def get_settings():
    return Settings()
