| *** Settings *** |
|                  |
| Library          | OperatingSystem
| Library          | RequestsLibrary
| Library          | json
| Library          | Selenium2Library

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
| Add Record       |                                   |
|                  | [Arguments]                       | ${record_name}                                                         | ${record_content}
|                  | Click Button                      | class=button_add_record                                                |
|                  | Input Text                        | id=edit-row-focus                                                      | ${record_name}
|                  | Input Text                        | id=current_edit_record_data                                            | ${record_content}
|                  | Click Button                      | class=button_save                                                      |
|                  | Element Text Should Be            | xpath=//table[@id='tbl_records']/*/tr[1]/td[1]                         | ${record_name}
|                  | Apply Changes                     |
| Edit Record      |                                   |
|                  | [Arguments]                       | ${record_name}
|                  | Click Button                      | class=button_edit                                                      |
|                  | Input Text                        | id=edit-row-focus                                                      | ${record_name}
|                  | Click Button                      | class=button_save                                                      |
|                  | Wait Until Element Contains       | xpath=//table[@id='tbl_records']/*/tr[1]/td[1]                         | ${record_name} | timeout=5
|                  | Apply Changes                     |
| Delete Record    |                                   |
|                  | Click Button                      | class=button_delete                                                    |
|                  | Wait Until Element Is Visible     | id=button_delete_confirm                                               | timeout=5
|                  | Click Button                      | id=button_delete_confirm                                               |
|                  | Wait Until Element Is Not Visible | id=button_delete_confirm                                               | timeout=5
|                  | Wait Until Element Is Not Visible | class=modal-backdrop                                                   | timeout=5
|                  | Apply Changes                     |                                                                        |
|                  | Wait Until Element Is Visible     | class=dataTables_empty                                                 | timeout=5
| Create Domain    |                                   |
|                  | [Arguments]                       | ${domain}
|                  | Click Link                        | xpath=//a[@href="/admin/domain/add"]                                   |
|                  | Wait Until Element Is Visible     | id=domain_name                                                         | timeout=5
|                  | Input Text                        | id=domain_name                                                         | ${domain}
|                  | Click Button                      | xpath=//*[contains(text(), "Submit")]                                  |
|                  | Wait Until Element Is Visible     | xpath=//a[@href="/domain/${domain}"]                                   | timeout=30
| Delete Domain    |                                   |
|                  | [Arguments]                       | ${domain}
|                  | Click Button                      | class=btn-danger                                                       |
|                  | Wait Until Element Is Visible     | class=delete_domain                                                    | timeout=5
|                  | Click Button                      | class=delete_domain                                                    |
|                  | Wait Until Element Is Visible     | id=button_delete_confirm                                               | timeout=5
|                  | Click Button                      | id=button_delete_confirm                                               |
|                  | Wait Until Element Is Not Visible | id=button_delete_confirm                                               | timeout=5
|                  | Wait Until Element Is Not Visible | class=modal-backdrop                                                   | timeout=5
|                  | Wait Until Element Is Visible     | class=dataTables_empty                                                 | timeout=5
