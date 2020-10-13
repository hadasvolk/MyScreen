import shlex
from subprocess import Popen, PIPE
import os


def get_exitcode_stdout_stderr(cmd):
    """
    Execute the external command and get its exitcode, stdout and stderr.
    """
    args = shlex.split(cmd)

    try:
        proc = Popen(args, stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
        exitcode = proc.returncode
        return exitcode, out.decode(), err.decode()
    except FileNotFoundError:
        print("failed")
        os._exit(1)


exitcode, out, err = get_exitcode_stdout_stderr("dotnet")

print(exitcode)
print(out)
print(err)
