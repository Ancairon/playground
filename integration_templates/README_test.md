
---
custom_edit_url: "https://github.com/netdata/go.d.plugin/edit/master/modules/powerdns/metadata.yaml"
sidebar_label: "PowerDNS Authoritative Server"
learn_status: "Published"
learn_rel_path "Data Collection/DNS and DHCP Servers"
---

# PowerDNS Authoritative Server

Plugin: go.d.plugin
Module: powerdns

## Overview

This collector monitors PowerDNS Authoritative Server instances.
It collects metrics from [the internal webserver](https://doc.powerdns.com/authoritative/http-api/index.html#webserver).

Used endpoints:

- [`/api/v1/servers/localhost/statistics`](https://doc.powerdns.com/authoritative/http-api/statistics.html)




This collector is supported on all platforms.

This collector supports collecting metrics from multiple instances of this integration, including remote instances.


### Default Behavior

#### Auto-Detection

This integration doesn't support auto-detection.

#### Limits

The default configuration for this integration does not impose any limits on data collection.

#### Performance Impact

The default configuration for this integration is not expected to impose a significant performance impact on the system.


## Metrics

Metrics grouped by *scope*.

The scope defines the instance that the metric belongs to. An instance is uniquely identified by a set of labels.



### Per PowerDNS Authoritative Server instance

These metrics refer to the entire monitored application.

This scope has no labels.

Metrics:

| Metric | Dimensions | Unit |
|:------|:----------|:----|
| powerdns.questions_in | udp, tcp | questions/s |
| powerdns.questions_out | udp, tcp | questions/s |
| powerdns.cache_usage | query-cache-hit, query-cache-miss, packetcache-hit, packetcache-miss | events/s |
| powerdns.cache_size | query-cache, packet-cache, key-cache, meta-cache | entries |
| powerdns.latency | latency | microseconds |



## Alerts

There are no alerts configured by default for this integration.


## Setup

### Prerequisites

#### Enable webserver

Follow [webserver](https://doc.powerdns.com/authoritative/http-api/index.html#webserver) documentation.


#### Enable HTTP API

Follow [HTTP API](https://doc.powerdns.com/authoritative/http-api/index.html#enabling-the-api) documentation.



### Configuration

#### File

The configuration file name for this integration is `go.d/powerdns.conf`.


You can edit the configuration file using the `edit-config` script from the
Netdata [config directory](https://github.com/netdata/netdata/blob/master/docs/configure/nodes.md#the-netdata-config-directory).

```bash
cd /etc/netdata 2>/dev/null || cd /opt/netdata/etc/netdata
sudo ./edit-config go.d/powerdns.conf
```
#### Options

The following options can be defined globally: update_every, autodetection_retry.


<details><summary>Config options</summary>

| Name | Description | Default | Required |
|:----|:-----------|:-------|:--------:|
| update_every | Data collection frequency. |  | False |
| autodetection_retry | Recheck interval in seconds. Zero means no recheck will be scheduled. |  | False |
| url | Server URL. |  | True |
| timeout | HTTP request timeout. |  | False |
| username | Username for basic HTTP authentication. |  | False |
| password | Password for basic HTTP authentication. |  | False |
| proxy_url | Proxy URL. |  | False |
| proxy_username | Username for proxy basic HTTP authentication. |  | False |
| proxy_password | Password for proxy basic HTTP authentication. |  | False |
| method | HTTP request method. |  | False |
| body | HTTP request body. |  | False |
| headers | HTTP request headers. |  | False |
| not_follow_redirects | Redirect handling policy. Controls whether the client follows redirects. |  | False |
| tls_skip_verify | Server certificate chain and hostname validation policy. Controls whether the client performs this check. |  | False |
| tls_ca | Certification authority that the client uses when verifying the server's certificates. |  | False |
| tls_cert | Client TLS certificate. |  | False |
| tls_key | Client TLS key. |  | False |

</details>

#### Examples

##### Basic

An example configuration.

<details><summary>Config</summary>

```yaml
jobs:
  - name: local
    url: http://127.0.0.1:8081

```
</details>

##### HTTP authentication

Basic HTTP authentication.

<details><summary>Config</summary>

```yaml
jobs:
  - name: local
    url: http://127.0.0.1:8081
    username: admin
    password: password

```
</details>

##### Multi-instance

> **Note**: When you define multiple jobs, their names must be unique.

Local and remote instances.


<details><summary>Config</summary>

```yaml
jobs:
  - name: local
    url: http://127.0.0.1:8081

  - name: remote
    url: http://203.0.113.0:8081

```
</details>



## Troubleshooting

### Debug Mode

To troubleshoot issues with the `powerdns` collector, run the `go.d.plugin` with the debug option enabled. The output
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
  ./go.d.plugin -d -m powerdns
  ```

