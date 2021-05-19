---
title: Webhook system design - base ZIO
date: 2021-05-14 09:42:33
tags:
  - Scala
  - ZIO
  - Webhook
  - Architecture design
---

# Goals

* Sending event message by http post
* Recording success/error response from third-party reply.
* It should re-send message after third-party reply error or down.

# Features

* Delivery (HTTP POST)
* Success / Error Record
* Re-send in the case of third-party failure.
* Run in multi-process environment (e.g. Kubernetes)
* Metrics of backlog message
* Policy of record automatic archive
* Prevent sent too fequencly after massive event generated.(throttle)

# Results