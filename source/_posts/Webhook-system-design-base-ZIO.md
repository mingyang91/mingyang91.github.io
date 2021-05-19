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

* Can send event message by http post
* Can record success/error fragment from third-party reply.
* It should be retry send after third-party reply error or down.

# Features

* Delivery (HTTP POST)
* Success / Error Record
* Failed Retry
* Run In Multi-Process Environment (e.g. Kubernetes)
* Throttle fequency by send to Third-party System.
* Metrics
* Older record archive/deletion
* Prevent sent too fequencly after massive event generated.

# Results