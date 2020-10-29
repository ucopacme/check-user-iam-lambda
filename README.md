## Requirements

No requirements.

## Providers

| Name | Version |
|------|---------|
| archive | n/a |
| aws | n/a |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| aws\_region | The AWS region to create things in. | `string` | `"us-west-2"` | no |
| enabled | Set to `false` to prevent the module from creating resources | `bool` | `true` | no |
| name | Resource name | `string` | `null` | no |
| tags | A map of tags to add to all resources | `map(string)` | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| lambda | n/a |
