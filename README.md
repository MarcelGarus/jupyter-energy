# Jupyter Energy

Jupyter Notebooks are a data science tool primarily used for statistics and machine learning, some of the most energy-intensive computing areas.
To make users of Jupyter Notebooks more aware of their notebooks' energy consumption, this project aims to offer a Jupyter Notebook plugin that informs you of the energy use since the notebook started.

Here's a quick overview of the repo folders:

## rust-energy

This folder contains a Rust program that shows you your current and cumulative energy use, along with some comparisons:

```text
Current energy use: 7.48 joules.
Since program start: 457.2 joules.
With this energy, you could crack a piñata. 🪅
```

To get data about energy consumption, the program just calls `perf` and parses the output.

## python-energy

This folder contains Python code that interacts with C code via FFI to directly perform syscalls to get the energy usage from the OS.

On a system with Intel CPUs, there are several interesting files in `/sys/bus/event_source/devices/power/events`:

- `<event>`: contains a hex value like `event=0x02`
- `<event>.scale`: contains a small number like `2.3431267432e-10`
- `<event>.unit`: contains a unit like `Joules`

The C code in `measure.c` calls the `perf_event_open` syscall with the event's hex value to request listening to energy events from the OS.
This syscall returns a file that you can read the cumulative amount of ticks since the measurement started.
It then calculates the actual energy use by subtracting the initial ticks, multiplying the difference with the scale, and using the unit.

There are two ways to use the C file:

- Run it as a standalone program: `gcc measure.c -o measure && sudo ./measure`
- Compile it into a shared library: `gcc --shared measure.c -o measure.so`

The python file `measure.py` is a wrapper that communicates with the precompiled shared library using FFI.
Again, there are two ways to use the Python file:

- Run it as a standalone program: `python3 measure.py`.  
  It will then start a webserver on `http://localhost:35396` that reports the cumulative energy use since the server start as JSON.
- Include it as a library. Then, you can use it like this:
  ```python
  ongoing_recording = record_energy("energy-pkg")
  sleep(1)
  ongoing_recording.used_joules()
  ```

## jupyter-energy

This folder contains an extension for Jupyter Notebooks.

### How to use

1. Create an environment that will hold our dependencies:
  ```bash
  conda create -n jupyter-energy -c conda-forge python
  ```
2. Activate the virtual environment that pipenv created for us
  ```bash
  conda activate jupyter-energy
  ```
3. Do a dev install of jupyter-energy and its dependencies
  ```bash
  pip install --editable .[dev]
  ```
4. Enable the server extension:
  ```bash
  jupyter serverextension enable --py jupyter_energy --sys-prefix
  ```
  *Note: if you're using Jupyter Server:*
  ```bash
  jupyter server extension enable --py jupyter_energy --sys-prefix
  ```
5. Install and enable the nbextension for use with Jupyter Classic Notebook.
  ```bash
  jupyter nbextension install --py jupyter_energy --symlink --sys-prefix
  jupyter nbextension enable --py jupyter_energy --sys-prefix
  ```
6. Start a Jupyter Notebook instance, open a new notebook and check out the memory usage in the top right!
  ```bash
  jupyter notebook
  ```
