document.addEventListener('DOMContentLoaded', function () {
    'use strict';

    var form = document.getElementById('dashboard-zone-delete-form');
    if (!form) {
        return;
    }
    var modal = document.getElementById('modal_dashboard_zone_delete');
    var name = document.getElementById('dashboard-zone-delete-name');
    var displayName = document.getElementById('dashboard-zone-delete-display-name');
    var error = document.getElementById('dashboard-zone-delete-error');
    var submit = document.getElementById('dashboard-zone-delete-submit');
    var pending = false;

    // Delegation also handles rows loaded or replaced by either dashboard.
    document.addEventListener('click', function (event) {
        var button = event.target.closest('.dashboard-remove-zone');
        if (!button || pending) {
            return;
        }
        event.preventDefault();
        name.value = button.dataset.domain;
        displayName.textContent = button.dataset.displayName || button.dataset.domain;
        error.classList.add('d-none');
        showModal(modal);
    });

    form.addEventListener('submit', function (event) {
        event.preventDefault();
        if (pending || !name.value) {
            return;
        }
        pending = true;
        submit.disabled = true;
        error.classList.add('d-none');
        $.ajax({
            url: form.action,
            method: 'POST',
            data: $(form).serialize(),
            dataType: 'json'
        }).done(function () {
            window.location.reload();
        }).fail(function (xhr) {
            error.textContent = xhr.status === 403
                ? 'You do not have permission to remove this zone.'
                : 'The zone could not be removed. Please try again.';
            error.classList.remove('d-none');
            showModal(modal);
        }).always(function () {
            pending = false;
            submit.disabled = false;
        });
    });
});
