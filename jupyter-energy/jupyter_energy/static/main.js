define([
    'jquery',
    'base/js/utils'
], function ($, utils) {
    function setupDOM() {
        $('#maintoolbar-container').append(
            $('<div>').attr('id', 'jupyter-energy-display')
                .addClass('btn-group')
                .addClass('pull-right')
                .append(
                    $('<strong>').text('Energy: ')
                ).append(
                    $('<span>').attr('id', 'jupyter-energy-current')
                        .attr('title', 'Actively used energy (updates every second)')
                )
        );
        // FIXME: Do something cleaner to get styles in here?
        $('head').append(
            $('<style>').html('.jupyter-energy-warn { background-color: #FFD2D2; color: #D8000C; }')
        );
        $('head').append(
            $('<style>').html('#jupyter-energy-display { padding: 2px 8px; }')
        );
    }

    function humanFileSize(size) {
        var i = Math.floor(Math.log(size) / Math.log(1024));
        return (size / Math.pow(1024, i)).toFixed(1) * 1 + ' ' + ['B', 'kB', 'MB', 'GB', 'TB'][i];
    }

    var displayMetrics = function () {
        if (document.hidden) {
            // Don't poll when nobody is looking
            return;
        }
        $.getJSON({
            url: utils.get_body_data('baseUrl') + 'api/metrics/v1',
            success: function (data) {
                console.log(data);
                let joulesPerSecond = data['joulesPerSecond'];
                $('#jupyter-energy-current').text(joulesPerSecond + " joules");

                // totalMemoryUsage = humanFileSize(data['rss']);

                // var limits = data['limits'];
                // var display = totalMemoryUsage;

                // if (limits['memory']) {
                //     if (limits['memory']['rss']) {
                //         maxMemoryUsage = humanFileSize(limits['memory']['rss']);
                //         display += " / " + maxMemoryUsage
                //     }
                //     if (limits['memory']['warn']) {
                //         $('#jupyter-energy-display').addClass('jupyter-energy-warn');
                //     } else {
                //         $('#jupyter-energy-display').removeClass('jupyter-energy-warn');
                //     }
                // }

                // $('#jupyter-energy-current').text(display);
            }
        });
    };

    return {
        load_ipython_extension: function () {
            setupDOM();
            displayMetrics();
            setInterval(displayMetrics, 1000);

            document.addEventListener("visibilitychange", function () {
                // Update instantly when user activates notebook tab.
                // FIXME: Turn off update timer completely when tab not in focus.
                displayMetrics();
            }, false);
        },
    };
});
