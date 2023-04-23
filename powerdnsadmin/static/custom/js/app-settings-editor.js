ko.bindingHandlers.classFlip = {
    init: function (element, valueAccessor, allBindings, viewModel, bindingContext) {
    },
    update: function (element, valueAccessor, allBindings, viewModel, bindingContext) {
        let el = $(element);
        let value = ko.unwrap(valueAccessor());
        let classes = allBindings.get('classFlipClasses') || ['success', 'danger'];

        if (!Array.isArray(classes) || classes.length !== 2) {
            console.error('classFlipClasses option must be an array of two strings');
            return;
        }

        if (value) {
            el.addClass(classes[0]).removeClass(classes[1]);
        } else {
            el.addClass(classes[1]).removeClass(classes[0]);
        }
    }
};

ko.bindingHandlers.textFlip = {
    init: function (element, valueAccessor, allBindings, viewModel, bindingContext) {
    },
    update: function (element, valueAccessor, allBindings, viewModel, bindingContext) {
        let el = $(element);
        let value = ko.unwrap(valueAccessor());
        let classes = allBindings.get('textFlipClasses') || ['Enabled', 'Disabled'];

        if (!Array.isArray(classes) || classes.length !== 2) {
            console.error('textFlipClasses option must be an array of two strings');
            return;
        }

        if (value) {
            el.text(classes[0]);
        } else {
            el.text(classes[1]);
        }
    }
};

ko.bindingHandlers.switchInput = {
    init: function (element, valueAccessor, allBindings, viewModel, bindingContext) {
        let el = $(element);
        let disabled = el.data('disabled') || false;
        let bindings = el.data('bindings');
        let profile = el.data('profile');
        let tpl = bindingContext.$data.templates()['input_switch'];

        // Replace the template variables
        tpl = tpl.replace(/{setting_name}/gm, valueAccessor()().name());
        tpl = tpl.replace(/{disabled}/gm, disabled);
        tpl = tpl.replace(/{bindings}/gm, bindings);
        tpl = tpl.replace(/{profile}/gm, profile);

        // Replace the original element with the template
        el.html(tpl);

        return { 'controlsDescendantBindings': true };
    },
    update: function (element, valueAccessor, allBindings, viewModel, bindingContext) {
        ko.applyBindingsToDescendants(bindingContext, element);
    }
};

ko.bindingHandlers.numberInput = {
    init: function (element, valueAccessor, allBindings, viewModel, bindingContext) {
        let el = $(element);
        let disabled = el.data('disabled') || false;
        let tpl = bindingContext.$data.templates()['input_number'];

        // Replace the template variables
        tpl = tpl.replace(/{setting_name}/gm, valueAccessor()().name());
        tpl = tpl.replace(/{disabled}/gm, disabled);

        // Replace the original element with the template
        el.html(tpl);

        return { 'controlsDescendantBindings': true };
    },
    update: function (element, valueAccessor, allBindings, viewModel, bindingContext) {
        ko.applyBindingsToDescendants(bindingContext, element);
    }
};

ko.bindingHandlers.settingMeta = {
    init: function (element, valueAccessor, allBindings, viewModel, bindingContext) {
        let el = $(element);
        let setting = valueAccessor()();
        let bind_type = el.data('bind-type');
        let tpl = bindingContext.$data.templates()['setting_meta'];

        // Replace the template variables
        tpl = tpl.replace(/{setting_name}/gm, setting.name());
        tpl = tpl.replace(/{bind_type}/gm, bind_type);

        // Replace the original element with the template
        el.html(tpl);

        return { 'controlsDescendantBindings': true };
    },
    update: function (element, valueAccessor, allBindings, viewModel, bindingContext) {
        ko.applyBindingsToDescendants(bindingContext, element);
    }
};

