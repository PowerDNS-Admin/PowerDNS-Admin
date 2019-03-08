*** Settings ***
Documentation   Test Web User interface of PowerDNS-Admin installation
Library         OperatingSystem
Library         RequestsLibrary
Library         json
Library         Selenium2Library
Suite teardown  Run Keywords  Close all browsers  AND  Delete All Sessions

*** Variables ***
${base_url}        http://powerdns-admin:9191
${admin_user}      admin
${admin_pass}      admin
${admin_email}     admin@admin.com
${browser}         headlessfirefox
#${browser}        firefox
${test_domain1}    example.org

*** Test Cases ***

Register Admin
  [Documentation]  Creates admin user
  Open Browser     ${base_url}  ${browser}
  Wait Until Page Contains Element  class=login-box-body  timeout=10
  Click Element  css:.login-box-body\ a\
  Wait Until Page Contains Element  class=register-box-body  timeout=10
  Input Text       name=firstname  ${admin_user}
  Input Text       name=lastname   ${admin_user}
  Input Text       name=email      ${admin_email}
  Input Text       name=username   ${admin_user}
  Input Password   name=password   ${admin_pass}
  Input Password   name=rpassword  ${admin_pass}
  Click Button     xpath: //*[contains(text(), "Register")]

Test create domain by Admin
  [Documentation]  Created domain by Admin User
  Open Browser     ${base_url}  ${browser}
  Wait Until Page Contains Element  class=login-box-body  timeout=10
  Input Text       name=username   ${admin_user}
  Input Password   name=password   ${admin_pass}
  Click Button     xpath: //*[contains(text(), "Sign In")]
  Wait Until Element Is Visible  xpath://a[@href="/admin/domain/add"]    timeout=5
  Click Link       xpath://a[@href="/admin/domain/add"]
  Wait Until Element Is Visible  id=domain_name    timeout=5
  Input Text       id=domain_name    ${test_domain1}
  Click Button     xpath://*[contains(text(), "Submit")]
  Wait Until Element Is Visible  xpath://a[@href="/domain/${test_domain1}"]    timeout=5
