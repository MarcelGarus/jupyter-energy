import os

import setuptools
from jupyter_packaging import (combine_commands, create_cmdclass,
                               ensure_targets, install_npm, skip_if_exists)

# The directory containing this file
HERE = os.path.abspath(os.path.dirname(__file__))

# The name of the project
NAME = "jupyter-energy"
PACKAGE_NAME = NAME.replace("-", "_")

src_path = os.path.join(HERE, "packages", "labextension")
lab_path = os.path.join(HERE, PACKAGE_NAME, "labextension")
nb_path = os.path.join(HERE, PACKAGE_NAME, "static")

# Representative files that should exist after a successful build
jstargets = [os.path.join(lab_path, "package.json")]

package_data_spec = {PACKAGE_NAME: ["*"]}

labext_name = "@marcelgarus/energy"
nbext_name = "jupyter_energy"

data_files_spec = [
    ("share/jupyter/nbextensions/%s" % nbext_name, nb_path, "**"),
    ("share/jupyter/labextensions/%s" % labext_name, lab_path, "**"),
    ("share/jupyter/labextensions/%s" % labext_name, HERE, "install.json"),
    (
        "etc/jupyter/jupyter_server_config.d",
        "jupyter-config/jupyter_server_config.d",
        "jupyter_energy.json",
    ),
    (
        "etc/jupyter/jupyter_notebook_config.d",
        "jupyter-config/jupyter_notebook_config.d",
        "jupyter_energy.json",
    ),
    (
        "etc/jupyter/nbconfig/notebook.d",
        "jupyter-config/nbconfig/notebook.d",
        "jupyter_energy.json",
    ),
]

cmdclass = create_cmdclass(
    "jsdeps", package_data_spec=package_data_spec, data_files_spec=data_files_spec
)

js_command = combine_commands(
    install_npm(src_path, build_cmd="build:prod", npm=["jlpm"]),
    ensure_targets(jstargets),
)

is_repo = os.path.exists(os.path.join(HERE, ".git"))
if is_repo:
    cmdclass["jsdeps"] = js_command
else:
    cmdclass["jsdeps"] = skip_if_exists(jstargets, js_command)

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name=NAME,
    version="0.1.0",
    url="https://github.com/MarcelGarus/jupyter-energy",
    author="Marcel Garus",
    description="Jupyter extension to show how much energy your notebook is using",
    long_description=long_description,
    long_description_content_type="text/markdown",
    cmdclass=cmdclass,
    packages=setuptools.find_packages(),
    install_requires=["jupyter_server>=1.0.0", "prometheus_client", "psutil>=5.6.0"],
    extras_require={
        "dev": ["autopep8", "black", "pytest", "flake8", "pytest-cov>=2.6.1", "mock"]
    },
    zip_safe=False,
    include_package_data=True,
    license="BSD",
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
    ],
)
