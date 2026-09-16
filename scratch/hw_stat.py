import sys
import os
from datetime import datetime


def main(args):
    if len(args) != 2:
        print("Usage python hw_stat.py <path>")
        return
    path = args[1]
    if len(path) == 0:
        print("Empty path provided")
        return
    try:
        stat_res = os.stat(path)
        print(f"  File: {path}")
        print(
            f"  Size: {stat_res.st_size}           Blocks: {stat_res.st_blocks}           IO Block:{stat_res.st_blksize}"
        )
        print(
            f"Device: {stat_res.st_dev}  Inode: {stat_res.st_ino}  Links: {stat_res.st_nlink}"
        )
        print(f"Access: {datetime.fromtimestamp(stat_res.st_atime)}")
        print(f"Change: {datetime.fromtimestamp(stat_res.st_mtime)}")
        print(f" Birth: {datetime.fromtimestamp(stat_res.st_ctime)}")
    except FileNotFoundError as e:
        print(e)


if __name__ == "__main__":
    main(sys.argv)
