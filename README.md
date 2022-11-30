# nightly-status-checker

## Installation

Make sure you are in the LHCb environment:

```console
source /cvmfs/lhcb.cern.ch/lib/LbEnv
```
Install the required packages in the local environment
```console
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
# or if that does not work
# pip install click requests pandas tabulate Jinja2
```

## Examples

### Available options

```console
dqcs-shifter:~$ python run.py --help
Usage: run.py [OPTIONS] COMMAND [ARGS]...

Options:
  --verbosity TEXT  verbosity of the logger
  --help            Show this message and exit.

Commands:
  current-status  Print in the terminal the summary of nightly slots
  dqcs-report     Prepare the DQCS report.
```

### Checking current status of the nightly slots

```console
dqcs-shifter:~$ python run.py current-status --slots lhcb-gaussino --date 2022-11-27
INFO:root:-> lhcb-gaussino/2022-11-27/1382:
+---+-----------------+------------+---------------------+----------------------+---------------------+
|   |     Project     | Failed MRs |        *-opt        |     *+dd4hep-opt     |        *-dbg        |
|   |                 |            |    BUILD / TEST     |     BUILD / TEST     |    BUILD / TEST     |
+---+-----------------+------------+---------------------+----------------------+---------------------+
| 0 |      Gaudi      |            | W:0 E:0 / P:293 F:0 | W:0 E:0 / P:293 F:0  | W:0 E:0 / P:293 F:0 |
| 1 |     Geant4      |            |  W:0 E:0 / P:0 F:0  |  W:0 E:0 / P:0 F:0   | W:33 E:0 / P:0 F:0  |
| 2 |    Detector     |            | W:0 E:0 / P:51 F:0  |  W:0 E:0 / P:51 F:0  | W:0 E:0 / P:51 F:0  |
| 3 |      LHCb       |            | W:0 E:0 / P:242 F:0 | W:0 E:0 / P:202 F:0  | W:0 E:0 / P:242 F:0 |
| 4 |   Run2Support   |            |  W:0 E:0 / P:6 F:0  |  W:0 E:0 / P:44 F:0  |  W:0 E:0 / P:6 F:0  |
| 5 | GaussinoExtLibs |            |  W:0 E:0 / P:0 F:0  | W:1049 E:0 / P:0 F:0 |  W:0 E:0 / P:0 F:0  |
| 6 |    Gaussino     |            |  W:2 E:0 / P:7 F:0  |  W:4 E:0 / P:7 F:0   |  W:2 E:0 / P:7 F:0  |
| 7 |      Gauss      |            |  W:5 E:0 / P:5 F:3  |  W:7 E:0 / P:5 F:0   |  W:2 E:0 / P:0 F:0  |
+---+-----------------+------------+---------------------+----------------------+---------------------+
```

More options:
```console
dqcs-shifter:~$ python run.py current-status --help
Usage: run.py current-status [OPTIONS]

  Print in the terminal the summary of nightly slots

Options:
  --projects TEXT   list of project names to check
  --platforms TEXT  list of platform names to check
  --slots TEXT      list of nightly slot names to check
  --date TEXT       date of the slot to check (in '%Y-%m-%d')
  --help            Show this message and exit.
```

### Prepare the nightly summary for the DQCS report

```console
python run.py dqcs-report
```
- exports `output.html` file with the summary tables,
- can be copied & pasted in your report,

More options:

```console
dqcs-shifter:~$ python run.py dqcs-report --help
Usage: run.py dqcs-report [OPTIONS]

  Prepare the DQCS report.

Options:
  --projects TEXT   list of project names to check
  --platforms TEXT  list of platform names to check
  --slots TEXT      list of nightly slot names to check
  --date TEXT       date of the slot to check (in '%Y-%m-%d')
  --days INTEGER    number of days to include in the report
  --html BOOLEAN    write in HTML format
  --filepath TEXT   path to a file
  --help            Show this message and exit.
```
