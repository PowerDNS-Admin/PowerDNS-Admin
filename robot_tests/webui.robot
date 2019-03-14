| *** Settings *** |
|                  |
| Documentation    | Test Web User interface of PowerDNS-Admin installation
| Library          | OperatingSystem
| Library          | RequestsLibrary
| Library          | json
| Library          | Selenium2Library


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


| *** Keywords *** |
|                  |
| Login            | [Arguments]                       | ${username}                                                            | ${password}
|                  | Open Browser                      | ${base_url}                                                            | ${browser}
|                  | Wait Until Page Contains Element  | class=login-box-body                                                   | timeout=10
|                  | Input Text                        | name=username                                                          | ${username}
|                  | Input Password                    | name=password                                                          | ${password}
|                  | Click Button                      | xpath: //*[contains(text(), "Sign In")]                                |
|                  | Wait Until Element Is Visible     | xpath://a[@href="/admin/domain/add"]                                   | timeout=5
| Apply Changes    |                                   |                                                                        |
|                  | Click Button                      | class=button_apply_changes                                             |
|                  | Wait Until Element Is Visible     | id=button_apply_confirm                                                | timeout=5
|                  | Click Button                      | id=button_apply_confirm                                                |
|                  | Wait Until Element Is Visible     | xpath://div[@id="modal_success"]/*/*/div[@class="modal-footer"]/button | timeout=10
|                  | Click Button                      | xpath://div[@id="modal_success"]/*/*/div[@class="modal-footer"]/button |                                                           |
|                  | Wait Until Element Is Not Visible | class=modal-success                                                    | timeout=20
|                  | Wait Until Element Is Not Visible | class=modal-backdrop                                                   | timeout=5
| Register User    |                                   |
|                  | [Arguments]                       | ${user}                                                                | ${pass}     | ${email} | ${url} | ${browser}
|                  | Open Browser                      | ${url}                                                                 | ${browser}
|                  | Wait Until Page Contains Element  | class=login-box-body                                                   | timeout=10
|                  | Click Element                     | css:.login-box-body\ a\                                                |
|                  | Wait Until Page Contains Element  | class=register-box-body                                                | timeout=10
|                  | Input Text                        | name=firstname                                                         | ${user}
|                  | Input Text                        | name=lastname                                                          | ${user}
|                  | Input Text                        | name=email                                                             | ${email}
|                  | Input Text                        | name=username                                                          | ${user}
|                  | Input Password                    | name=password                                                          | ${pass}
|                  | Input Password                    | name=rpassword                                                         | ${pass}
|                  | Click Button                      | xpath=//*[contains(text(), "Register")]                                |


| *** Test Cases *** |
|                    |
| Register Admin     | [Documentation] | Creates admin user
|                    | Register User   | ${admin_user}      | ${admin_pass} | ${admin_email} | ${base_url} | ${browser}


| Test create domain by Admin | [Documentation]               | Test create domain by Admin User
|                             | Login                         | ${admin_user}                               | ${admin_pass}
|                             | Click Link                    | xpath=//a[@href="/admin/domain/add"]        |
|                             | Wait Until Element Is Visible | id=domain_name                              | timeout=5
|                             | Input Text                    | id=domain_name                              | ${test_domain1}
|                             | Click Button                  | xpath=//*[contains(text(), "Submit")]       |
|                             | Wait Until Element Is Visible | xpath=//a[@href="/domain/${test_domain1}"]  | timeout=30


| Test create domain records by Admin | [Documentation]                   | Test create domain records by Admin User
|                                     | Login                             | ${admin_user}                                  | ${admin_pass}
|                                     | Click Link                        | xpath=//a[@href="/domain/${test_domain1}"]     |
|                                     | Wait Until Element Is Visible     | id:${test_domain1}                             | timeout=5
|                                     | Click Button                      | class=button_add_record                        |
|                                     | Input Text                        | id=edit-row-focus                              | ${test_server}
|                                     | Input Text                        | id=current_edit_record_data                    | ${test_server_ip}
|                                     | Click Button                      | class=button_save                              |
|                                     | Element Text Should Be            | xpath=//table[@id='tbl_records']/*/tr[1]/td[1] | ${test_server}
|                                     | Apply Changes                     |


| Test edit domain records by Admin | [Documentation]                   | Test edit domain records by Admin User         |
|                                   | Login                             | ${admin_user}                                  | ${admin_pass}
|                                   | Click Link                        | xpath=//a[@href="/domain/${test_domain1}"]     |
|                                   | Wait Until Element Is Visible     | id=${test_domain1}                             | timeout=5
|                                   | Click Button                      | class=button_edit                              |
|                                   | Input Text                        | id=edit-row-focus                              | ${test_server_edit}
|                                   | Click Button                      | class=button_save                              |
|                                   | Wait Until Element Contains       | xpath=//table[@id='tbl_records']/*/tr[1]/td[1] | ${test_server_edit} | timeout=5
|                                   | Apply Changes                     |


| Test delete domain records by Admin | [Documentation]                          | Test delete domain records by Admin User
|                                     | Login                                    | ${admin_user}                                  | ${admin_pass}
|                                     | Click Link                               | xpath=//a[@href="/domain/${test_domain1}"]     |
|                                     | Wait Until Element Is Visible            | id=${test_domain1}                             | timeout=5
|                                     | Click Button                             | class=button_delete                            |
|                                     | Wait Until Element Is Visible            | id=button_delete_confirm                       | timeout=5
|                                     | Click Button                             | id=button_delete_confirm                       |
|                                     | Wait Until Element Is Not Visible        | id=button_delete_confirm                       | timeout=5
|                                     | Wait Until Element Is Not Visible        | class=modal-backdrop                           | timeout=5
|                                     | Apply Changes                            |                                                |
|                                     | Wait Until Element Is Visible            | class=dataTables_empty                         | timeout=5
|                                     | Click Link                               | xpath=//a[@href="/dashboard"]                  |
|                                     | Click Link                               | xpath=//a[@href="/domain/${test_domain1}"]     |
|                                     | Wait Until Element Is Visible            | class=dataTables_empty                         | timeout=5
