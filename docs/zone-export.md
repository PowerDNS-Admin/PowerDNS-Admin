# Zone export

Open a zone in the Zone Editor and select **Zone Export**. The export page shows
PowerDNS's BIND-compatible zone file in a read-only text area. Select individual
lines, use **Copy to clipboard** to copy the complete file, or use **Download** to save it as
`<zone>.zone`. The copy and download icons are on the right above the file.
**Back to zone** returns to the Zone Editor.

The export contains the saved zone. Apply pending editor changes before opening
the export page. The download on that page contains exactly the displayed text.
PowerDNS generates the file, including its handling of disabled records and
record types; PowerDNS-Admin does not reconstruct records from the editor table.

Administrators and Operators may export zones. To enable exports for the User
role, turn on `allow_user_export_domain` under **Settings > Basic Settings**.
The default is off. Users still need access to the zone, either directly or
through an account. The same rules apply to API key roles and their zone/account
assignments.

## API

`GET /api/v1/servers/{server_id}/zones/{zone_id}/export` returns the zone file
as a UTF-8 `text/plain` attachment. Authenticate with a base64-encoded API key in the `X-API-Key` header:

```sh
curl --fail --header 'X-API-Key: YOUR_BASE64_ENCODED_API_KEY' \
  'http://localhost:9191/api/v1/servers/localhost/zones/example.org./export' \
  --output example.org.zone
```

Missing export permission returns HTTP 401, following the existing API privilege
checks. Missing zone access returns HTTP 403. An upstream failure
or invalid PowerDNS export returns HTTP 502.
