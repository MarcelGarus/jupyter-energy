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
            const normalizedJoulesInLastSecond = secondsSinceLastMeasurement == 0 ?
                0 : joulesUsedSinceLastMeasurement / secondsSinceLastMeasurement;

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

    function resetValues() {
        initData();
        displayMetrics();
    }

    let useWatt = false;

    function toggleUnit() {
        useWatt = !useWatt;
        displayMetrics();
    }

    function setupDOM() {
        let menuOpened = false;
        function openMenu() {
            document.getElementById('je-menu').style.visibility = 'visible';
            menuOpened = true;
        }
        function closeMenu() {
            document.getElementById('je-menu').style.visibility = 'hidden';
            menuOpened = false;
        }
        function toggleMenu() {
            if (menuOpened) {
                closeMenu();
            } else {
                openMenu();
            }
        }
        // We use je as a prefix for jupyter-energy related stuff.
        $('#maintoolbar-container').append(
            $('<button>').attr('id', 'je-toolbar')
                .click((_) => toggleMenu())
                .addClass('btn-group')
                .addClass('btn')
                .addClass('btn-default')
                .addClass('pull-right')
                .append($('<span>').text('Now: '))
                .append($('<strong>').text('…').attr('id', 'je-toolbar-metric-current'))
                .append($('<span>').text('Total: ').attr('style', 'padding-left: 1em;'))
                .append($('<strong>').text('…').attr('id', 'je-toolbar-metric-total'))
                .append($('<span>').text(' '))
                .append($('<span>').text('…').attr('id', 'je-toolbar-comparison-emoji'))
        );
        $('#maintoolbar-container').append(
            $('<div>').attr('id', 'je-menu')
                .append($('<div>')
                    .addClass('je-menu-section')
                    .attr('style', 'min-height: 3em;')
                    .append($('<div>').attr('id', 'je-menu-comparison-emoji'))
                    .append($('<span>').text('Your computer used '))
                    .append($('<strong>').text('…').attr('id', 'je-menu-metric-total'))
                    .append($('<span>').text(' since you opened this notebook. This is enough energy to '))
                    .append($('<strong>').text('…').attr('id', 'je-menu-comparison-text'))
                    .append($('<span>').text('.')))
                .append($('<div>')
                    .addClass('je-menu-section')
                    .append($('<span>').text('Total: '))
                    .append($('<strong>').text('…').attr('id', 'je-menu-metric-total-2'))
                    .append($('<span>').text('CPU: ').attr('style', 'padding-left: 1em;'))
                    .append($('<strong>').text('…').attr('id', 'je-menu-metric-cpu'))
                    .append($('<span>').text('RAM: ').attr('style', 'padding-left: 1em;'))
                    .append($('<strong>').text('…').attr('id', 'je-menu-metric-ram'))
                    .append($('<span>').text('GPU: ').attr('style', 'padding-left: 1em;'))
                    .append($('<strong>').text('…').attr('id', 'je-menu-metric-gpu')))
                .append($('<div>').addClass('je-menu-section').text('[TODO: Graph]'))
                .append($('<div>')
                    .addClass('je-menu-section')
                    .append($('<button>')
                        .addClass('btn').addClass('btn-default')
                        .text('Switch units between J and Wh')
                        .click((_) => toggleUnit()))
                    .append($('<button>')
                        .addClass('btn').addClass('btn-default')
                        .attr('style', 'margin-left: 1em;')
                        .text('Reset values')
                        .click((_) => resetValues())))
                .append($('<div>')
                    .addClass('je-menu-section')
                    .addClass('je-menu-footer')
                    .text("The values also contain workload from other programs because there is " +
                        "no reliable way for the operating system to attribute the energy usage " +
                        "of PC components with the running processes."))
        );
        $('head').append($('<style>').html(`
            #je-menu {
                visibility: hidden; /* This will be changed by JS. */
                position: absolute;
                top: 4em;
                right: 0;
                display: inline-block;
                max-width: 30em;
                padding: 1em;
                border-radius: 1em;
                background: white;
                box-shadow: 0 0 4em rgba(0,0,0,0.2);
            }
            .je-menu-section {
                margin-bottom: 1em;
            }
            #je-menu-comparison-emoji {
                float: right;
                font-size: 3em;
                margin-left: 0.5em;
            }
            .je-menu-footer {
                margin-bottom: 0;
                font-size: 0.8em;
                opacity: 0.6;
            }
            #jupyter-resource-usage-display { display: none; }
        `));
    }

    function humanSiPrefixed(size) {
        const smallPrefixes = ['', 'm', 'μ', 'n'];
        const bigPrefixes = ['', 'K', 'M', 'G', 'T', 'P'];
        let i = size == 0 ? 0 : Math.floor(Math.log(size) / Math.log(1000));
        const prefix = (i >= 0) ? bigPrefixes[Math.min(i, bigPrefixes.length - 1)]
            : smallPrefixes[Math.min(-i, smallPrefixes.length - 1)];
        return (size / Math.pow(1000, i)).toFixed(1) + ' ' + prefix;
    }
    function humanEnergy(joules) {
        if (useWatt) {
            return humanSiPrefixed(joules / 3600.0) + 'Wh';
        } else {
            return humanSiPrefixed(joules) + 'J';
        }
    }
    function humanPower(joulesPerSecond) {
        return humanSiPrefixed(joulesPerSecond) + 'W';
    }

    function comparisonForJoules(joules) {
        const comparisons = [
            { joules: 0, emoji: '🕸️', text: 'do nothing interesting' },
            { joules: 6, emoji: '💡', text: 'power a modern lamp for one second' },
            { joules: 12, emoji: '💡', text: 'power a modern lamp for two seconds' },
            { joules: 18, emoji: '💡', text: 'power a modern lamp for three seconds' },
            { joules: 24, emoji: '💡', text: 'power a modern lamp for four seconds' },
            { joules: 30, emoji: '💡', text: 'power a modern lamp for five seconds' },
            { joules: 36, emoji: '💡', text: 'power a modern lamp for six seconds' },
            { joules: 42, emoji: '💡', text: 'power a modern lamp for seven seconds' },
            { joules: 48, emoji: '💡', text: 'power a modern lamp for eight seconds' },
            { joules: 54, emoji: '💡', text: 'power a modern lamp for nine seconds' },
            { joules: 60, emoji: '🎧', text: 'play a one-minute MP3 song' },
            { joules: 120, emoji: '🎧', text: 'play a two-minute MP3 song' },
            { joules: 180, emoji: '🎧', text: 'play a three-minute MP3 song' },
            { joules: 240, emoji: '🎧', text: 'play a four-minute MP3 song' },
            { joules: 300, emoji: '🎧', text: 'play a five-minute MP3 song' },
            { joules: 360, emoji: '🎧', text: 'play a six-minute MP3 song' },
            { joules: 420, emoji: '🎧', text: 'play a seven-minute MP3 song' },
            { joules: 448, emoji: '🪅', text: 'crack a piñata' },
            { joules: 856, emoji: '🎬', text: 'run a movie-grade LED panel for a minute on full brightness' },
            { joules: 1250, emoji: '🎹', text: 'play a four-minute song on an electric keyboard' },
            { joules: 2500, emoji: '🎹', text: 'play an eight-minute song on an electric keyboard' },
            // { joules: 29000, emoji: '📱', text: 'charge a phone' },
            { joules: 64337, emoji: '🐮', text: 'make a hot cup of milk in a milk frother' },
            { joules: 100000, emoji: '🍞', text: 'toast a toast' },
            { joules: 150000, emoji: '🫖', text: 'brew a cup of tea' },
            // { joules: 150000, emoji: '🫖', text: 'brew a cup of coffee' },
            // { joules: 108000, emoji: '📺', text: 'run a TV for 1 hour' },
            // { joules: 110000, emoji: '🎢', text: 'ride a roller coaster' },
            // { joules: 180000, emoji: '💻', text: 'run a laptop for 1 hour' },
            // { joules: 360000, emoji: '🎮', text: 'play video games for 1 hour' },
            { joules: 1250000, emoji: '🧱', text: 'break through a brick' },
            { joules: 3400000, emoji: '🍕', text: 'bake a pizza' },
            { joules: 5400000, emoji: '🎂', text: 'bake a cake' },
            { joules: 10800000, emoji: '🍪', text: 'bake cookies' },
            { joules: 248000000, emoji: '🏠', text: 'power an average house for 1 day' },
            { joules: 14000000000000000000000000000000, emoji: '🌅', text: 'run the sun for 1 hour' }
        ];
        for (const i in comparisons) {
            const comparison = comparisons[comparisons.length - i - 1];
            if (comparison.joules <= joules) {
                return comparison;
            }
        }
        throw 'Shouldn\'t be reached.';
    }

    function displayMetrics() {
        if (document.hidden) {
            // Don't poll when nobody is looking.
            return;
        }
        fetchData(function (data) {
            console.log(data);
            const comparison = comparisonForJoules(data.joulesUsedByAllSinceNotebookStart);

            $('#je-toolbar-metric-current').text(humanPower(data.joulesUsedByAllInLastSecond));
            $('#je-toolbar-metric-total').text(humanEnergy(data.joulesUsedByAllSinceNotebookStart));
            $('#je-toolbar-comparison-emoji').text(comparison.emoji);

            $('#je-menu-metric-total').text(humanEnergy(data.joulesUsedByAllSinceNotebookStart));
            $('#je-menu-comparison-text').text(comparison.text);
            $('#je-menu-comparison-emoji').text(comparison.emoji);
            $('#je-menu-metric-total-2').text(humanEnergy(data.joulesUsedByAllSinceNotebookStart));
            $('#je-menu-metric-cpu').text(humanEnergy(data.joulesUsedByCpuSinceNotebookStart));
            $('#je-menu-metric-ram').text(humanEnergy(data.joulesUsedByRamSinceNotebookStart));
            $('#je-menu-metric-gpu').text(humanEnergy(data.joulesUsedByGpuSinceNotebookStart));
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
