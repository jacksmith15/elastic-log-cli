# Elastic Log CLI

CLI for streaming logs from Elasticsearch to a terminal.

## Installation

This project is not currently packaged and so must be installed manually.

Clone the project with the following command:
```
git clone https://github.com/jacksmith15/elastic-log-cli.git
```

## Configuration

The following environment variables are used to configure the tool. For secure, easy selection of target clusters, a tool like [envchain](https://github.com/sorah/envchain) is recommended.

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

Whether to authenticate using Basic Auth or an API Key. If using `apikey`, provide as follows:

```
ELASTICSEARCH_USERNAME=${APIKEY_NAME}
ELASTICSEARCH_PASSWORD=${APIKEY_KEY}
```

#### Possible values

`basicauth`, `apikey`

### `ELASTICSEARCH_TIMEOUT`

*Optional*, default value: `40`

How long to wait on Elasticsearch requests.
<!-- generated env. vars. end -->

## Usage

<!-- generated usage start -->
```
Usage: elastic-logs [OPTIONS] QUERY

  Stream logs from Elasticsearch.

  Accepts a KQL query as its only positional argument.

Options:
  -p, --page-size INTEGER RANGE   The number of logs to fetch per page  [x>=0]
  -i, --index TEXT                The index to target. Globs are supported.
  -s, --start [%Y-%m-%d|%Y-%m-%dT%H:%M:%S|%Y-%m-%d %H:%M:%S]
                                  When to begin streaming logs from.
  -e, --end [%Y-%m-%d|%Y-%m-%dT%H:%M:%S|%Y-%m-%d %H:%M:%S]
                                  When to stop streaming logs. Omit to
                                  continuously stream logs until interrupted.
  --source CSV                    Source fields to retrieve, comma-separated.
                                  Default behaviour is to fetch full document.
  -t, --timestamp-field TEXT      The field which denotes the timestamp in the
                                  indexed logs.
  --version                       Show version and exit.
  --help                          Show this message and exit.

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
