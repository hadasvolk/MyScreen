import shlex
from subprocess import Popen, PIPE

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
        print("ok")

cmd = "samtool"  # arbitrary external command, e.g. "python mytest.py"
exitcode, out, err = get_exitcode_stdout_stderr(cmd)

print(exitcode)
print(out)
print(err)
