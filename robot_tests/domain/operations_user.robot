| *** Settings *** |
|                  |
| Documentation    | Test Web User interface of PowerDNS-Admin installation
| Library          | OperatingSystem
| Library          | RequestsLibrary
| Library          | json
| Library          | Selenium2Library        | run_on_failure=Nothing
| Resource         | ../resource/basic.robot
| Suite Teardown   | Cleanup


| *** Variables ***   |
|                     |
| ${base_url}         | http://localhost:9191
| ${admin_user}       | admin
| ${admin_pass}       | admin
| ${admin_email}      | admin@admin.com
| ${user}             | user-domain
| ${pass}             | user-domain
| ${email}            | user-domain@user.com
| ${browser}          | headlessfirefox
| #${browser}         | firefox
| ${test_domain1}     | example-user.org
| ${test_server}      | test_server
| ${test_server_ip}   | 192.168.5.12
| ${test_server_edit} | test_server_edit
| ${path_domain_add}  | //a[@href="/admin/domain/add"]


| *** Keywords *** |
|                  |
| Cleanup          |
|                  | Login              | ${admin_user}            | ${admin_pass}
|                  | Delete Domain      | ${test_domain1}          |
|                  | Toggle Setting     | allow_user_create_domain | OFF
|                  | Close All Browsers |                          |


| *** Test Cases *** |
|                    |
| Register Admin     | [Documentation] | Creates admin user    |
|                    | Register User   | ${admin_user}         | ${admin_pass} | ${admin_email} | ${base_url} | ${browser}


| Register User      | [Documentation] | Creates ordinary user |
|                    | Register User   | ${user}               | ${pass}       | ${email}       | ${base_url} | ${browser}


| Create domain Failure | [Documentation]   | Test create domain failure when User does not have permissions to create domain |
|                       | Login             | ${user}                      | ${pass}                                          |
|                       | ${msg}            | Run Keyword And Ignore Error | Wait Until Element Is Visible                    | xpath:${path_domain_add} | timeout=10
|                       | Should Start With | ${msg[1]}                    | Element 'xpath:${path_domain_add}' not visible   |


| Allow create domain | [Documentation]              | Test toggling allow create domain for ordinary user |               |
|                     | Login                        | ${admin_user}                                       | ${admin_pass} |
|                     | Toggle Setting               | allow_user_create_domain                            | ON            |


| Create Domain       | [Documentation]               | Test create domain by Admin User           |
|                     | Login                         | ${user}                                    | ${pass}
|                     | Create Domain                 | ${test_domain1}                            |


| Create Records | [Documentation]                   | Test create domain records by User         |
|                | Login                             | ${user}                                    | ${pass}
|                | Click Link                        | xpath=//a[@href="/domain/${test_domain1}"] |
|                | Wait Until Element Is Visible     | id:${test_domain1}                         | timeout=5
|                | Add Record                        | ${test_server}                             | ${test_server_ip}


| Edit Records   | [Documentation]                   | Test edit domain records by User           |
|                | Login                             | ${user}                                    | ${pass}
|                | Click Link                        | xpath=//a[@href="/domain/${test_domain1}"] |
|                | Wait Until Element Is Visible     | id=${test_domain1}                         | timeout=5
|                | Edit Record                       | ${test_server_edit}                        |


| Delete Records | [Documentation]                   | Test delete domain records by User         |
|                | Login                             | ${user}                                    | ${pass}
|                | Click Link                        | xpath=//a[@href="/domain/${test_domain1}"] |
|                | Wait Until Element Is Visible     | id=${test_domain1}                         | timeout=5
|                | Delete Record                     |                                            |
|                | Click Link                        | xpath=//a[@href="/dashboard"]              |
|                | Click Link                        | xpath=//a[@href="/domain/${test_domain1}"] |
|                | Wait Until Element Is Visible     | class=dataTables_empty                     | timeout=5


| Delete Domain  | [Documentation]                   | Test delete domain by User                 |
|                | Login                             | ${user}                                    | ${pass}
|                | ${msg}                            | Run Keyword And Ignore Error               | Delete Domain | ${test_domain1}
|                | Should Start With                 | ${msg[1]}                                  | Button with locator 'class=btn-danger' not found
