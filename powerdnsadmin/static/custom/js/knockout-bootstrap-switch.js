ko.bindingHandlers.bootstrapSwitch = {
    init: function (element, valueAccessor, allBindings, viewModel, bindingContext) {
        let el = $(element);
        let disabled = allBindings.get('inputDisabled') || false;

        let profiles = {
            'enabled': {
                handleWidth: el.data('handle-width') || 55,
                offColor: el.data('off-color') || 'secondary',
                offText: el.data('off-text') || 'Disabled',
                onColor: el.data('on-color') || 'primary',
                onText: el.data('on-text') || 'Enabled',
                state: ko.unwrap(valueAccessor()),
                size: 'mini',
            },
            'enabled-danger-off': {
                handleWidth: el.data('handle-width') || 55,
                offColor: el.data('off-color') || 'danger',
                offText: el.data('off-text') || 'Disabled',
                onColor: el.data('on-color') || 'success',
                onText: el.data('on-text') || 'Enabled',
                state: ko.unwrap(valueAccessor()),
                size: 'mini',
            },
            'enabled-danger-on': {
                handleWidth: el.data('handle-width') || 55,
                offColor: el.data('off-color') || 'success',
                offText: el.data('off-text') || 'Disabled',
                onColor: el.data('on-color') || 'danger',
                onText: el.data('on-text') || 'Enabled',
                state: ko.unwrap(valueAccessor()),
                size: 'mini',
            },
            'enabled-warning-off': {
                handleWidth: el.data('handle-width') || 55,
                offColor: el.data('off-color') || 'warning',
                offText: el.data('off-text') || 'Disabled',
                onColor: el.data('on-color') || 'success',
                onText: el.data('on-text') || 'Enabled',
                state: ko.unwrap(valueAccessor()),
                size: 'mini',
            },
            'enabled-warning-on': {
                handleWidth: el.data('handle-width') || 55,
                offColor: el.data('off-color') || 'success',
                offText: el.data('off-text') || 'Disabled',
                onColor: el.data('on-color') || 'warning',
                onText: el.data('on-text') || 'Enabled',
                state: ko.unwrap(valueAccessor()),
                size: 'mini',
            },
        }

        let profile = el.data('profile');

        if (typeof profile === 'string' && profile.length > 0 && !profiles[profile]) {
            console.error('Unknown profile: ' + profile);
            return;
        }

        el.bootstrapSwitch(profiles[profile] || profiles['enabled']);
        el.bootstrapSwitch('disabled', disabled);

        el.on('switchChange.bootstrapSwitch', function (event, state) {
            valueAccessor()(state);
        });
    },
    update: function (element, valueAccessor, allBindings, viewModel, bindingContext) {
        let el = $(element);
        let disabled = allBindings.get('inputDisabled') || false;
        el.bootstrapSwitch('state', ko.unwrap(valueAccessor()));
        el.bootstrapSwitch('disabled', disabled);
    }
};