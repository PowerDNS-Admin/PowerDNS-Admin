(function () {
    'use strict';
    const field = document.getElementById('zone-content');
    document.getElementById('copy-zone').addEventListener('click', async function () {
        try {
            if (window.isSecureContext && navigator.clipboard) {
                await navigator.clipboard.writeText(field.value);
            } else {
                field.focus();
                field.select();
                if (!document.execCommand('copy')) {
                    throw new Error('Clipboard access unavailable');
                }
            }
            bootstrap.Toast.getOrCreateInstance(
                document.getElementById('copy-toast'), {delay: 5000}
            ).show();
        } catch (error) {
            showErrorModal('Copy failed. Select the zone text and copy it manually.');
        }
    });
    document.getElementById('download-zone').addEventListener('click', function () {
        const url = URL.createObjectURL(new Blob([field.value], {type: 'text/plain;charset=utf-8'}));
        const link = document.createElement('a');
        link.href = url;
        link.download = this.dataset.filename;
        link.click();
        setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    });
}());
