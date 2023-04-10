let AuthenticationSettingsModel = function (user_data, api_url, csrf_token, selector) {
    let self = this;
    self.api_url = api_url;
    self.csrf_token = csrf_token;
    self.selector = selector;
    self.loading = false;
    self.saving = false;
    self.tab_active = '';
    self.tab_default = 'local';

    let defaults = {
        // Local Authentication Settings
        local_db_enabled: true,
        signup_enabled: true,
        pwd_enforce_characters: false,
        pwd_min_len: 10,
        pwd_min_lowercase: 3,
        pwd_min_uppercase: 2,
        pwd_min_digits: 2,
        pwd_min_special: 1,
        pwd_enforce_complexity: false,
        pwd_min_complexity: 11,

        // LDAP Authentication Settings
        ldap_enabled: false,
        ldap_type: 'ldap',
        ldap_uri: '',
        ldap_base_dn: '',
        ldap_admin_username: '',
        ldap_admin_password: '',
        ldap_domain: '',
        ldap_filter_basic: '',
        ldap_filter_username: '',
        ldap_filter_group: '',
        ldap_filter_groupname: '',
        ldap_sg_enabled: 0,
        ldap_admin_group: '',
        ldap_operator_group: '',
        ldap_user_group: '',
        autoprovisioning: 0,
        autoprovisioning_attribute: '',
        urn_value: '',
        purge: 0,

        // Google OAuth2 Settings
        google_oauth_enabled: false,
        google_oauth_client_id: '',
        google_oauth_client_secret: '',
        google_oauth_scope: '',
        google_base_url: '',
        google_oauth_auto_configure: true,
        google_oauth_metadata_url: '',
        google_token_url: '',
        google_authorize_url: '',

        // GitHub OAuth2 Settings
        github_oauth_enabled: false,
        github_oauth_key: '',
        github_oauth_secret: '',
        github_oauth_scope: '',
        github_oauth_api_url: '',
        github_oauth_auto_configure: false,
        github_oauth_metadata_url: '',
        github_oauth_token_url: '',
        github_oauth_authorize_url: '',

        // Azure AD OAuth2 Settings
        azure_oauth_enabled: false,
        azure_oauth_key: '',
        azure_oauth_secret: '',
        azure_oauth_scope: '',
        azure_oauth_api_url: '',
        azure_oauth_auto_configure: true,
        azure_oauth_metadata_url: '',
        azure_oauth_token_url: '',
        azure_oauth_authorize_url: '',
        azure_sg_enabled: false,
        azure_admin_group: '',
        azure_operator_group: '',
        azure_user_group: '',
        azure_group_accounts_enabled: false,
        azure_group_accounts_name: '',
        azure_group_accounts_name_re: '',
        azure_group_accounts_description: '',
        azure_group_accounts_description_re: '',

        // OIDC OAuth2 Settings
        oidc_oauth_enabled: false,
        oidc_oauth_key: '',
        oidc_oauth_secret: '',
        oidc_oauth_scope: '',
        oidc_oauth_api_url: '',
        oidc_oauth_auto_configure: true,
        oidc_oauth_metadata_url: '',
        oidc_oauth_token_url: '',
        oidc_oauth_authorize_url: '',
        oidc_oauth_logout_url: '',
        oidc_oauth_username: '',
        oidc_oauth_email: '',
        oidc_oauth_firstname: '',
        oidc_oauth_last_name: '',
        oidc_oauth_account_name_property: '',
        oidc_oauth_account_description_property: '',
    }
    
    self.init = function (autoload) {
        self.loading = ko.observable(self.loading);
        self.saving = ko.observable(self.saving);
        self.tab_active = ko.observable(self.tab_active);
        self.tab_default = ko.observable(self.tab_default);
        self.update(user_data);

        let el = null;
        if (typeof selector !== 'undefined') {
            el = $(selector)
        }

        if (el !== null && el.length > 0) {
            ko.applyBindings(self, el[0]);
        } else {
            ko.applyBindings(self);
        }

        if (self.hasHash()) {
            self.activateTab(self.getHash());
        } else {
            self.activateDefaultTab();
        }

        self.setupListeners();

        if (autoload) {
            self.load();
        }
    }

    self.load = function () {
        self.loading(true);
        $.ajax({
            url: self.api_url,
            type: 'POST',
            data: {_csrf_token: csrf_token},
            dataType: 'json',
            success: self.onDataLoaded
        });
    }

    self.save = function () {
        self.saving(true);
        $.ajax({
            url: self.api_url,
            type: 'POST',
            data: {_csrf_token: csrf_token, commit: 1, data: JSON.parse(ko.toJSON(self))},
            dataType: 'json',
            success: self.onDataSaved
        });
    }

    self.update = function (instance) {
        for (const [key, value] of Object.entries($.extend(defaults, instance))) {
            if (ko.isObservable(self[key])) {
                self[key](value);
            } else {
                self[key] = ko.observable(value);
            }
        }
    }

    self.activateTab = function (tab) {
        $('[role="tablist"] a.nav-link').blur();
        self.tab_active(tab);
        window.location.hash = tab;
    }

    self.activateDefaultTab = function () {
        self.activateTab(self.tab_default());
    }

    self.getHash = function () {
        return window.location.hash.substring(1);
    }

    self.hasHash = function () {
        return window.location.hash.length > 1;
    }

    self.setupListeners = function () {
        if ('onhashchange' in window) {
            $(window).bind('hashchange', self.onHashChange);
        }
    }

    self.destroyListeners = function () {
        if ('onhashchange' in window) {
            $(window).unbind('hashchange', self.onHashChange);
        }
    }

    self.onDataLoaded = function (result) {
        if (result.status == 0) {
            console.log('Error loading settings: ' + result.messages.join(', '));
            self.loading(false);
            return false;
        }

        self.update(result.data);

        console.log('Settings loaded: ' + result.messages.join(', '));

        self.loading(false);
    }

    self.onDataSaved = function (result) {
        if (result.status == 0) {
            console.log('Error saving settings: ' + result.messages.join(', '));
            self.saving(false);
            return false;
        }

        self.update(result.data);

        console.log('Settings saved: ' + result.messages.join(', '));

        self.saving(false);
    }

    self.onHashChange = function (event) {
        let hash = window.location.hash.trim();
        if (hash.length > 1) {
            self.activateTab(hash.substring(1));
        } else {
            self.activateDefaultTab();
        }
    }

    self.onSaveClick = function (model, event) {
        self.save();
        return false;
    }

    self.onTabClick = function (model, event) {
        self.activateTab($(event.target).data('tab'));
        return false;
    }
}
