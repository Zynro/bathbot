import random
import subprocess
import traceback
from bs4 import BeautifulSoup


def rand_color():
    return random.randint(0, 0xFFFFFF)


def git_sub(*args):
    try:
        return subprocess.check_output(["git"] + list(args), stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        return print("Exception on process, rc=", e.returncode, "output=", e.output)


def get_master_hash(repo):
    versions = str(git_sub("ls-remote", repo))
    return versions.split("\\n")[-2].split("\\")[0]


def gen_traceback(exception):
    # get data from exception
    etype = type(exception)
    trace = exception.__traceback__

    # the verbosity is how large of a traceback to make
    # more specifically, it's the amount of levels up the traceback goes from
    # the exception source
    verbosity = 4

    # 'traceback' is the stdlib module, `import traceback`.
    lines = traceback.format_exception(etype, exception, trace, verbosity)

    # format_exception returns a list with line breaks embedded in the lines,
    # so let's just stitch the elements together
    traceback_text = "".join(lines)

    # now we can send it to the user
    # it would probably be best to wrap this in a codeblock via e.g. a Paginator
    return f"```{traceback_text}```"


def num_emoji_gen(number):
    number = str(number)
    number_emoji_dict = {
        "1": ":one:",
        "2": ":two:",
        "3": ":three:",
        "4": ":four:",
        "5": ":five:",
        "6": ":six:",
        "7": ":seven:",
        "8": ":eight:",
        "9": ":nine:",
        "0": ":zero:",
        ".": "<:periodt:667205110937419786>",
        "%": "<:percentmoji:667203548639002642>",
    }
    number_string = ""
    for digit in number:
        number_string += number_emoji_dict[digit]
    return number_string


async def async_get_json(session, URL):
    async with session.get(URL) as response:
        return await response.json()


async def async_fetch_text(session, URL):
    async with session.get(URL) as response:
        return await response.text()


def bs4_parse_html(resp):
    return BeautifulSoup(resp, "html.parser")
