"""All the process that can be run using nox.

The nox run are build in isolated environment that will be stored in .nox. to force the venv update, remove the .nox/xxx folder.
"""

import nox
import toml


@nox.session(reuse_venv=True)
def lint(session):
    """Apply the pre-commits."""
    session.install("pre-commit")
    session.run("pre-commit", "run", "--a", *session.posargs)


@nox.session(reuse_venv=True)
def app(session):
    """Run the application."""
    init_notebook = toml.load("pyproject.toml")["sepal-ui"]["init-notebook"]
    session.install("numpy")
    session.install("gdal==3.4.3")
    session.install("-r", "requirements.txt")
    session.run("jupyter", "trust", init_notebook)
    session.run("voila", "--debug", init_notebook)


@nox.session(reuse_venv=True)
def jupyter(session):
    """Run the application"""
    session.install("numpy")
    session.install("gdal==3.4.3")
    session.install("-r", "requirements.txt")
    session.run("jupyter", "trust", "no_ui.ipynb")
    session.run("jupyter", "notebook", "no_ui.ipynb")
