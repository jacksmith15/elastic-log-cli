# Elastic Log CLI

CLI for streaming logs from Elasticsearch to a terminal.

## Installation

Install with `pip`:

```bash
pip install elastic-log-cli
```

> :memo: Requires Python 3.10


## Configuration

The following environment variables are used to configure the tool. For secure, easy selection of target clusters, a tool like [envchain](https://github.com/sorah/envchain) is recommended.

Where available, CLI options will override environment variables.

<!-- generated env. vars. start -->
### `ELASTICSEARCH_URL`

**Required**

URL of the Elasticsearch cluster containing logs. You can also provide an Elastic Cloud ID by prefixing with it `cloud:`.

### `ELASTICSEARCH_USERNAME`

*Optional*

Username for the Elasticsearch cluster containing logs.

### `ELASTICSEARCH_PASSWORD`

*Optional*

Password for the Elasticsearch cluster containing logs.

### `ELASTICSEARCH_AUTH_MODE`

*Optional*, default value: `basicauth`

Specify which authentication mode you are using.

The default behaviour is `basicauth`, which encodes the username and password using HTTP Basic Auth.

You may also set this to `apikey`, in which case the API Keys should be provided as follows:

```
ELASTICSEARCH_USERNAME=${APIKEY_NAME}
ELASTICSEARCH_PASSWORD=${APIKEY_KEY}
```

Finally, if you are using [Amazon OpenSearch Service](https://aws.amazon.com/opensearch-service/) with [AWS Signature V4](https://docs.aws.amazon.com/general/latest/gr/signature-version-4.html) auth, then set this to `awssigv4`. AWS credentials will be read from the environment and used to sign your requests.


#### Possible values

`basicauth`, `apikey`, `awssigv4`

### `ELASTICSEARCH_TIMEOUT`

*Optional*, default value: `40`

How long to wait on Elasticsearch requests.

### `ELASTICSEARCH_INDEX`

*Optional*, default value: `filebeat-*`

The index to target. Globs are supported.

### `ELASTICSEARCH_TIMESTAMP_FIELD`

*Optional*, default value: `@timestamp`

The field which denotes the timestamp in the indexed logs.
<!-- generated env. vars. end -->

## Usage

<!-- generated usage start -->
```
Usage: elastic-logs [OPTIONS] QUERY

  Stream logs from Elasticsearch.

  Accepts a KQL query as its only positional argument.

Options:
  -p, --page-size INTEGER RANGE  The number of logs to fetch per page  [x>=0]
  -i, --index TEXT               The index to target. Globs are supported.
                                 [default: (filebeat-*)]
  -s, --start TEXT               When to begin streaming logs from.
  -e, --end TEXT                 When to stop streaming logs. Omit to
                                 continuously stream logs until interrupted.
  --source CSV                   Source fields to retrieve, comma-separated.
                                 Default behaviour is to fetch full document.
  -t, --timestamp-field TEXT     The field which denotes the timestamp in the
                                 indexed logs.  [default: (@timestamp)]
  --version                      Show version and exit.
  --help                         Show this message and exit.

```
<!-- generated usage end -->


### Example

```shell
elastic-logs \
    --start 2022-03-05T12:00:00 \
    --end 2022-03-05T13:00:00 \
    --source time,level,message,error \
    --index filebeat-7.16.2 \
    --timestamp-field time \
    'level:ERROR and error.code:500'
```

### KQL support

The following KQL features are not yet supported:

- Wildcard fields, e.g. `*:value` or `machine.os*:windows 10`
- Prefix matching, e.g. `machine.os:win*`
- Match phrase, e.g. `message:"A quick brown fox"`

## Development

Install dependencies:

```shell
pyenv shell 3.10.x
pre-commit install  # Configure commit hooks
poetry install  # Install Python dependencies
```

Run tests:

```shell
poetry run inv verify
```

# License
This project is distributed under the MIT license.
