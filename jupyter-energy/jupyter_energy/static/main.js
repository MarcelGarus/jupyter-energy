define([
    'jquery',
    'base/js/utils'
], function ($, utils) {
    function setupDOM() {
        $('#maintoolbar-container').append(
            $('<div>').attr('id', 'jupyter-energy')
                .addClass('btn-group')
                .addClass('pull-right')
                // .append($('<span>').text('Now: '))
                // .append($('<strong>')
                //     .attr('id', 'jupyter-energy-current')
                //     .attr('title', 'Actively used energy per second')
                // )
                .append($('<span>').text('Total: ').attr('style', 'padding-left: 1em;'))
                .append($('<strong>')
                    .attr('id', 'jupyter-energy-total')
                    .attr('title', 'Energy usage since this notebook started'))
        );
        $('head').append(
            $('<style>').html('.jupyter-energy-warn { background-color: #FFD2D2; color: #D8000C; }')
        );
        $('head').append(
            $('<style>').html('#jupyter-energy { padding: 2px 8px; }')
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
            url: utils.get_body_data('baseUrl') + 'api/energy-metrics/v1',
            success: function (data) {
                console.log(data);
                let joulesPerSecond = data['joulesPerSecond'];
                let joulesSinceStart = data['joulesSinceStart'];

                $('#jupyter-energy-current')
                    .text(joulesPerSecond + ' J/s')
                    .attr('You are currently using ' + joulesPerSecond + ' joules per second.');
                $('#jupyter-energy-total')
                    .text(joulesSinceStart + ' J 🪅')
                    .attr(joulesSinceStart + ' joules are enough energy to crack open a pinata.');

                // totalMemoryUsage = humanFileSize(data['rss']);

                // var limits = data['limits'];
                // var display = totalMemoryUsage;

                // if (limits['memory']) {
                //     if (limits['memory']['rss']) {
                //         maxMemoryUsage = humanFileSize(limits['memory']['rss']);
                //         display += " / " + maxMemoryUsage
                //     }
                //     if (limits['memory']['warn']) {
                //         $('#jupyter-energy').addClass('jupyter-energy-warn');
                //     } else {
                //         $('#jupyter-energy').removeClass('jupyter-energy-warn');
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
