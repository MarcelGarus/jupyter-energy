define([
    'jquery',
    'base/js/namespace',
    'notebook/js/codecell',
    'base/js/utils',
    'nbextensions/jupyter_energy/charts'
], function ($, Jupyter, codecell, utils, charts) {
    function getJson(url) {
        return new Promise(resolve => {
            $.getJSON({ url: url, success: (response) => resolve(response) });
        });
    }

    async function getMetrics() {
        return await getJson(utils.get_body_data('baseUrl') + 'api/energy-metrics/v1');
    }

    function runCell(cell) {
        return new Promise(resolve => {
            function cellFinished() {
                cell.events.off('finished_execute.CodeCell', cellFinished);
                resolve();
            }
            cell.events.on('finished_execute.CodeCell', cellFinished);
            cell.execute();
        });
    }

    async function runBenchmark() {
        console.log('Running benchmark.');
        const results = [];

        const cell = Jupyter.notebook.get_selected_cell();
        if (!(cell instanceof codecell.CodeCell)) {
            alert('Select the cell to run for the benchmark first.');
            return;
        }

        console.log('Running cell to warm up.');
        await runCell(cell);

        // The intention of this benchmark is that one energy server is running
        // on the device to be tested (proxied by the jupyter server and
        // extension), while another energy server is running on the testing
        // device, connected via MCP.
        async function getLocalMetrics() {
            let response = await fetch("http://localhost:35396");
            return await response.json();
        }
        function diffMetrics(before, after) {
            const response = {};
            for (const source of Object.keys(before.usage)) {
                response[source] = after.usage[source].joules - before.usage[source].joules;
            }
            return response;
        }

        for (let i = 0; i < 10; i++) {
            console.log('Running the benchmarking cell. Run #' + i);
            const before = await Promise.all([getLocalMetrics(), getMetrics()]);
            await runCell(cell);
            const after = await Promise.all([getLocalMetrics(), getMetrics()]);

            console.log('Energy usage:');
            const externalDiff = diffMetrics(before[0], after[0]);
            const internalDiff = diffMetrics(before[1], after[1]);
            console.log('Measured internally: ' + JSON.stringify(internalDiff));
            console.log('Measured externally: ' + JSON.stringify(externalDiff));
            results.push({
                'internal': internalDiff,
                'external': externalDiff,
            });
        }

        console.log(JSON.stringify(results));
    }

    function setupDOM() {
        let menuOpened = false;
        function toggleMenu() {
            menuOpened = !menuOpened;
            document.getElementById('je-menu').style.visibility = menuOpened ? 'visible' : 'hidden';
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
                    .append($('<span>').text(' since you started the Jupyter server. This is enough energy to '))
                    .append($('<strong>').text('…').attr('id', 'je-menu-comparison-text'))
                    .append($('<span>').text('.')))
                .append($('<div>')
                    .addClass('je-menu-section')
                    .append($('<canvas>').attr('id', 'je-menu-chart')))
                .append($('<div>')
                    .addClass('je-menu-section')
                    .append($('<button>')
                        .addClass('btn').addClass('btn-default')
                        .text('Switch units between J and Wh')
                        .click((_) => toggleUnit()))
                    .append($('<button>')
                        .addClass('btn').addClass('btn-default')
                        .text('Start benchmark')
                        .click((_) => runBenchmark())))
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

    let useWatt = false;
    let chart = undefined;

    function toggleUnit() {
        useWatt = !useWatt;
        displayMetrics();
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
        throw 'Shouldn\'t be reached. Joules: ' + joules;
    }

    async function displayMetrics() {
        if (document.hidden) {
            // Don't poll when nobody is looking.
            return;
        }
        const metrics = await getMetrics();
        console.debug(metrics);
        const comparison = comparisonForJoules(metrics.usage.all.joules);

        $('#je-toolbar-metric-current').text(humanPower(metrics.usage.all.watts));
        $('#je-toolbar-metric-total').text(humanEnergy(metrics.usage.all.joules));
        $('#je-toolbar-comparison-emoji').text(comparison.emoji);

        $('#je-menu-metric-total').text(humanEnergy(metrics.usage.all.joules));
        $('#je-menu-comparison-text').text(comparison.text);
        $('#je-menu-comparison-emoji').text(comparison.emoji);

        const timelineLength = Object.values(metrics.usage)[0].wattsOverTime.length;
        const labels = Array(timelineLength).fill().map((_, index) => '-' + (timelineLength - index) + 's');
        const colors = ['#BD74E7', '#264653', '#2A9D8F', '#E9C46A', '#F4A261', '#E76F51'];

        const data = { labels: labels, datasets: [] };
        for (const source of Object.values(metrics.usage)) {
            // console.log('Source: ' + source);
            const color = colors.pop();
            data.datasets.push({
                label: source.name + ' (' + humanEnergy(source.joules) + ')',
                backgroundColor: color,
                borderColor: color,
                data: source.wattsOverTime,
                radius: 0,
            });
        }
        if (chart == undefined) {
            chart = new charts.Chart(document.getElementById('je-menu-chart'), {
                type: 'line',
                data: data,
                options: {
                    animation: { duration: 0 },
                    scales: {
                        y: { min: 0 }
                    }
                },
            });
        } else {
            chart.data = data;
            chart.update();
        }
    };

    return {
        load_ipython_extension: async function () {
            setupDOM();
            await displayMetrics();
            setInterval(displayMetrics, 1000);

            document.addEventListener("visibilitychange", async function () {
                // Update instantly when user activates notebook tab.
                // FIXME: Turn off update timer completely when tab not in focus.
                await displayMetrics();
            }, false);
        },
    };
});
