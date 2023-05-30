# Apache collector

## Overview

Apache is an open-source HTTP server for modern operating systems including UNIX and Windows.

This collector will collect metrics directly exposed by one or more Apache servers, depending on your configuration. 
We recommend to also monitor Apache as a process, using the [apps.plugin](https://github.com/netdata/netdata/blob/master/collectors/apps.plugin/README.md) and also monitor Apache's logs through the [weblog collector](https://github.com/netdata/go.d.plugin/blob/master/modules/weblog/README.md).

The collector will also autodetect any default Apache server running on port PORT

## Collected metrics

TBD


### global

TBD

This scope no labels.

Metrics:

| Metric   | Dimensions | Unit | Description |
| -------|  :-------: | :--------: | :--------: |
|apache.connections|connections |connections|This metric shows the total number of connections to your Apache server, helping to measure the overall demand on your server.
|apache.conns_async|keepalive, closing, writing |connections|This metric monitors the state of asynchronous connections, allowing you to identify potential bottlenecks or server capacity issues.
|apache.workers|idle, busy |workers|This metric tracks the number of idle and busy worker threads, helpful in identifying if your server has enough capacity to handle requests.
|apache.scoreboard|waiting, starting, reading, sending, keepalive, dns_lookup, closing, logging, finishing, idle_cleanup, open |connections|This metric provides a granular view of what each worker is doing, beneficial for identifying performance issues patterns.
|apache.requests|requests |requests/s|This metric records the number of requests per second, useful for tracking the load on your server.
|apache.net|sent |kilobit/s|This metric monitors the bandwidth used by Apache, essential for understanding your server's usage patterns and ensuring sufficient network capacity.
|apache.reqpersec|requests |requests/s|This metric records the lifetime average number of requests per second, useful for understanding the average load on your server and for long-term capacity planning.
|apache.bytespersec|served |KiB/s|This metric represents the lifetime average number of bytes served per second, helping to understand the data serving rate of your server.
|apache.bytesperreq|size |KiB|This metric shows the average response size over the lifetime of the Apache server, helpful to understand the efficiency of your server.
|apache.uptime|uptime |seconds|This metric indicates the total time for which the Apache server has been running, useful in detecting any unscheduled downtimes or server crashes and provides an indicator of overall server stability.


## Setup

### Prerequisites

#### Enabling your Apache server

- Ensure the [Apache status module](https://httpd.apache.org/docs/2.4/mod/mod_status.html) is enabled and configured for Apache instance.
- Ensure the Apache status module endpoint (default `server-status`) is available from the host containing the Apache integration.


### Configuration

#### File format

This file is in YAML format. Generally the format is:

```yaml
update_every: 1
autodetection_retry: 0
jobs:
  - name: some_name1
  - name: some_name1
```

#### Options

The following options can be defined globally: update_every, autodetection_retry.

<details>
<summary>All options</summary>

| Name   | Description | Default |
| :-------:| ----------- | :-------: |
|update_every|Data collection frequency.|1 |
|autodetection_retry|Re-check interval in seconds. Zero means not to schedule re-check.|0 |
|url|Server URL.|`http://127.0.0.1/server-status?auto` |
|timeout|HTTP request timeout.|1 |
|username|Username for basic HTTP authentication.|- |
|password|Password for basic HTTP authentication.|- |
|proxy_url|The Proxie's URL.|- |
|proxy_username|Username for proxy basic HTTP authentication.|- |
|proxy_password|Password for proxy basic HTTP authentication.|- |
|method|HTTP request method.|GET |
|body|HTTP request body.|- |
|headers|HTTP request headers.|- |
|not_follow_redirects|Whether to not follow redirects from the server.|no |
|tls_skip_verify|Whether to skip verifying server's certificate chain and hostname.|no |
|tls_ca|Certificate authority that client use when verifying server certificates.|- |
|tls_cert|Client tls certificate.|- |
|tls_key|Client tls key.|- |

</details>

#### Examples

##### Basic

An example configuration.
<details>
<summary>Example</summary>

```yaml
jobs:
  - name: local
    url: http://127.0.0.1/server-status?auto
```

</details>

##### Basic HTTP auth

Local server with basic HTTP authentication.
<details>
<summary>Example</summary>

```yaml
jobs:
  - name: local
    url: https://127.0.0.1/server-status?auto
    username: foo
    password: bar
```

</details>

##### Multi-instance

When you are defining more than one jobs, you must be careful to use different job names, to not override each other.
<details>
<summary>Example</summary>

```yaml
jobs:
  - name: local
    http://127.0.0.1/server-status?auto
  
  - name: remote
    http://192.0.2.0/server-status?auto
```

</details>

## Troubleshooting

### Debug mode

To troubleshoot issues with the `apache` collector, run the `go.d.plugin` with the debug option enabled. The output
should give you clues as to why the collector isn't working.

- Navigate to the `plugins.d` directory, usually at `/usr/libexec/netdata/plugins.d/`. If that's not the case on
  your system, open `netdata.conf` and look for the `plugins` setting under `[directories]`.

  ```bash
  cd /usr/libexec/netdata/plugins.d/
  ```

- Switch to the `netdata` user.

  ```bash
  sudo -u netdata -s
  ```

- Run the `go.d.plugin` to debug the collector:

  ```bash
  ./go.d.plugin -d -m apache
  ```
