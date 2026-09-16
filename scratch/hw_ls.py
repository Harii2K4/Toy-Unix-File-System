import os
import pwd
import argparse
import sys
import stat
from datetime import datetime


def prBlue(s, end="\n"):
    print("\033[34m{}\033[00m".format(s), end=end)


def prYellow(s, end="\n"):
    print("\033[93m{}\033[00m".format(s), end=end)


def prCyan(s, end="\n"):
    print("\033[96m{}\033[00m".format(s), end=end)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="myLs",
        description="We just copied ls but worse",
        epilog="Use the -h flag to display the help menu",
    )
    parser.add_argument(
        "-l",
        action="store_true",
        default=False,
        dest="list",
        help="Use to view the metadata of each file or dir",
    )
    parser.add_argument(
        "-a",
        action="store_true",
        default=False,
        dest="hidden",
        help="Use to view the hidden files/dir",
    )
    parser.add_argument("path", nargs="?", default=".")
    return parser


def formatPermissionBits(permissions: int):
    res = ""
    octal = format(permissions, "o")

    for num in octal:
        bits = format(int(num, 8), "b")
        # because 2 -> 10 and we need 010
        bits = "0" * (3 - len(bits)) + bits
        read_bit = "-" if bits[0] == "0" else "r"
        write_bit = "-" if bits[1] == "0" else "w"
        exec_bit = "-" if bits[2] == "0" else "x"
        res += f"{read_bit}{write_bit}{exec_bit}"
    return res


def getType(entry: os.DirEntry):
    if entry.is_symlink():
        return "l"
    elif entry.is_dir():
        return "d"
    else:
        return "-"


def getEntryMetadata(entry: os.DirEntry, size_width=0):
    # -rw-r--r-- 1 zoraonice zoraonice 1360 Sep 14 18:33 file_tree_with_txt.py
    stat_metadata = entry.stat()
    permissions_bits = formatPermissionBits(stat.S_IMODE(stat_metadata.st_mode))
    links = stat_metadata.st_nlink
    user = pwd.getpwuid(stat_metadata.st_uid).pw_name
    group = pwd.getpwuid(stat_metadata.st_gid).pw_name
    size = stat_metadata.st_size
    date = datetime.fromtimestamp(stat_metadata.st_mtime)
    date = date.strftime("%b %-d %H:%M")
    name = entry.name
    entry_type = getType(entry)
    return (
        f"{entry_type}{permissions_bits} "
        f"{links} {user:<8} {group:<8} {size:>{size_width}} {date} {name}"
    )


def printTable(entry_list: list[os.DirEntry]):
    max_size = max((entry.stat().st_size for entry in entry_list), default=0)
    size_width = len(str(max_size))
    for entry in entry_list:
        row = getEntryMetadata(entry, size_width)
        if entry.is_symlink():
            prCyan(row)
        elif entry.is_dir():
            prBlue(row)
        else:
            # file
            print(row) if entry.name.startswith(".") else prYellow(row)


def main(args):
    parser = build_parser()
    parsed_args = parser.parse_args(args[1:])
    path = parsed_args.path
    entry_list: list[os.DirEntry] = []

    with os.scandir(path) as dir_table:
        for entry in dir_table:
            entry_list.append(entry)

    if not parsed_args.hidden:
        entry_list = list(filter(lambda x: not x.name.startswith("."), entry_list))

    if parsed_args.list:
        printTable(entry_list)
    else:
        for entry in entry_list:
            if entry.is_symlink():
                # Symbolic link
                prCyan(entry.name, end=" ")
            elif entry.is_dir():
                prBlue(entry.name, end=" ")
            else:
                print(entry.name, end=" ") if entry.name.startswith(".") else prYellow(
                    entry.name, end=" "
                )
        print()


if __name__ == "__main__":
    main(sys.argv)
