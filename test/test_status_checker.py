import subprocess


def test_cli_simple_training():
    ex_generate = subprocess.run(
        [
            "python",
            "run.py",
            "current-status",
            "--slots",
            "lhcb-sim11",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert ex_generate.returncode == 0
