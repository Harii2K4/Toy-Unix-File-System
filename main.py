from datetime import datetime,UTC
from enum import Enum
import math


USERS = {1:"zora"}
GROUPS = {1:"zora"}
CURR_UID= 1
CURR_GID = 1

#Constants
BLOCK_SIZE = 4 * 1024 #4KB
MEM_BLOCK_COUNT = 64

DATA_OFFSET = 8
DATA_OFFSET_MEM = 8 * BLOCK_SIZE
INODE_OFFSET = 3
INODE_OFFSET_MEM = INODE_OFFSET * BLOCK_SIZE
INODE_COUNT = 0
ROOT_INODE = 0
INODE_SIZE= 256 # 256 bytes
INODES_PER_BLOCK = BLOCK_SIZE // 256 # 16 inodes for block

# Idx 0 is the Super Block
# Idx 1-2 are the bitmap blocks
# Idx 3-7 are the inode blocks ( Each block consits of an inode array)
# Idx 8-63 are the data block (Used to store user data)
DISK_MEMORY = [None] * MEM_BLOCK_COUNT

#Global Variables
curr_dir = "/"

class Inode_Type(Enum):
    FILE = 1
    DIR = 2
    SYMBOLIC = 3


#FileSystem Internal DS
def create_inode(i_type:Inode_Type):
    global INODE_COUNT
    node_number = INODE_COUNT
    INODE_COUNT+=1
    b_time=m_time =a_time = datetime.now(UTC).timestamp()

    match(i_type):
        case Inode_Type.FILE:
            link_count = 1
            file_type = "_"
            permission_bits = "644"
        case Inode_Type.SYMBOLIC:
            link_count = 1
            file_type = "l"
            permission_bits = "777"
        case Inode_Type.DIR:
            link_count = 2
            file_type = "d"
            permission_bits = "755"

    #each number in a octal
    permission_bits = "644"


    #TODO:Number of Blocks,Size and Data Pointers
    return {
            "inode": node_number,
            "link_count":link_count,
            "mode":file_type+permission_bits,
            "b_time":b_time,
            "m_time":m_time,
            "a_time":a_time,
            "uid":CURR_UID,
            "gid":CURR_GID,
            "blocks":0,
            "size":0,
            "data_ptrs":[]
            }


#Access Functions


def get_inode(inode):

    #In reality the calculation is as follows
    # INODE_OFFSET_MEM + ( INODE_SIZE * inode)  -> this will give the byte address
    # But memory is not byte addressable so we need to find the sector.
    # But here our memory is an array
    iarray_idx =INODE_OFFSET+math.floor(inode/INODES_PER_BLOCK)
    inode_array = DISK_MEMORY[iarray_idx]

    if inode_array is None:
        return []

    idx= inode % INODES_PER_BLOCK
    #TODO:catch index-error for inodes that dont exist
    return inode_array[idx]


def write_dir(dir_table,name,inode):
    pass

def read_dir(data_ptrs):
    if data_ptrs is None or len(data_ptrs) == 0:
        return []

    dir_table =[]

    #This is so wrong in many diffrent ways but for now lets stick to it
    for data_ptr in data_ptrs:
        dir_table.extend(DISK_MEMORY[data_ptr])

    return dir_table

def read_dir_table_from_inode(inode):
    inode_content = get_inode(inode)
    if inode_content.mode.startswith("l") or inode_content.mode.startswith("_"):
        raise Exception("Not a dir")
    return read_dir(inode_content["data_ptrs"])


def walk(dir_table,path_tokens,curr_idx):
    if curr_idx == len(path_tokens):
        return

    if path_tokens[curr_idx] == ".":
        return walk(dir_table,path_tokens,curr_idx+1)

    for entry in dir_table:
        name,inode = entry
        if path_tokens[curr_idx] == name:
            token_dir_table=read_dir_table_from_inode(inode)
            return walk(token_dir_table,path_tokens,curr_idx+1)

    raise Exception("Not a dir")



def stat(path):
    # for now only accepts absolute dir
    #TODO: add relative path support
    path_tokens= path[1:].split("/")
    root_inode = get_inode(0)
    inode_content = walk(root_inode,path_tokens)


def filesystem_mkfs():

    root_inode = create_inode(Inode_Type.DIR)
    root_dir_table=[(".",root_inode.get("inode")),("..",root_inode.get("inode"))]

    #TODO:create the root directory table in memory
    DISK_MEMORY[INODE_OFFSET] = [root_inode]
    DISK_MEMORY[DATA_OFFSET] = root_dir_table # write the table into memory
    #looks stupid why not just store the inode after data is stored? but empty inodes are created first
    root_inode = get_inode(ROOT_INODE)
    root_inode["data_ptrs"].append(DATA_OFFSET)
    root_inode["size"] =len(str(root_dir_table))
    root_inode["blocks"] = 1

    #TODO:need the change the bitmaps


def main():

    while True:
        user=USERS[CURR_UID]
        command = input(f"[{user} {curr_dir}]$ ")

        if command.lower() == "exit":
            return


if __name__ == "__main__":
    filesystem_mkfs()
    print(read_dir(get_inode(0)["data_ptrs"]))
    # main()

