variable "zone_count" {
  description = "Number of deterministic test zones to manage."
  type        = number
  default     = 10000

  validation {
    condition     = var.zone_count >= 1 && var.zone_count <= 100000 && floor(var.zone_count) == var.zone_count
    error_message = "zone_count must be a whole number between 1 and 100000."
  }
}

variable "records_per_zone" {
  description = "Number of A-record RRsets to manage in each test zone."
  type        = number
  default     = 20

  validation {
    condition     = var.records_per_zone >= 1 && var.records_per_zone <= 254 && floor(var.records_per_zone) == var.records_per_zone
    error_message = "records_per_zone must be a whole number between 1 and 254."
  }
}

variable "zone_suffix" {
  description = "Suffix for generated zones, including the trailing dot."
  type        = string
  default     = "terraform.test."

  validation {
    condition     = endswith(var.zone_suffix, ".")
    error_message = "zone_suffix must be an FQDN ending with a dot."
  }
}

variable "record_ttl" {
  description = "TTL applied to generated A-record RRsets."
  type        = number
  default     = 300

  validation {
    condition     = var.record_ttl >= 0 && floor(var.record_ttl) == var.record_ttl
    error_message = "record_ttl must be a non-negative whole number."
  }
}
