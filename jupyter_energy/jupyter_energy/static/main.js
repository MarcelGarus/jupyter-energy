define([
    'jquery',
    'base/js/namespace',
    'base/js/events',
    'base/js/utils',
    'notebook/js/codecell',
    'nbextensions/jupyter_energy/charts'
], function ($, Jupyter, events, utils, codecell, charts) {
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
                'time': {
                    'wall': after[1].time.wall - before[1].time.wall,
                    'user': after[1].time.user - before[1].time.user,
                },
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
                    .addClass('je-time-frame-buttons')
                    .addClass('btn-group')
                    .append($('<button>')
                        .attr('id', 'je-btn-short-term').addClass('btn').addClass('btn-default').addClass('je-time-frame-active-button')
                        .text('Last 100 seconds')
                        .click((_) => showLongTerm ? toggleTimeFrame() : null))
                    .append($('<button>')
                        .attr('id', 'je-btn-long-term').addClass('btn').addClass('btn-default')
                        .text('Since server start')
                        .click((_) => showLongTerm ? null : toggleTimeFrame())))
                .append($('<div>')
                    .addClass('je-menu-section')
                    .append($('<canvas>').attr('id', 'je-menu-chart')))
                .append($('<div>')
                    .addClass('je-menu-section')
                    .append($('<button>')
                        .addClass('btn').addClass('btn-default').attr('style', 'margin-right: 1em;')
                        .text('Switch units between J and Wh')
                        .click((_) => toggleUnit()))
                    .append($('<button>')
                        .addClass('btn').addClass('btn-default')
                        .text('Start benchmark')
                        .click((_) => runBenchmark())))
                .append($('<div>')
                    .addClass('je-menu-section')
                    .addClass('je-menu-footer')
                    .html("Energy usage numbers also contain workload from other programs on the " +
                        "Juypter server because there's no reliable way to directly attribute " +
                        "the energy usage of PC components with the running processes.<br>" +
                        "Information about energy generation comes from the European Network of " +
                        "Transmission System Operators for Electricity."))
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
            .je-time-frame-buttons {
                display: flex;
                justify-content: center;
            }
            .je-time-frame-active-button {
                color: #333;
                background-color: #e6e6e6;
                background-image: none;
                border-color: #adadad;
                box-shadow: inset 0 3px 5px rgba(0, 0, 0, 0.125);
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
    let showLongTerm = false;
    let chart = undefined;

    function toggleUnit() {
        useWatt = !useWatt;
        displayMetrics();
    }

    function humanSiPrefixed(size) {
        const smallPrefixes = ['', 'm', 'μ', 'n'];
        const bigPrefixes = ['', 'k', 'M', 'G', 'T', 'P'];
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

    function toggleTimeFrame() {
        showLongTerm = !showLongTerm;

        if (showLongTerm) {
            document.getElementById('je-btn-short-term').classList.remove('je-time-frame-active-button');
            document.getElementById('je-btn-long-term').classList.add('je-time-frame-active-button');
        } else {
            document.getElementById('je-btn-short-term').classList.add('je-time-frame-active-button');
            document.getElementById('je-btn-long-term').classList.remove('je-time-frame-active-button');
        }

        if (chart instanceof charts.Chart) {
            console.log("Destroying chart.");
            chart.destroy();
        }
        chart = undefined;

        displayMetrics();
    }

    let isRunning = false;
    let runningHistory = Array(100).fill(false);

    async function tickRunning() {
        runningHistory.push(isRunning);
        if (runningHistory.length > 100) {
            runningHistory.shift();
        }
    }

    async function displayMetrics() {
        console.log("Displaying metrics");
        const metrics = await getMetrics();
        console.debug(metrics);
        const comparison = comparisonForJoules(metrics.usage.all.joules);

        $('#je-toolbar-metric-current').text(humanPower(metrics.usage.all.watts));
        $('#je-toolbar-metric-total').text(humanEnergy(metrics.usage.all.joules));
        $('#je-toolbar-comparison-emoji').text(comparison.emoji);

        $('#je-menu-metric-total').text(humanEnergy(metrics.usage.all.joules));
        $('#je-menu-comparison-text').text(comparison.text);
        $('#je-menu-comparison-emoji').text(comparison.emoji);

        if (showLongTerm) {
            displayLongTermChart(metrics);
        } else {
            displayShortTermChart(metrics);
        }
    }

    function displayShortTermChart(metrics) {
        const timelineLength = Object.values(metrics.usage)[0].wattsOverTime.length;
        const labels = Array(timelineLength).fill().map((_, index) => '-' + (timelineLength - index) + 's');
        const colors = ['#BD74E7', '#264653', '#2A9D8F', '#E9C46A', '#F4A261', '#E76F51'];

        const data = { labels: labels, datasets: [] };
        let max = 0;
        for (const source of Object.values(metrics.usage)) {
            const color = colors.pop();
            data.datasets.push({
                label: source.name + ' (' + humanEnergy(source.joules) + ')',
                backgroundColor: color,
                borderColor: color,
                data: source.wattsOverTime,
                radius: 0,
            });
            const sourceMax = source.wattsOverTime.reduce((a, b) => a > b ? a : b);
            if (sourceMax > max) max = sourceMax;
        }
        max = Math.round((max * 1.2) / 10) * 10;
        data.datasets.push({
            label: 'This notebook is running code',
            backgroundColor: 'rgba(0,200,0,0.3)',
            borderColor: 'transparent',
            fill: true,
            stepped: true,
            data: runningHistory.map((it) => it ? max : 0),
            radius: 0,
        });
        console.log('Running history: ' + runningHistory);

        if (chart == undefined) {
            chart = new charts.Chart(document.getElementById('je-menu-chart'), {
                type: 'line',
                data: data,
                options: {
                    animation: { duration: 0 },
                    scales: { y: { min: 0, max: max } }
                },
            });
        } else {
            chart.data = data;
            chart.update();
        }
    }

    function displayLongTermChart(metrics) {
        const timelineLength = metrics.usage.all.longTermJoules.length;
        const labels = Array(timelineLength).fill().map((_, index) => {
            const totalMinutes = (timelineLength - index - 1) * 15;
            const hours = Math.floor(totalMinutes / 60);
            const minutes = (totalMinutes % 60);
            return '-' + hours + ':' + (minutes.toString().length < 2 ? ('0' + minutes) : minutes) + 'h';
        });

        const data = { labels: labels, datasets: [] };
        let max = Object.values(metrics.usage)
            .map((it) => it.longTermJoules.reduce((a, b) => a > b ? a : b))
            .reduce((a, b) => a > b ? a : b);
        max = Math.round((max * 1.2) / 10) * 10;

        const colors = ['#BD74E7', '#264653', '#2A9D8F', '#E9C46A', '#F4A261', '#E76F51'];
        for (const source of Object.values(metrics.usage)) {
            const color = colors.pop();
            data.datasets.push({
                label: source.name + ' (' + humanEnergy(source.joules) + ')',
                backgroundColor: color,
                borderColor: color,
                data: source.longTermJoules,
                radius: 0,
            });
        }

        const generationSources = ['renewable', 'nonRenewable', 'storage', 'unknown'];
        const generationStacked = {};
        for (const source of generationSources) {
            const index = generationSources.indexOf(source);
            const previousSource = index == 0 ? null : generationSources[index - 1];
            generationStacked[source] = [];
            for (let i = 0; i < timelineLength; i++) {
                const previous = previousSource == null ? 0 : generationStacked[previousSource][i];
                generationStacked[source].push(previous + metrics.generation[source][i]);
            }
        }
        for (const source of generationSources) {
            for (let i = 0; i < timelineLength; i++) {
                generationStacked[source][i] *= max / generationStacked[generationSources[generationSources.length - 1]][i];
            }
        }

        const generationColors = {
            'renewable': '#DCEAB0',
            'nonRenewable': '#FDC6C6',
            'storage': '#ffff44',
            'unknown': '#444444',
        };
        const generationLabels = {
            'renewable': 'renewable',
            'nonRenewable': 'non-renewable',
            'storage': 'from storage',
            'unknown': 'unknown',
        };
        for (const source of generationSources) {
            data.datasets.push({
                label: generationLabels[source],
                backgroundColor: generationColors[source],
                borderColor: 'white',
                fill: true,
                data: generationStacked[source],
                radius: 0,
                borderWidth: 0,
            });
        }

        console.log(data);
        console.log(max);
        if (chart == undefined) {
            chart = new charts.Chart(document.getElementById('je-menu-chart'), {
                type: 'line',
                data: data,
                options: {
                    animation: { duration: 0 },
                    scales: { y: { min: 0, max: max } }
                },
            });
        } else {
            chart.data = data;
            chart.update();
        }
    }

    return {
        load_ipython_extension: async function () {
            setupDOM();

            // Call `displayMetrics` every second, but only if the tab is in the
            // foreground.
            await displayMetrics();
            setInterval(() => {
                if (document.hidden) return; // Don't poll when nobody is looking.
                displayMetrics();
            }, 1000);
            document.addEventListener("visibilitychange", async function () {
                // Update instantly when user activates notebook tab.
                await displayMetrics();
            }, false);

            // We record when the notebook was running vs. when it wasn't.
            setInterval(tickRunning, 1000);
            events.on('execute.CodeCell', (_, data) => {
                isRunning = true;
                const cell = data.cell;
                function cellFinished() {
                    cell.events.off('finished_execute.CodeCell', cellFinished);
                    isRunning = false;
                }
                cell.events.on('finished_execute.CodeCell', cellFinished);
            });
        },
    };
});