ko.bindingHandlers.settingTitle = {
    init: function (element, valueAccessor, allBindings, viewModel, bindingContext) {
        let el = $(element);
        let setting = valueAccessor()();
        let tpl = bindingContext.$data.templates()['setting_title'];

        // Replace the template variables
        tpl = tpl.replace(/{setting_name}/gm, setting.name());

        // Replace the original element with the template
        el.html(tpl);

        return { 'controlsDescendantBindings': true };
    },
    update: function (element, valueAccessor, allBindings, viewModel, bindingContext) {
        ko.applyBindingsToDescendants(bindingContext, element);
    }
};

ko.bindingHandlers.settingCallout = {
    init: function (element, valueAccessor, allBindings, viewModel, bindingContext) {
        let el = $(element);
        let type = el.data('type');
        let bindings = el.data('bindings');
        let content = el.html();
        let tpl = bindingContext.$data.templates()['setting_callout'];

        // Replace the template variables
        tpl = tpl.replace(/{callout_type}/gm, type);
        tpl = tpl.replace(/{callout_bindings}/gm, bindings);
        tpl = tpl.replace(/{callout_content}/gm, content);

        // Replace the original element with the template
        el.html(tpl);

        return { 'controlsDescendantBindings': true };
    },
    update: function (element, valueAccessor, allBindings, viewModel, bindingContext) {
        ko.applyBindingsToDescendants(bindingContext, element);
    }
};

