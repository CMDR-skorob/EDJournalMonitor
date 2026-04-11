EDJournalMonitor
===

[![](https://github.com/CMDR-skorob/ed_journal_monitor/workflows/CI/badge.svg)](https://github.com/CMDR-skorob/ed_journal_monitor/actions/workflows/ci.yml "Github Actions")
[![](https://codecov.io/gh/CMDR-skorob/gon/branch/master/graph/badge.svg)](https://codecov.io/gh/CMDR-skorob/ed_journal_monitor "Codecov")
[![](https://readthedocs.org/projects/ed_journal_monitor/badge/?version=latest)](https://ed_journal_monitor.readthedocs.io/en/latest "Documentation")
[![](https://img.shields.io/github/license/CMDR-skorob/ed_journal_monitor.svg)](https://github.com/CMDR-skorob/ed_journal_monitor/blob/master/LICENSE "License")
[![](https://badge.fury.io/py/ed_journal_monitor.svg)](https://badge.fury.io/py/ed_journal_monitor "PyPI")

Summary
-------

EDJournalMonitor is a small Python utility for Elite Dangerous that watches
the game's journal log directory, follows the newest journal file as logs
rotate, and publishes each new journal line over a local ZeroMQ `PUB` socket.
It is intended as a lightweight bridge for tools that want to consume
real-time journal events without polling log files directly.

---

Installation
------------

Currently, the library is _not_ on PyPI. It will be uploaded there as 
soon as the code here is mature enough and is proved to work correctly 
with consumers. One can install this library directly from GitHub:
```bash
python -m pip install git+https://github.com/CMDR-skorob/ed_journal_monitor.git
```

Usage
-----

Currently, there is no CLI entry point. This might and will probably change 
in the nearest future. To start the monitor, run:
```bash
python ed_journal_monitor/ed_journal_monitor.py
```

The monitor will start watching the default Elite Dangerous journal directory under
`~/Saved Games/Frontier Developments/Elite Dangerous`, it will follow the newest
journal file (Odyssey journals only) and publish each new log line on 
`tcp://127.0.0.1:5555` through a ZeroMQ `PUB` socket.

Any local ZeroMQ subscriber can connect to that address to consume journal
events in real time.

Development
-----------

### Bumping version

_.bumpversion.toml_ config file is provided for easier version changes 
using [bump-my-version](https://github.com/callowayproject/bump-my-version).

### Dev containers
It is not advisable to use dev containers for working on code that uses 
watchdog library for monitoring filesystem events as these events do not 
propagate into the mounted volumes inside the containers. Use venv instead.

### Managing dependencies
Poetry is configured to manage dependencies of the project.
Run, e.g. `poetry add <library>` to add desired dependency.

### Documentation
Readthedocs+Sphinx config files are provided. To add the docs on the 
readthedocs one would just need to link this repo there.
