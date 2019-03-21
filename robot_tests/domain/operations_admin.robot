| *** Settings *** |
|                  |
| Documentation    | Test Domain management By Admin user
| Library          | OperatingSystem
| Library          | json
| Library          | Selenium2Library         | run_on_failure=Nothing
| Resource         | ../resource/domain.robot
| Resource         | ../resource/user.robot
| Suite Teardown   | Cleanup
| Test Teardown    | Cleanup

| *** Variables ***   |
|                     |
| ${base_url}         | http://powerdns-admin-ui-test:9191
| ${admin_user}       | admin
| ${admin_pass}       | admin
| ${admin_email}      | admin@admin.com
| ${browser}          | headlessfirefox
| #${browser}         | firefox
| ${test_domain1}     | example.org
| ${test_server}      | test_server
| ${test_server_ip}   | 192.168.5.12
| ${test_server_edit} | test_server_edit


| *** Keywords *** |
|                  |
| Cleanup          |
|                  | Close All Browsers


| *** Test Cases *** |
|                    |
| Register Admin     | [Documentation]               | Creates admin user |
|                    | Register User                 | ${admin_user}      | ${admin_pass} | ${admin_email} | ${base_url} | ${browser}


| Create Domain      | [Documentation]               | Test create domain by Admin User           |
|                    | Login                         | ${admin_user}                              | ${admin_pass}
|                    | Create Domain                 | ${test_domain1}                            |


| Create Record      | [Documentation]               | Test create domain records by Admin User   |
|                    | Login                         | ${admin_user}                              | ${admin_pass}
|                    | Click Link                    | xpath://a[@href="/domain/${test_domain1}"] |
|                    | Wait Until Element Is Visible | id:${test_domain1}                         | timeout=5
|                    | Add Record                    | ${test_server}                             | ${test_server_ip}


| Edit Records       | [Documentation]               | Test edit domain records by Admin User     |
|                    | Login                         | ${admin_user}                              | ${admin_pass}
|                    | Click Link                    | xpath://a[@href="/domain/${test_domain1}"] |
|                    | Wait Until Element Is Visible | id=${test_domain1}                         | timeout=5
|                    | Edit Record                   | ${test_server_edit}                        |


| Delete Records     | [Documentation]               | Test delete domain records by Admin User   |
|                    | Login                         | ${admin_user}                              | ${admin_pass}
|                    | Wait Until Element Is Visible | xpath://a[@href="/domain/${test_domain1}"] | timeout=10
|                    | Click Link                    | xpath://a[@href="/domain/${test_domain1}"] |
|                    | Wait Until Element Is Visible | id=${test_domain1}                         | timeout=5
|                    | Delete Record                 |                                            |
|                    | Click Link                    | xpath://a[@href="/dashboard"]              |
|                    | Click Link                    | xpath://a[@href="/domain/${test_domain1}"] |
|                    | Wait Until Element Is Visible | class=dataTables_empty                     | timeout=5


| Delete Domain      | [Documentation]               | Test delete domain by Admin User           |
|                    | Login                         | ${admin_user}                              | ${admin_pass}
|                    | Delete Domain                 | ${test_domain1}                            |