let SettingsEditorModel = function (user_data, user_options) {
    let self = this;
    let target = null;
    let defaults = {
        debug: false,
        url: '/api/v1/settings',
        token: null,
        selector: null,
    };
    let options = $.extend({}, defaults, user_options);

    if (typeof options.debug !== 'boolean') {
        console.error('SettingsEditorModel "debug" option must be a boolean: ' + options.debug);
        return;
    }

    self.settings = ko.observable({});
    self.templates = ko.observable({});
    self.loading = ko.observable(true);
    self.saving = ko.observable(false);
    self.saved = ko.observable(false);
    self.save_failed = ko.observable(false);
    self.messages = ko.observableArray([]);
    self.messages_class = ko.observable('info');
    self.tab_active = ko.observable('');
    self.tab_default = ko.observable('authentication');

    self.tabs = ko.observableArray([
        ko.observable({id: 'authentication', name: 'Authentication', icon: 'fa fa-lock', parent: null}),
        ko.observable({id: 'mail', name: 'Mail', icon: 'fa fa-envelope', parent: null}),
        ko.observable({id: 'powerdns', name: 'PowerDNS', icon: 'fa fa-server', parent: null}),
        ko.observable({id: 'security', name: 'Security', icon: 'fa fa-shield-alt', parent: null}),
        ko.observable({id: 'ui', name: 'UI', icon: 'fa fa-desktop', parent: null}),
        ko.observable({id: 'zone-editor', name: 'Zone Editor', icon: 'fa fa-edit', parent: null}),
        ko.observable({id: 'local', name: 'Local', icon: 'fa fa-user-lock', parent: 'authentication', def: true}),
        ko.observable({id: 'ldap', name: 'LDAP', icon: 'fa fa-database', parent: 'authentication'}),
        ko.observable({id: 'azure', name: 'Azure OAuth', icon: 'fa-brands fa-microsoft', parent: 'authentication'}),
        ko.observable({id: 'github', name: 'GitHub OAuth', icon: 'fa-brands fa-github', parent: 'authentication'}),
        ko.observable({id: 'google', name: 'Google OAuth', icon: 'fa-brands fa-google', parent: 'authentication'}),
        ko.observable({id: 'oidc', name: 'OpenID Connect', icon: 'fa-brands fa-openid', parent: 'authentication'}),
        ko.observable({id: 'saml', name: 'SAML', icon: 'fa fa-network-wired', parent: 'authentication'}),
    ]);

    self.init = function (autoload) {
        // This is because of Internet Explorer, as usual. I used to say nothing was impossible, but then there was IE.
        document.createElement('setting-callout');
        document.createElement('setting-input');
        document.createElement('setting-meta');
        document.createElement('setting-title');

        // Load editor templates
        let templates = self.templates();

        for (index in options.templates) {
            let template_id = options.templates[index];
            templates[template_id] = $('#' + template_id).html();
        }

        self.templates(templates);

        if (autoload) {
            self.load();
        }
    }

    self.load = function () {
        $.ajax({
            url: options.url,
            type: 'POST',
            data: {_csrf_token: options.token},
            dataType: 'json',
            success: self.onDataLoaded
        });
    }

    self.save = function () {
        if (!target.valid()) {
            return false;
        }
        self.saving(true);
        $.ajax({
            url: options.url,
            type: 'POST',
            data: {_csrf_token: options.token, commit: 1, data: ko.toJSON(self)},
            dataType: 'json',
            success: self.onDataSaved
        });
    }

    self.setupProperties = function (settings) {
        for (const key in settings) {
            if (!settings.hasOwnProperty(key)) {
                continue;
            }
            self[key] = self.observe(settings[key].value);
            self[key + '_config'] = self.observe(settings[key]);
            self[key + '_default'] = self.observe(settings[key].default);
            self[key + '_description'] = self.observe(settings[key].description);
            self[key + '_environment'] = self.observe(settings[key].environment);
            self[key + '_label'] = self.observe(settings[key].label);
            self[key + '_prompts'] = self.observe(settings[key].prompts);
        }
    }

    self.updateProperties = function (settings) {
        for (const key in settings) {
            if (!settings.hasOwnProperty(key)) {
                continue;
            }

            self[key](settings[key].value);
            self[key + '_config'](settings[key]);
            self[key + '_default'](settings[key].default);
            self[key + '_description'](settings[key].description);
            self[key + '_environment'](settings[key].environment);
            self[key + '_label'](settings[key].label);
            self[key + '_prompts'](settings[key].prompts);
        }
    }

    self.setupKnockoutBindings = function () {
        let el = null;
        if (typeof options.selector !== 'undefined' && options.selector !== null) {
            el = $(options.selector)
        }

        if (el !== null && el.length > 0) {
            target = el;

            for (let i = 0; i < el.length; i++) {
                ko.applyBindings(self, el[i]);
            }

            //ko.applyBindings(self, el[0]);
        } else {
            ko.applyBindings(self);
        }
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

    self.setupValidation = function () {
        let uuidRegExp = /^([0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})|[0-9]+$/i;

        let footerErrorElements = [
            'input#local_db_enabled',
        ];

        let errorCheckSelectors = [
            'input.error:not([disabled])',
            'select.error:not([disabled])',
            'textarea.error:not([disabled])',
        ];

        let errorCheckQuery = errorCheckSelectors.join(',');
        let tabs = target.find('.tab-content > *[data-tab]')

        let onElementChanged = function (event) {
            target.valid();
        }

        let auth_enabled = function (value, element, params) {
            let enabled = 0;
            if (self.local_db_enabled()) {
                enabled++;
            }
            if (self.ldap_enabled()) {
                enabled++;
            }
            if (self.google_oauth_enabled()) {
                enabled++;
            }
            if (self.github_oauth_enabled()) {
                enabled++;
            }
            if (self.azure_oauth_enabled()) {
                enabled++;
            }
            if (self.oidc_oauth_enabled()) {
                enabled++;
            }
            return enabled > 0;
        };

        let ldap_exclusive = function (value, element, params) {
            let enabled = 0;
            if (self.ldap_sg_enabled() === 1) {
                enabled++;
            }
            if (self.autoprovisioning() === 1) {
                enabled++;
            }
            return enabled < 2;
        }

        let uuid = function (value, element, params) {
            return uuidRegExp.test(value);
        }

        let local_enabled = function (element) {
            return self.local_db_enabled();
        };

        let ldap_enabled = function (element) {
            return self.ldap_enabled();
        };

        let google_oauth_enabled = function (element) {
            return self.google_oauth_enabled();
        };

        let github_oauth_enabled = function (element) {
            return self.github_oauth_enabled();
        };

        let azure_oauth_enabled = function (element) {
            return self.azure_oauth_enabled();
        };

        let oidc_oauth_enabled = function (element) {
            return self.oidc_oauth_enabled();
        };

        let enforce_characters = function (element) {
            return self.local_db_enabled() === 1 && self.pwd_enforce_characters() === 1;
        };

        let enforce_complexity = function (element) {
            return self.local_db_enabled() === 1 && self.pwd_enforce_complexity() === 1;
        };

        let ldap_type_openldap = function (element) {
            return self.ldap_enabled() && self.ldap_type() === 'ldap';
        };

        let ldap_type_ad = function (element) {
            return self.ldap_enabled() && self.ldap_type() === 'ad';
        };

        let ldap_sg_enabled = function (element) {
            return self.ldap_enabled() === 1 && self.ldap_sg_enabled() === 1;
        }

        let ldap_ap_enabled = function (element) {
            return self.ldap_enabled() === 1 && self.autoprovisioning() === 1;
        }

        let azure_gs_enabled = function (element) {
            return self.azure_oauth_enabled() === 1 && self.azure_sg_enabled() === 1;
        }

        let azure_gas_enabled = function (element) {
            return self.azure_oauth_enabled() && self.azure_group_accounts_enabled();
        }

        let google_oauth_auto_configure_enabled = function (element) {
            return self.google_oauth_enabled() && self.google_oauth_auto_configure();
        }

        let google_oauth_auto_configure_disabled = function (element) {
            return self.google_oauth_enabled() && !self.google_oauth_auto_configure();
        }

        let github_oauth_auto_configure_enabled = function (element) {
            return self.github_oauth_enabled() && self.github_oauth_auto_configure();
        }

        let github_oauth_auto_configure_disabled = function (element) {
            return self.github_oauth_enabled() && !self.github_oauth_auto_configure();
        }

        let azure_oauth_auto_configure_enabled = function (element) {
            return self.azure_oauth_enabled() && self.azure_oauth_auto_configure();
        }

        let azure_oauth_auto_configure_disabled = function (element) {
            return self.azure_oauth_enabled() && !self.azure_oauth_auto_configure();
        }

        let oidc_oauth_auto_configure_enabled = function (element) {
            return self.oidc_oauth_enabled() && self.oidc_oauth_auto_configure();
        }

        let oidc_oauth_auto_configure_disabled = function (element) {
            return self.oidc_oauth_enabled() && !self.oidc_oauth_auto_configure();
        }

        jQuery.validator.addMethod('auth_enabled', auth_enabled, 'At least one authentication method must be enabled.');
        jQuery.validator.addMethod('ldap_exclusive', ldap_exclusive, 'The LDAP group security and role auto-provisioning features are mutually exclusive.');
        jQuery.validator.addMethod('uuid', uuid, 'A valid UUID is required.');

        target.validate({
            ignore: '',
            errorPlacement: function (error, element) {
                let useFooter = false;
                for (let i = 0; i < footerErrorElements.length; i++) {
                    if (element.is(footerErrorElements[i])) {
                        useFooter = true;
                    }
                }
                if (useFooter) {
                    target.find('.card-footer > .error').append(error);
                } else if (element.is('input[type=radio]')) {
                    error.insertAfter(element.parents('div.radio'));
                } else {
                    element.after(error);
                }
            },
            showErrors: function (errorMap, errorList) {
                this.defaultShowErrors();
                tabs.each(function (index, tab) {
                    tab = $(tab);
                    let tabId = tab.data('tab');
                    let tabLink = target.find('.nav-tabs > li > a[data-tab="' + tabId + '"]');
                    if (tab.find(errorCheckQuery).length > 0) {
                        tabLink.addClass('error');
                    } else {
                        tabLink.removeClass('error');
                    }
                });
            },
            rules: {
                local_db_enabled: 'auth_enabled',
                ldap_enabled: 'auth_enabled',
                google_oauth_enabled: 'auth_enabled',
                github_oauth_enabled: 'auth_enabled',
                azure_oauth_enabled: 'auth_enabled',
                oidc_oauth_enabled: 'auth_enabled',
                pwd_min_len: {
                    required: enforce_characters,
                    digits: true,
                    min: 1,
                    max: 64,
                },
                pwd_min_lowercase: {
                    required: enforce_characters,
                    digits: true,
                    min: 0,
                    max: 64,
                },
                pwd_min_uppercase: {
                    required: enforce_characters,
                    digits: true,
                    min: 0,
                    max: 64,
                },
                pwd_min_digits: {
                    required: enforce_characters,
                    digits: true,
                    min: 0,
                    max: 64,
                },
                pwd_min_special: {
                    required: enforce_characters,
                    digits: true,
                    min: 0,
                    max: 64,
                },
                pwd_min_complexity: {
                    required: enforce_complexity,
                    digits: true,
                    min: 1,
                    max: 1000,
                },
                ldap_type: ldap_enabled,
                ldap_uri: {
                    required: ldap_enabled,
                    minlength: 11,
                    maxlength: 255,
                },
                ldap_base_dn: {
                    required: ldap_enabled,
                    minlength: 4,
                    maxlength: 255,
                },
                ldap_admin_username: {
                    required: ldap_type_openldap,
                    minlength: 4,
                    maxlength: 255,
                },
                ldap_admin_password: {
                    required: ldap_type_openldap,
                    minlength: 1,
                    maxlength: 255,
                },
                ldap_domain: {
                    required: ldap_type_ad,
                    minlength: 1,
                    maxlength: 255,
                },
                ldap_filter_basic: {
                    required: ldap_enabled,
                    minlength: 3,
                    maxlength: 1000,
                },
                ldap_filter_username: {
                    required: ldap_enabled,
                    minlength: 1,
                    maxlength: 100,
                },
                ldap_filter_group: {
                    required: ldap_type_openldap,
                    minlength: 3,
                    maxlength: 100,
                },
                ldap_filter_groupname: {
                    required: ldap_type_openldap,
                    minlength: 1,
                    maxlength: 100,
                },
                ldap_sg_enabled: {
                    required: ldap_enabled,
                    ldap_exclusive: true,
                },
                ldap_admin_group: {
                    required: ldap_sg_enabled,
                    minlength: 3,
                    maxlength: 100,
                },
                ldap_operator_group: {
                    required: ldap_sg_enabled,
                    minlength: 3,
                    maxlength: 100,
                },
                ldap_user_group: {
                    required: ldap_sg_enabled,
                    minlength: 3,
                    maxlength: 100,
                },
                autoprovisioning: {
                    required: ldap_enabled,
                    ldap_exclusive: true,
                },
                autoprovisioning_attribute: {
                    required: ldap_ap_enabled,
                    minlength: 1,
                    maxlength: 100,
                },
                urn_value: {
                    required: ldap_ap_enabled,
                    minlength: 1,
                    maxlength: 100,
                },
                purge: ldap_enabled,
                google_oauth_client_id: {
                    required: google_oauth_enabled,
                    minlength: 1,
                    maxlength: 255,
                },
                google_oauth_client_secret: {
                    required: google_oauth_enabled,
                    minlength: 1,
                    maxlength: 255,
                },
                google_oauth_scope: {
                    required: google_oauth_enabled,
                    minlength: 1,
                    maxlength: 255,
                },
                google_base_url: {
                    required: google_oauth_enabled,
                    minlength: 1,
                    maxlength: 255,
                    url: true,
                },
                google_oauth_metadata_url: {
                    required: google_oauth_auto_configure_enabled,
                    minlength: 1,
                    maxlength: 255,
                    url: true,
                },
                google_token_url: {
                    required: google_oauth_auto_configure_disabled,
                    minlength: 1,
                    maxlength: 255,
                    url: true,
                },
                google_authorize_url: {
                    required: google_oauth_auto_configure_disabled,
                    minlength: 1,
                    maxlength: 255,
                    url: true,
                },
                github_oauth_key: {
                    required: github_oauth_enabled,
                    minlength: 1,
                    maxlength: 255,
                },
                github_oauth_secret: {
                    required: github_oauth_enabled,
                    minlength: 1,
                    maxlength: 255,
                },
                github_oauth_scope: {
                    required: github_oauth_enabled,
                    minlength: 1,
                    maxlength: 255,
                },
                github_oauth_api_url: {
                    required: github_oauth_enabled,
                    minlength: 1,
                    maxlength: 255,
                    url: true,
                },
                github_oauth_metadata_url: {
                    required: github_oauth_auto_configure_enabled,
                    minlength: 1,
                    maxlength: 255,
                    url: true,
                },
                github_oauth_token_url: {
                    required: github_oauth_auto_configure_disabled,
                    minlength: 1,
                    maxlength: 255,
                    url: true,
                },
                github_oauth_authorize_url: {
                    required: github_oauth_auto_configure_disabled,
                    minlength: 1,
                    maxlength: 255,
                    url: true,
                },
                azure_oauth_key: {
                    required: azure_oauth_enabled,
                    minlength: 1,
                    maxlength: 255,
                    uuid: true,
                },
                azure_oauth_secret: {
                    required: azure_oauth_enabled,
                    minlength: 1,
                    maxlength: 255,
                },
                azure_oauth_scope: {
                    required: azure_oauth_enabled,
                    minlength: 1,
                    maxlength: 255,
                },
                azure_oauth_api_url: {
                    required: azure_oauth_enabled,
                    minlength: 1,
                    maxlength: 255,
                    url: true,
                },
                azure_oauth_metadata_url: {
                    required: azure_oauth_auto_configure_enabled,
                    minlength: 1,
                    maxlength: 255,
                    url: true,
                },
                azure_oauth_token_url: {
                    required: azure_oauth_auto_configure_disabled,
                    minlength: 1,
                    maxlength: 255,
                    url: true,
                },
                azure_oauth_authorize_url: {
                    required: azure_oauth_auto_configure_disabled,
                    minlength: 1,
                    maxlength: 255,
                    url: true,
                },
                azure_sg_enabled: azure_oauth_enabled,
                azure_admin_group: {
                    uuid: azure_gs_enabled,
                },
                azure_operator_group: {
                    uuid: azure_gs_enabled,
                },
                azure_user_group: {
                    uuid: azure_gs_enabled,
                },
                azure_group_accounts_enabled: azure_oauth_enabled,
                azure_group_accounts_name: {
                    required: azure_gas_enabled,
                    minlength: 1,
                    maxlength: 255,
                },
                azure_group_accounts_name_re: {
                    required: azure_gas_enabled,
                    minlength: 1,
                    maxlength: 255,
                },
                azure_group_accounts_description: {
                    required: azure_gas_enabled,
                    minlength: 1,
                    maxlength: 255,
                },
                azure_group_accounts_description_re: {
                    required: azure_gas_enabled,
                    minlength: 1,
                    maxlength: 255,
                },
                oidc_oauth_key: {
                    required: oidc_oauth_enabled,
                    minlength: 1,
                    maxlength: 255,
                },
                oidc_oauth_secret: {
                    required: oidc_oauth_enabled,
                    minlength: 1,
                    maxlength: 255,
                },
                oidc_oauth_scope: {
                    required: oidc_oauth_enabled,
                    minlength: 1,
                    maxlength: 255,
                },
                oidc_oauth_api_url: {
                    required: oidc_oauth_enabled,
                    minlength: 1,
                    maxlength: 255,
                    url: true,
                },
                oidc_oauth_metadata_url: {
                    required: oidc_oauth_auto_configure_enabled,
                    minlength: 1,
                    maxlength: 255,
                    url: true,
                },
                oidc_oauth_token_url: {
                    required: oidc_oauth_auto_configure_disabled,
                    minlength: 1,
                    maxlength: 255,
                    url: true,
                },
                oidc_oauth_authorize_url: {
                    required: oidc_oauth_auto_configure_disabled,
                    minlength: 1,
                    maxlength: 255,
                    url: true,
                },
                oidc_oauth_logout_url: {
                    required: oidc_oauth_enabled,
                    minlength: 1,
                    maxlength: 255,
                    url: true,
                },
                oidc_oauth_username: {
                    required: oidc_oauth_enabled,
                    minlength: 1,
                    maxlength: 255,
                },
                oidc_oauth_email: {
                    required: oidc_oauth_enabled,
                    minlength: 1,
                    maxlength: 255,
                },
                oidc_oauth_firstname: {
                    minlength: 0,
                    maxlength: 255,
                },
                oidc_oauth_last_name: {
                    minlength: 0,
                    maxlength: 255,
                },
                oidc_oauth_account_name_property: {
                    minlength: 0,
                    maxlength: 255,
                },
                oidc_oauth_account_description_property: {
                    minlength: 0,
                    maxlength: 255,
                },
            },
            messages: {
                ldap_sg_enabled: {
                    ldap_exclusive: 'The LDAP group security feature is mutually exclusive with the LDAP role auto-provisioning feature.',
                },
                autoprovisioning: {
                    ldap_exclusive: 'The LDAP role auto-provisioning feature is mutually exclusive with the LDAP group security feature.',
                },
            },
        });

        target.find('input, select, textarea, label').on('change,keyup,blur,click', onElementChanged);
        target.valid();
    }

    self.activateTab = function (tab) {
        $('[role="tablist"] a.nav-link').blur();

        if (!tab.includes('/')) {
            for (const index in self.tabs()) {
                let item = self.tabs()[index]();
                if (item.parent === tab && item.def) {
                    tab += '/' + item.id;
                }
            }
        }

        self.tab_active(tab);
        window.location.hash = tab;
    }

    self.activateSubTab = function (tab) {
        $('[role="tablist"] a.nav-link').blur();
        self.tab_sub_active(tab);
        window.location.hash = self.tab_active() + '/' + tab;
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

    self.observe = function (value) {
        if (typeof value === 'undefined') {
            return null;
        }

        if (value === null) {
            return null;
        }

        let result = value;

        if (value.constructor === Array) {
            result = [];
            for (const index in value) {
                result[index] = self.observe(value[index]);
            }
        } else if (value.constructor === Object) {
            result = {};
            for (const key in value) {
                if (value.hasOwnProperty(key))
                    result[key] = self.observe(value[key]);
            }
        }

        return ko.observable(result);
    }

    self.onDataLoaded = function (result) {
        let settings = result.payload;

        self.setupProperties(settings);
        self.setupKnockoutBindings();

        if (self.hasHash()) {
            self.activateTab(self.getHash());
        } else {
            self.activateDefaultTab();
        }

        self.setupListeners();
        self.setupValidation();

        self.settings(settings);
        self.messages(result.messages != null && result.messages.constructor === Array ? result.messages : []);
        self.messages_class(result.status === 0 ? 'danger' : 'info');
        self.loading(false);

        return true;
    }

    self.onDataSaved = function (result) {
        if (result.status === 0) {
            self.saved(false);
            self.save_failed(true);
            self.messages_class('danger');
            self.messages(result.messages);
            self.saving(false);
            return false;
        }

        self.updateProperties(result.data);
        self.saved(true);
        self.save_failed(false);
        self.messages_class('info');
        self.messages(result.messages);
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
        let el = $(event.target);

        if (!el.is('a')) {
            el = el.closest('a');
        }

        let tab = el.data('tab');
        let parent = el.data('tab-parent');
        let path = '';

        if (parent) {
            path = parent + '/';
        }

        path += tab;

        self.activateTab(path);
        return false;
    }

    self.onSubTabClick = function (model, event) {
        self.activateSubTab($(event.target).data('tab'));
        return false;
    }
}
