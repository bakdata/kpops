"""Runs mypy on kpops, tests and the pre-commit hooks

info: https://jaredkhan.com/blog/mypy-pre-commit
"""
from mypy import api
from sys import stdout, stderr
from hooks import cd

# Args should contain the args that the equivalent
# call to mypy from the shell would contain
args = ["--pretty", "kpops", "tests", "hooks"]
result: tuple = tuple()
with cd():
    result = api.run(args)
# Print normal_report to stdout
print(result[0], file=stdout)
# Print error_report to stderr
print(result[1], file=stderr)
# Exit with the exit code that mypy returns
exit(result[2])
