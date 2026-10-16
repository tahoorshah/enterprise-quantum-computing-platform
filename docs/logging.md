## Centralized Logging (Loki + Promtail)

Pod logs are collected by Promtail, deployed as a DaemonSet that tails the
container log files on each node (`/var/log/pods/*/*/*.log`) with a `cri`
pipeline stage and ships them to Loki at `http://loki:3100`. Loki is
registered as a Grafana data source, so logs are queryable in Grafana
alongside the Prometheus metrics. Backend access logs — including blocked
requests (401 / 403 / 404 / 429) — are shown live on the
"Security - blocked requests" dashboard panel.
