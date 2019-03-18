| *** Settings *** |
|                  |
| Documentation    | Test User and Group management
| Library          | OperatingSystem
| Library          | RequestsLibrary
| Library          | json
| Library          | Selenium2Library       | run_on_failure=Nothing
| Resource         | ../resource/user.robot
| Resource         | ../resource/domain.robot
| Suite Teardown   | Cleanup


| *** Variables ***     |
|                       |
| ${base_url}           | http://localhost:9191
| ${admin_user}         | admin
| ${admin_pass}         | admin
| ${admin_email}        | admin@admin.com
| ${user}               | user-manage
| ${user1}              | user-manage1
| ${pass}               | user-manage
| ${email}              | user-manage@user.com
| ${browser}            | headlessfirefox
| #${browser}           | firefox


| *** Keywords *** |
|                  |
| Cleanup          |
|                  | Close All Browsers


| *** Test Cases *** |
|                    |
| Add User           | [Documentation] | Test add User    |
|                    | Login           | ${admin_user}    | ${admin_pass}
|                    | Add User        | ${user}          | ${pass}       | ${email}


| Edit User          | [Documentation] | Test edit User   |
|                    | Login           | ${admin_user}    | ${admin_pass}
|                    | Edit User       | ${user}          | ${user1}


| Delete User        | [Documentation] | Test delete User |
|                    | Login           | ${admin_user}    | ${admin_pass}
|                    | Delete User     | ${user}          | ${user1}
