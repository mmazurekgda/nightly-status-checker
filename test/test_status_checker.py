import subprocess


def test_status_checker():
    ex_generate = subprocess.run(
        [
            "python",
            "run.py",
            "--verbosity",
            "DEBUG",
            "current-status",
            "--slots",
            "lhcb-sim11",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert ex_generate.returncode == 0
