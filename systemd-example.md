# systemd journal Logs

## Overview

The `systemd` journal plugin by Netdata makes viewing, exploring and analyzing `systemd` journal logs simple and efficient.

It automatically discovers available journal sources, allows advanced filtering, offers interactive visual
representations and supports exploring the logs of both individual servers and the logs on infrastructure wide journal centralization servers.

## Visualization

You can start exploring `systemd` journal logs on the "Logs" tab of the Netdata UI.

## Key features

- Works on both **individual servers** and **journal centralization servers**.
- Supports `persistent` and `volatile` journals.
- Supports `system`, `user`, `namespaces` and `remote` journals.
- Allows filtering on **any journal field** or **field value**, for any time-frame.
- Allows **full text search** (`grep`) on all journal fields, for any time-frame.
- Provides a **histogram** for log entries over time, with a break down per field-value, for any field and any time-frame.
- Works directly on journal files, without any other third-party components.
- Supports coloring log entries, the same way `journalctl` does.
- In PLAY mode provides the same experience as `journalctl -f`, showing new log entries immediately after they are received.

## Prerequisites

- A Netdata Cloud account

## Configuration

This integration is a Netdata Function, there is no configuration needed.

## Log Sources

The plugin automatically detects the available journal sources, based on the journal files available in
`/var/log/journal` (persistent logs) and `/run/log/journal` (volatile logs).

The journals supported are:

- `system` journals
- `user` journals
- `namespaces` journals
- `remote` journals
