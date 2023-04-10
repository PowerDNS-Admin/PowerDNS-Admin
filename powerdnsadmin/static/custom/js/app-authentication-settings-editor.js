let model;

let AuthenticationSettingsModel = function (user_data, api_url, csrf_token, selector) {
    let self = this;
    self.api_url = api_url;
    self.csrf_token = csrf_token;
    self.selector = selector;
    self.loading = false;

    let defaults = {
        tab_active: '',
        tab_default: 'local',

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

    self.data = {};

    self.setupObservables = function () {
        self.loading = ko.observable(self.loading);
        self.tab_active = ko.observable(self.data.tab_active);
        self.tab_default = ko.observable(self.data.tab_default);

        // Local Authentication Settings
        self.local_db_enabled = ko.observable(self.data.local_db_enabled);
        self.signup_enabled = ko.observable(self.data.signup_enabled);
        self.pwd_enforce_characters = ko.observable(self.data.pwd_enforce_characters);
        self.pwd_min_len = ko.observable(self.data.pwd_min_len);
        self.pwd_min_lowercase = ko.observable(self.data.pwd_min_lowercase);
        self.pwd_min_uppercase = ko.observable(self.data.pwd_min_uppercase);
        self.pwd_min_digits = ko.observable(self.data.pwd_min_digits);
        self.pwd_min_special = ko.observable(self.data.pwd_min_special);
        self.pwd_enforce_complexity = ko.observable(self.data.pwd_enforce_complexity);
        self.pwd_min_complexity = ko.observable(self.data.pwd_min_complexity);

        // LDAP Authentication Settings
        self.ldap_enabled = ko.observable(self.data.ldap_enabled);
        self.ldap_type = ko.observable(self.data.ldap_type);
        self.ldap_uri = ko.observable(self.data.ldap_uri);
        self.ldap_base_dn = ko.observable(self.data.ldap_base_dn);
        self.ldap_admin_username = ko.observable(self.data.ldap_admin_username);
        self.ldap_admin_password = ko.observable(self.data.ldap_admin_password);
        self.ldap_domain = ko.observable(self.data.ldap_domain);
        self.ldap_filter_basic = ko.observable(self.data.ldap_filter_basic);
        self.ldap_filter_username = ko.observable(self.data.ldap_filter_username);
        self.ldap_filter_group = ko.observable(self.data.ldap_filter_group);
        self.ldap_filter_groupname = ko.observable(self.data.ldap_filter_groupname);
        self.ldap_sg_enabled = ko.observable(self.data.ldap_sg_enabled);
        self.ldap_admin_group = ko.observable(self.data.ldap_admin_group);
        self.ldap_operator_group = ko.observable(self.data.ldap_operator_group);
        self.ldap_user_group = ko.observable(self.data.ldap_user_group);
        self.autoprovisioning = ko.observable(self.data.autoprovisioning);
        self.autoprovisioning_attribute = ko.observable(self.data.autoprovisioning_attribute);
        self.urn_value = ko.observable(self.data.urn_value);
        self.purge = ko.observable(self.data.purge);

        // Google OAuth2 Settings
        self.google_oauth_enabled = ko.observable(self.data.google_oauth_enabled);
        self.google_oauth_client_id = ko.observable(self.data.google_oauth_client_id);
        self.google_oauth_client_secret = ko.observable(self.data.google_oauth_client_secret);
        self.google_oauth_scope = ko.observable(self.data.google_oauth_scope);
        self.google_base_url = ko.observable(self.data.google_base_url);
        self.google_oauth_auto_configure = ko.observable(self.data.google_oauth_auto_configure);
        self.google_oauth_metadata_url = ko.observable(self.data.google_oauth_metadata_url);
        self.google_token_url = ko.observable(self.data.google_token_url);
        self.google_authorize_url = ko.observable(self.data.google_authorize_url);

        // GitHub OAuth2 Settings
        self.github_oauth_enabled = ko.observable(self.data.github_oauth_enabled);
        self.github_oauth_key = ko.observable(self.data.github_oauth_key);
        self.github_oauth_secret = ko.observable(self.data.github_oauth_secret);
        self.github_oauth_scope = ko.observable(self.data.github_oauth_scope);
        self.github_oauth_api_url = ko.observable(self.data.github_oauth_api_url);
        self.github_oauth_auto_configure = ko.observable(self.data.github_oauth_auto_configure);
        self.github_oauth_metadata_url = ko.observable(self.data.github_oauth_metadata_url);
        self.github_oauth_token_url = ko.observable(self.data.github_oauth_token_url);
        self.github_oauth_authorize_url = ko.observable(self.data.github_oauth_authorize_url);

        // Azure AD OAuth2 Settings
        self.azure_oauth_enabled = ko.observable(self.data.azure_oauth_enabled);
        self.azure_oauth_key = ko.observable(self.data.azure_oauth_key);
        self.azure_oauth_secret = ko.observable(self.data.azure_oauth_secret);
        self.azure_oauth_scope = ko.observable(self.data.azure_oauth_scope);
        self.azure_oauth_api_url = ko.observable(self.data.azure_oauth_api_url);
        self.azure_oauth_auto_configure = ko.observable(self.data.azure_oauth_auto_configure);
        self.azure_oauth_metadata_url = ko.observable(self.data.azure_oauth_metadata_url);
        self.azure_oauth_token_url = ko.observable(self.data.azure_oauth_token_url);
        self.azure_oauth_authorize_url = ko.observable(self.data.azure_oauth_authorize_url);
        self.azure_sg_enabled = ko.observable(self.data.azure_sg_enabled);
        self.azure_admin_group = ko.observable(self.data.azure_admin_group);
        self.azure_operator_group = ko.observable(self.data.azure_operator_group);
        self.azure_user_group = ko.observable(self.data.azure_user_group);
        self.azure_group_accounts_enabled = ko.observable(self.data.azure_group_accounts_enabled);
        self.azure_group_accounts_name = ko.observable(self.data.azure_group_accounts_name);
        self.azure_group_accounts_name_re = ko.observable(self.data.azure_group_accounts_name_re);
        self.azure_group_accounts_description = ko.observable(self.data.azure_group_accounts_description);
        self.azure_group_accounts_description_re = ko.observable(self.data.azure_group_accounts_description_re);

        // OIDC OAuth2 Settings
        self.oidc_oauth_enabled = ko.observable(self.data.oidc_oauth_enabled);
        self.oidc_oauth_key = ko.observable(self.data.oidc_oauth_key);
        self.oidc_oauth_secret = ko.observable(self.data.oidc_oauth_secret);
        self.oidc_oauth_scope = ko.observable(self.data.oidc_oauth_scope);
        self.oidc_oauth_api_url = ko.observable(self.data.oidc_oauth_api_url);
        self.oidc_oauth_auto_configure = ko.observable(self.data.oidc_oauth_auto_configure);
        self.oidc_oauth_metadata_url = ko.observable(self.data.oidc_oauth_metadata_url);
        self.oidc_oauth_token_url = ko.observable(self.data.oidc_oauth_token_url);
        self.oidc_oauth_authorize_url = ko.observable(self.data.oidc_oauth_authorize_url);
        self.oidc_oauth_logout_url = ko.observable(self.data.oidc_oauth_logout_url);
        self.oidc_oauth_username = ko.observable(self.data.oidc_oauth_username);
        self.oidc_oauth_email = ko.observable(self.data.oidc_oauth_email);
        self.oidc_oauth_firstname = ko.observable(self.data.oidc_oauth_firstname);
        self.oidc_oauth_last_name = ko.observable(self.data.oidc_oauth_last_name);
        self.oidc_oauth_account_name_property = ko.observable(self.data.oidc_oauth_account_name_property);
        self.oidc_oauth_account_description_property = ko.observable(self.data.oidc_oauth_account_description_property);
    }

    self.initTabs = function () {
        if (self.hasHash()) {
            self.activateTab(self.getHash());
        } else {
            self.activateDefaultTab();
        }
    }

    self.loadData = function () {
        self.loading = true;
        $.ajax({
            url: self.api_url,
            type: 'POST',
            data: {_csrf_token: csrf_token},
            dataType: 'json',
            success: self.onDataLoaded
        });
    }

    self.updateWithDefaults = function (instance) {
        self.data = $.extend(defaults, instance)
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

    self.onDataLoaded = function (data) {
        self.updateWithDefaults(data);
        self.setupObservables();
        self.loading = false;

        let el = null;
        if (typeof selector !== 'undefined') {
            el = $(selector)
        }

        if (el !== null && el.length > 0) {
            ko.applyBindings(self, el[0]);
        } else {
            ko.applyBindings(self);
        }

        self.initTabs();
        self.setupListeners();
    }

    self.onTabClick = function (model, event) {
        self.activateTab($(event.target).data('tab'));
        return false;
    }

    self.onHashChange = function (event) {
        let hash = window.location.hash.trim();
        if (hash.length > 1) {
            self.activateTab(hash.substring(1));
        } else {
            self.activateDefaultTab();
        }
    }

    self.loadData();
}

$(function () {
    // TODO: Load the data from the server and pass it to the model instantiation
    loaded_data = {};
    model = new AuthenticationSettingsModel(loaded_data, API_URL, CSRF_TOKEN, '#settings-editor');
})