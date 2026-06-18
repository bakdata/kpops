# Migrate from V9 to V10

## Helm diff config

- https://github.com/bakdata/kpops/pull/600
- https://github.com/bakdata/kpops/pull/601

The Helm diff configuration has moved from `config.yaml` to the `HelmApp` component. To ignore specific keypaths we use string arrays now (formerly dot-notation). It is now possible to ignore YAML keys containing `.` or other special characters.

### Example

#### defaults.yaml

```yaml
helm-app:
  diff_config:
    ignore:
      - ["metadata", "labels", "helm.sh/chart"]
```
