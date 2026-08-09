terraform {
  required_version = ">= 1.15.0, < 1.16.0"

  required_providers {
    powerdns = {
      source  = "pan-net/powerdns"
      version = "1.5.0"
    }
  }

  # Connection settings come from PG_CONN_STR / PG_SCHEMA_NAME on the
  # terraform-pdns-seed service. Net-new deployments only; no local-state
  # migration path is provided.
  backend "pg" {}
}

provider "powerdns" {}

locals {
  # Terraform limits range() to 1,024 generated values, so build large zone
  # indexes from batches of at most 1,000 values.
  zone_indexes = flatten([
    for batch_index in range(ceil(var.zone_count / 1000)) : [
      for offset in range(1000) : batch_index * 1000 + offset
      if batch_index * 1000 + offset < var.zone_count
    ]
  ])

  zones = {
    for zone_index in local.zone_indexes :
    format("zone-%05d.%s", zone_index + 1, var.zone_suffix) => zone_index
  }

  records = {
    for record in flatten([
      for zone_name, zone_index in local.zones : [
        for record_index in range(var.records_per_zone) : {
          key          = format("%05d-%02d", zone_index + 1, record_index + 1)
          zone_name    = zone_name
          zone_index   = zone_index
          record_index = record_index
        }
      ]
    ]) : record.key => record
  }
}

resource "powerdns_zone" "load" {
  for_each = local.zones

  name = each.key
  kind = "Native"
}

resource "powerdns_record" "load" {
  for_each = local.records

  zone = powerdns_zone.load[each.value.zone_name].name
  name = format("record-%02d.%s", each.value.record_index + 1, each.value.zone_name)
  type = "A"
  ttl  = var.record_ttl
  records = [
    format(
      "10.%d.%d.%d",
      floor(each.value.zone_index / 256) % 256,
      each.value.zone_index % 256,
      each.value.record_index + 1,
    )
  ]
}

output "seed_summary" {
  value = {
    zone_count       = length(powerdns_zone.load)
    records_per_zone = var.records_per_zone
    record_count     = length(powerdns_record.load)
  }
}
