# General Installation

## PowerDNS-Admin Architecture

![PowerDNS-Admin Component Layout](Architecture.png)

A PowerDNS-Admin installation consists of four main components:

-   **PowerDNS-Admin Database:** Stores application data.
-   **PowerDNS-Admin Application Server:** The core application logic.
-   **PowerDNS-Admin Frontend Web Server:** Serves the user interface.
-   **PowerDNS Server:** The DNS server that PowerDNS-Admin manages.

All four components can be installed on a single server. For larger installations or for security purposes, they can be distributed across multiple servers.

## Requirements

-   **Operating System:** A Linux-based system is required. While other systems may work, they are not officially tested or supported.
-   **Python:**
    -   Supported versions: 3.10, 3.11, 3.12, 3.13
    -   Python 3.9 and earlier are not supported due to application dependencies.
    -   Python 3.14 and later are not yet tested or supported.
-   **Database:** PowerDNS-Admin requires its own database, which must be separate from the PowerDNS database. The following databases are supported:
    -   MySQL
    -   PostgreSQL
    -   SQLite
-   **PowerDNS:** A PowerDNS server that will be managed by PowerDNS-Admin.
