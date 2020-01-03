import random
import subprocess


def generate_random_color():
    return random.randint(0, 0xFFFFFF)


def git_subprocess(*args):
    try:
        return subprocess.check_output(["git"] + list(args), stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        return print("Exception on process, rc=", e.returncode, "output=", e.output)
