| *** Settings *** |
|                  |
| Library          | OperatingSystem
| Library          | RequestsLibrary
| Library          | json
| Library          | Selenium2Library


| *** Variables ***     |
|                       |
| ${path_edit_button}   | //tr[td/text() = "${user}"]/td/button[contains(@class, "button_edit")]
| ${path_delete_button} | //tr[td/text() = "${user}"]/td/button[contains(@class, "button_delete")]


| *** Keywords *** |
|                  |
| Login            | [Arguments]                       | ${username}                             | ${password}
|                  | Open Browser                      | ${base_url}                             | ${browser}
|                  | Wait Until Page Contains Element  | class=login-box-body                    | timeout=10
|                  | Input Text                        | name=username                           | ${username}
|                  | Input Password                    | name=password                           | ${password}
|                  | Click Button                      | xpath://*[contains(text(), "Sign In")]  |
|                  | Wait Until Element Is Visible     | xpath://a[@href="/dashboard"]           | timeout=5
| Register User    |                                   |                                         |             |          |        |
|                  | [Arguments]                       | ${user}                                 | ${pass}     | ${email} | ${url} | ${browser}
|                  | Open Browser                      | ${url}                                  | ${browser}
|                  | Wait Until Page Contains Element  | class=login-box-body                    | timeout=10
|                  | Click Element                     | css:.login-box-body\ a\                 |
|                  | Wait Until Page Contains Element  | class=register-box-body                 | timeout=10
|                  | Input Text                        | name=firstname                          | ${user}
|                  | Input Text                        | name=lastname                           | ${user}
|                  | Input Text                        | name=email                              | ${email}
|                  | Input Text                        | name=username                           | ${user}
|                  | Input Password                    | name=password                           | ${pass}
|                  | Input Password                    | name=rpassword                          | ${pass}
|                  | Click Button                      | xpath=//*[contains(text(), "Register")] |
| Add User         |                                   |                                         |
|                  | [Arguments]                       | ${user}                                 | ${pass}     | ${email}
|                  | Wait Until Element Is Visible     | xpath://a[@href="/admin/manageuser"]    | timeout=5
|                  | Click Link                        | xpath://a[@href="/admin/manageuser"]    |
|                  | Wait Until Element Is Visible     | xpath://table[@id="tbl_users"]          | timeout=5
|                  | Click Button                      | class=button_add_user                   |
|                  | Wait Until Element Is Visible     | class=form-group                        |
|                  | Input Text                        | name=firstname                          | ${user}
|                  | Input Text                        | name=lastname                           | ${user}
|                  | Input Text                        | name=email                              | ${email}
|                  | Input Text                        | name=username                           | ${user}
|                  | Input Password                    | name=password                           | ${pass}
|                  | Click Button                      | css:button[type='submit']               |
|                  | Wait Until Element Is Visible     | xpath=//td[contains(text(), ${user})]   |
| Edit User        |                                   |                                              |
|                  | [Arguments]                       | ${user}                                      | ${user_data}
|                  | Wait Until Element Is Visible     | xpath://a[@href="/admin/manageuser"]         | timeout=5
|                  | Click Link                        | xpath://a[@href="/admin/manageuser"]         |
|                  | Wait Until Element Is Visible     | xpath://table[@id="tbl_users"]               | timeout=5
|                  | Click Button                      | xpath:${path_edit_button}                    |
|                  | Wait Until Element Is Visible     | class=form-group                             |
|                  | Input Text                        | name=firstname                               | ${user_data}
|                  | Input Text                        | name=lastname                                | ${user_data}
|                  | Click Button                      | css:button[type='submit']                    |
|                  | Wait Until Element Is Visible     | xpath://td[contains(text(), ${user_data})]   |
| Delete User      |                                   |                                              |
|                  | [Arguments]                       | ${user}                                      | ${user_data}
|                  | Wait Until Element Is Visible     | xpath://a[@href="/admin/manageuser"]         | timeout=5
|                  | Click Link                        | xpath://a[@href="/admin/manageuser"]         |
|                  | Wait Until Element Is Visible     | xpath://table[@id="tbl_users"]               | timeout=5
|                  | Click Button                      | xpath:${path_delete_button}                  |
|                  | Wait Until Element Is Visible     | id=button_delete_confirm                     | timeout=5
|                  | Click Button                      | id=button_delete_confirm                     |
|                  | Wait Until Element Is Not Visible | class=modal-backdrop                         | timeout=5
|                  | Wait Until Element Is Visible     | xpath://table[@id="tbl_users"]               | timeout=5
|                  | Wait Until Element Is Not Visible | xpath://td[contains(text(), "${user_data}")] | timeout=20
