| *** Settings *** |
|                  |
| Documentation    | Test Web User interface of PowerDNS-Admin installation
| Library          | OperatingSystem
| Library          | RequestsLibrary
| Library          | json
| Library          | Selenium2Library
| Resource         | ./resource/basic.robot

| *** Variables ***   |
|                     |
| ${base_url}         | http://localhost:9191
| ${admin_user}       | admin
| ${admin_pass}       | admin
| ${admin_email}      | admin@admin.com
| ${browser}          | headlessfirefox
| #${browser}         | firefox
| ${test_domain1}     | example.org
| ${test_server}      | test_server
| ${test_server_ip}   | 192.168.5.12
| ${test_server_edit} | test_server_edit


| *** Test Cases *** |
|                    |
| Register Admin     | [Documentation] | Creates admin user
|                    | Register User   | ${admin_user}      | ${admin_pass} | ${admin_email} | ${base_url} | ${browser}


| Test create domain by Admin | [Documentation]               | Test create domain by Admin User
|                             | Login                         | ${admin_user}                               | ${admin_pass}
|                             | Create Domain                 | ${test_domain1}                             |


| Test create domain records by Admin | [Documentation]                   | Test create domain records by Admin User
|                                     | Login                             | ${admin_user}                                  | ${admin_pass}
|                                     | Click Link                        | xpath=//a[@href="/domain/${test_domain1}"]     |
|                                     | Wait Until Element Is Visible     | id:${test_domain1}                             | timeout=5
|                                     | Add Record                        | ${test_server}                                 | ${test_server_ip}


| Test edit domain records by Admin | [Documentation]                   | Test edit domain records by Admin User         |
|                                   | Login                             | ${admin_user}                                  | ${admin_pass}
|                                   | Click Link                        | xpath=//a[@href="/domain/${test_domain1}"]     |
|                                   | Wait Until Element Is Visible     | id=${test_domain1}                             | timeout=5
|                                   | Edit Record                       | ${test_server_edit}                            |


| Test delete domain records by Admin | [Documentation]                          | Test delete domain records by Admin User
|                                     | Login                                    | ${admin_user}                                  | ${admin_pass}
|                                     | Click Link                               | xpath=//a[@href="/domain/${test_domain1}"]     |
|                                     | Wait Until Element Is Visible            | id=${test_domain1}                             | timeout=5
|                                     | Delete Record                            |
|                                     | Click Link                               | xpath=//a[@href="/dashboard"]                  |
|                                     | Click Link                               | xpath=//a[@href="/domain/${test_domain1}"]     |
|                                     | Wait Until Element Is Visible            | class=dataTables_empty                         | timeout=5

| Test delete domain by Admin | [Documentation]               | Test delete domain by Admin User
|                             | Login                         | ${admin_user}                               | ${admin_pass}
|                             | Delete Domain                 | ${test_domain1}                             |
