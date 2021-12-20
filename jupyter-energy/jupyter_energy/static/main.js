define([
    'jquery',
    'base/js/utils'
], function ($, utils) {

    let startMeasurements = {};
    let previousMeasurements = {};
    let previousTimestamp = 0;

    function _getMeasurements(callback) {
        $.getJSON({
            url: utils.get_body_data('baseUrl') + 'api/energy-metrics/v1',
            success: callback
        });
    }
    function initData() {
        _getMeasurements((measurements) => {
            startMeasurements = measurements;
            previousMeasurements = measurements;
            previousTimestamp = new Date().getTime();
        });
    }
    function fetchData(callback) {
        _getMeasurements((measurements) => {
            const now = new Date().getTime();
            const joulesByAll = measurements['joulesUsedByAll'] - (startMeasurements['joulesUsedByAll'] ?? 0);
            const joulesByCpu = measurements['joulesUsedByCpu'] - (startMeasurements['joulesUsedByCpu'] ?? 0);
            const joulesByRam = measurements['joulesUsedByRam'] - (startMeasurements['joulesUsedByRam'] ?? 0);
            const joulesByGpu = measurements['joulesUsedByGpu'] - (startMeasurements['joulesUsedByGpu'] ?? 0);
            const joulesUsedSinceLastMeasurement = measurements['joulesUsedByAll'] - previousMeasurements['joulesUsedByAll'];
            const secondsSinceLastMeasurement = (now - previousTimestamp) / 1000.0;
            const normalizedJoulesInLastSecond = secondsSinceLastMeasurement == 0 ? 0 : joulesUsedSinceLastMeasurement / secondsSinceLastMeasurement;

            previousMeasurements = measurements;
            previousTimestamp = now;
            callback({
                joulesUsedByAllSinceNotebookStart: joulesByAll,
                joulesUsedByCpuSinceNotebookStart: joulesByCpu,
                joulesUsedByRamSinceNotebookStart: joulesByRam,
                joulesUsedByGpuSinceNotebookStart: joulesByGpu,
                joulesUsedByAllInLastSecond: normalizedJoulesInLastSecond,
                comparisonAction: 'crack a pinata',
                comparisonEmoji: '🪅',
            });
        });
    }

    function setupDOM() {
        $('#maintoolbar-container').append(
            $('<div>').attr('id', 'jupyter-energy')
                .addClass('btn-group')
                .addClass('pull-right')
                .append($('<span>').text('Now: '))
                .append($('<strong>')
                    .text('0')
                    .attr('id', 'jupyter-energy-current')
                    .attr('title', 'Actively used energy per second')
                )
                .append($('<span>').text('Total: ').attr('style', 'padding-left: 1em;'))
                .append($('<strong>')
                    .text('0')
                    .attr('id', 'jupyter-energy-total')
                    .attr('title', 'Energy usage since this notebook started'))
                .append($('<span>').text('CPU: ').attr('style', 'padding-left: 1em;'))
                .append($('<strong>')
                    .text('0')
                    .attr('id', 'jupyter-energy-cpu')
                    .attr('title', 'CPU usage since this notebook started'))
                .append($('<span>').text('RAM: ').attr('style', 'padding-left: 1em;'))
                .append($('<strong>')
                    .text('0')
                    .attr('id', 'jupyter-energy-ram')
                    .attr('title', 'RAM usage since this notebook started'))
                .append($('<span>').text('GPU: ').attr('style', 'padding-left: 1em;'))
                .append($('<strong>')
                    .text('0')
                    .attr('id', 'jupyter-energy-gpu')
                    .attr('title', 'GPU usage since this notebook started'))
        );
        $('head').append($('<style>').html(
            '#jupyter-energy { padding: 2px 8px; } ' +
            '#jupyter-resource-usage-display { display: none; } ' +
            '.jupyter-energy-warn { background- color: #FFD2D2; color: #D8000C;}'
        ));
    }

    function humanEnergy(size) {
        const units = ['J', 'KiJ', 'MiJ', 'GiJ', 'TiJ'];
        let i = size == 0 ? 0 : Math.floor(Math.log(size) / Math.log(1024));
        if (i < 0) i = 0;
        if (i >= units.length) i = units.length - 1;
        return (size / Math.pow(1024, i)).toFixed(1) * 1 + ' ' + units[i];
    }

    function displayMetrics() {
        if (document.hidden) {
            // Don't poll when nobody is looking.
            return;
        }
        fetchData(function (data) {
            console.log(data);

            $('#jupyter-energy-current')
                .text(humanEnergy(data.joulesUsedByAllInLastSecond) + '/s')
                .attr('You are currently using ' + humanEnergy(data.joulesUsedByAllInLastSecond) + ' joules per second.');
            $('#jupyter-energy-total')
                .text(humanEnergy(data.joulesUsedByAllSinceNotebookStart) + ' 🪅')
                .attr(humanEnergy(data.joulesUsedByAllSinceNotebookStart) + ' joules are enough energy to crack open a pinata.');
            $('#jupyter-energy-cpu')
                .text(humanEnergy(data.joulesUsedByCpuSinceNotebookStart))
                .attr('Since this notebook started, your CPU consumed ' + humanEnergy(data.joulesUsedByCpuSinceNotebookStart));
            $('#jupyter-energy-ram')
                .text(humanEnergy(data.joulesUsedByRamSinceNotebookStart))
                .attr('Since this notebook started, your RAM consumed ' + humanEnergy(data.joulesUsedByRamSinceNotebookStart));
            $('#jupyter-energy-gpu')
                .text(humanEnergy(data.joulesUsedByGpuSinceNotebookStart))
                .attr('Since this notebook started, your GPU consumed ' + humanEnergy(data.joulesUsedByGpuSinceNotebookStart));

            // if (limits['memory']['warn']) {
            //     $('#jupyter-energy').addClass('jupyter-energy-warn');
            // } else {
            //     $('#jupyter-energy').removeClass('jupyter-energy-warn');
            // }
        });
    };

    return {
        load_ipython_extension: function () {
            initData();
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
