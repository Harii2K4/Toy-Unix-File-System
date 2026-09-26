from datetime import datetime,UTC
from enum import Enum
import math
import sys
import os
import argparse
import readline

#this is the root user
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
ROOT_INODE_NUM = 0
INODE_SIZE= 256 # 256 bytes
INODES_PER_BLOCK = BLOCK_SIZE // INODE_SIZE # 16 inodes for block
INODE_BITMAP = 1
DATA_BITMAP = 2

# Idx 0 is the Super Block
# Idx 1-2 are the bitmap blocks
# Idx 3-7 are the inode blocks ( Each block consits of an inode array)
# Idx 8-63 are the data block (Used to store user data)
DISK_MEMORY = [None] * MEM_BLOCK_COUNT

#Global Variables
curr_dir = "/"

def memory_init():
    global DISK_MEMORY,INODE_OFFSET,DATA_OFFSET,INODES_PER_BLOCK

    for idx in range(INODE_OFFSET,DATA_OFFSET):
        DISK_MEMORY[idx]=[[]] * INODES_PER_BLOCK

    for idx in range(DATA_OFFSET,len(DISK_MEMORY)):
        DISK_MEMORY[idx]=[]

    #bit-maps
    data_bitmap = [0]*(len(DISK_MEMORY) - DATA_OFFSET)
    inode_bitmap = [0]*(INODES_PER_BLOCK)*(DATA_OFFSET - INODE_OFFSET)

    DISK_MEMORY[INODE_BITMAP]=inode_bitmap
    DISK_MEMORY[DATA_BITMAP] = data_bitmap

class Inode_Type(Enum):
    FILE = 1
    DIR = 2
    SYMBOLIC = 3

def prBlue(s, end="\n"):
    print("\033[34m{}\033[00m".format(s), end=end)

def prYellow(s, end="\n"):
    print("\033[93m{}\033[00m".format(s), end=end)

def prCyan(s, end="\n"):
    print("\033[96m{}\033[00m".format(s), end=end)

#FileSystem Internal DS
def get_free_inode_block():
    for idx,val in enumerate(DISK_MEMORY[INODE_BITMAP]):
        if val == 0:
           disk_block_idx=INODE_OFFSET+(idx//INODES_PER_BLOCK)
           partition_in_block=idx%INODES_PER_BLOCK
           DISK_MEMORY[INODE_BITMAP][idx]=1
           return DISK_MEMORY[disk_block_idx],partition_in_block

    raise Exception("Failed to create inode memory is full")

def get_free_data_block_idx():
    for idx,val in enumerate(DISK_MEMORY[DATA_BITMAP]):
        if val == 0:
            DISK_MEMORY[DATA_BITMAP][idx] = 1
            return DATA_OFFSET+idx

    raise Exception("Failed to store data memory is full")

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
def resolve_path(path):
    path=path.strip(" ")

    if path.startswith("/"):
        return path

    global curr_dir
    path_resolved = os.path.join(curr_dir,path)

    return path_resolved

def get_inode(inode_number):

    #In reality the calculation is as follows
    # INODE_OFFSET_MEM + ( INODE_SIZE * inode)  -> this will give the byte address
    # But memory is not byte addressable so we need to find the sector.
    # But here our memory is an array
    iarray_idx =INODE_OFFSET+math.floor(inode_number/INODES_PER_BLOCK)
    inode_array = DISK_MEMORY[iarray_idx]

    if inode_array is None:
        return []

    idx= inode_number % INODES_PER_BLOCK
    try :
        return inode_array[idx]
    except IndexError:
        raise Exception("No such file or directory")

def read_mem(data_ptr):
    global DISK_MEMORY
    try:
        return DISK_MEMORY[data_ptr]
    except IndexError:
        raise Exception(f"Data not found in memory: {data_ptr}")

def write_dir(mem_block,name,inode_number):
    for existing_name,_ in mem_block:
        if existing_name == name:
            raise Exception("File exists")

    mem_block.append((name,inode_number))

def read_dir(data_ptrs):
    if data_ptrs is None or len(data_ptrs) == 0:
        return []

    dir_table =[]

    #This is so wrong in many diffrent ways but for now lets stick to it
    for data_ptr in data_ptrs:
        dir_table.append(read_mem(data_ptr))

    return dir_table

def read_dir_table_from_inode(inode_number):
    inode_content = get_inode(inode_number)
    if inode_content['mode'].startswith("l") or inode_content['mode'].startswith("_"):
        raise Exception("Not a directory")
    return read_dir(inode_content["data_ptrs"])

def create_dir(parent_dir_table,new_dir):
    #1)Increment link count of parent
    #2)read and update the bitmaps of inode and data
    #3)Create new_dir inode and dir_table
    #4)add the name,inode to parent
    #5)Change access time of parent
    #Done in this order to recover from crashes (got it so wrong the first time)
    parent_dir_table_unpacked = unpack_array(parent_dir_table)
    parent_inode_number = None

    for name,inode_number in parent_dir_table_unpacked:
        if name == ".":
            parent_inode_number = inode_number
            break
    assert parent_inode_number is not None
    parent_inode = get_inode(parent_inode_number)
    parent_inode["link_count"]+=1
    parent_inode["a_time"] = datetime.now(UTC).timestamp()

    new_dir_inode = create_inode(Inode_Type.DIR)
    new_dir_inode_number = new_dir_inode["inode"]
    allocated=False

    new_dir_table =[(".",new_dir_inode.get("inode")),("..",parent_inode.get("inode"))]

    idx = get_free_data_block_idx()
    DISK_MEMORY[idx] = new_dir_table

    new_dir_inode["data_ptrs"].append(idx)
    new_dir_inode["size"] =len(str(new_dir_table))
    new_dir_inode["blocks"] = 1

    inode_block,idx = get_free_inode_block()
    inode_block[idx] = new_dir_inode

    parent_inode["m_time"] = datetime.now(UTC).timestamp()
    write_dir(parent_dir_table[-1],new_dir,new_dir_inode_number)

    return [new_dir_table]

def unpack_array(arr):
    unpacked_arr = []
    for elem in arr:
        unpacked_arr.extend(elem)
    return unpacked_arr

def walk(dir_table,path_tokens,curr_idx):
    if curr_idx == len(path_tokens):
        return dir_table

    if path_tokens[curr_idx] == ".":
        return walk(dir_table,path_tokens,curr_idx+1)

    unpacked_dir_table = unpack_array(dir_table)
    for entry in unpacked_dir_table:
        name,inode_number = entry
        if path_tokens[curr_idx] == name:
            inode=get_inode(inode_number)
            inode['a_time']=datetime.now(UTC).timestamp()
            token_dir_table=read_dir_table_from_inode(inode_number)
            return walk(token_dir_table,path_tokens,curr_idx+1)

    raise Exception("No such file or directory")

def format_permissions(mode):
    permission_bits =""
    for mode_num in mode:
        bits= format(int(mode_num),"b")
        read_bit = "-" if bits[0] == "0" else "r"
        write_bit = "-" if bits[1] == "0" else "w"
        exec_bit = "-" if bits[2] == "0" else "x"
        permission_bits+= f"{read_bit}{write_bit}{exec_bit}"
    return permission_bits

def print_inode(inode_obj,path):
        user_name = USERS[inode_obj['uid']]
        grp_name= USERS[inode_obj['gid']]
        mode =inode_obj['mode']

        match(mode[0]):
            case "_":
                i_type = "regular file"
            case "d":
                i_type = "directory"
            case "l":
                i_type = "symbolic link"

        formatted_mode = format_permissions(mode[1:])
        formatted_mode = mode[0]+formatted_mode

        print(f"  File: {path}")
        print(f"  Size: {inode_obj['size']}        Blocks: {inode_obj['blocks']} {i_type}" )
        print(f" Inode: {inode_obj['inode']}         Links: {inode_obj['link_count']}")
        print(f"  Mode: {formatted_mode}  Uid: ({inode_obj['uid']}/{user_name})  Gid: ({inode_obj['gid']}/{grp_name})")
        print(f"Access: {datetime.fromtimestamp(inode_obj['a_time'])}")
        print(f"Modify: {datetime.fromtimestamp(inode_obj['m_time'])}")
        print(f" Birth: {datetime.fromtimestamp(inode_obj['b_time'])}")

def tokenize_path(path):
    path_tokens= path[1:].split("/")
    path_tokens = [token for token in path_tokens if token !=""]

    return path_tokens

def stat(path):
    #TODO: add support files and symbolic links
    path_tokens= tokenize_path(resolve_path(path))
    target_token = path_tokens.pop() if path_tokens else "."
    root_dir_table=read_dir_table_from_inode(ROOT_INODE_NUM)
    root_inode = get_inode(ROOT_INODE_NUM)
    root_inode["a_time"] = datetime.now(UTC).timestamp()
    parent_dir_table=unpack_array(walk(root_dir_table,path_tokens,0))
    target_inode = [inode_number for name,inode_number in parent_dir_table if name == target_token]
    assert len(target_inode) <=1

    if len(target_inode) == 0:
        raise Exception("No such file or dir")

    target_inode_obj = get_inode(target_inode[0])
    print_inode(target_inode_obj,path)
    return


def getEntryMetadata(inode_obj,name,size_width=0):
    # -rw-r--r-- 1 zoraonice zoraonice 1360 Sep 14 18:33 file_tree_with_txt.py
    links = inode_obj["link_count"]
    user = USERS[inode_obj["uid"]]
    group = GROUPS[inode_obj["gid"]]
    size = inode_obj["size"]
    date = datetime.fromtimestamp(inode_obj["m_time"])
    date = date.strftime("%b %-d %H:%M")
    entry_type = inode_obj["mode"][0]
    permissions_bits = format_permissions(inode_obj["mode"][1:])
    return (
        f"{entry_type}{permissions_bits} "
        f"{links} {user} {group} {size:>{size_width}} {date} {name}"
    )


def pretty_print(content,obj_type,hidden,end=" "):
    match obj_type:
        case "_":
            if hiddent:
                print(content,end=end)
            else:
                prYellow(content,end=end)
        case "l":
            prCyan(content,end=end)
        case "d":
            prBlue(content,end=end)

def ls(path,show_hidden=False,display_table=False):
    path_tokens= tokenize_path(resolve_path(path))
    root_dir_table=read_dir_table_from_inode(ROOT_INODE_NUM)
    root_inode = get_inode(ROOT_INODE_NUM)
    root_inode["a_time"] = datetime.now(UTC).timestamp()

    if not path_tokens:
        entries=unpack_array(root_dir_table)
    else:
        entries=unpack_array(walk(root_dir_table,path_tokens,0))

    if not show_hidden:
        entries = filter(lambda x: not x[0].startswith("."),entries)

    inode_objs =[(name,get_inode(inode_number)) for name,inode_number in entries]

    if display_table:
        max_size = max((inode_obj["size"] for _,inode_obj in inode_objs),default=0)
        # l pad for size column
        size_width = len(str(max_size))

        for name,inode in inode_objs:
            row = getEntryMetadata(inode,name,size_width)
            obj_type=inode['mode'][0]
            hidden = True if name.startswith(".") else False
            pretty_print(row,obj_type,hidden,end="\n")

    else:
        for name,inode in inode_objs:
            obj_type=inode['mode'][0]
            hidden = True if name.startswith(".") else False
            pretty_print(name,obj_type,hidden,end=" ")
        print()


def mkdir_recurse(dir_table,path_tokens,curr_idx):
    if curr_idx == len(path_tokens):
        return dir_table

    if path_tokens[curr_idx] == ".":
        return walk(dir_table,path_tokens,curr_idx+1)

    unpacked_dir_table = unpack_array(dir_table)
    for entry in unpacked_dir_table:
        name,inode_number = entry
        if path_tokens[curr_idx] == name:
            inode = get_inode(inode_number)
            inode["a_time"] = datetime.now(UTC).timestamp()
            token_dir_table=read_dir_table_from_inode(inode_number)
            return mkdir_recurse(token_dir_table,path_tokens,curr_idx+1)

    new_dir_table=create_dir(dir_table,path_tokens[curr_idx])
    return mkdir_recurse(new_dir_table,path_tokens,curr_idx+1)

def mkdir(path,create_parents):

    path_tokens = tokenize_path(resolve_path(path))
    try :
        new_dir = path_tokens.pop()
    except IndexError:
        #For the root dir which exists
        raise Exception("File exists")
    root_dir_table=read_dir_table_from_inode(ROOT_INODE_NUM)

    if create_parents:
        parent_dir_table=mkdir_recurse(root_dir_table,path_tokens,0)
    else :
        parent_dir_table=walk(root_dir_table,path_tokens,0)

    create_dir(parent_dir_table,new_dir)
    return


def cd(path):
    cand_path = resolve_path(path)
    root_dir_table=read_dir_table_from_inode(ROOT_INODE_NUM)
    path_tokens = tokenize_path(cand_path)

    #will throw error if the path is invalid
    walk(root_dir_table,path_tokens,0)

    global curr_dir
    cand_path_tokens=[]
    for idx in range(0,len(path_tokens)):
        if path_tokens[idx] == ".":
            continue
        elif path_tokens[idx] == "..":
            cand_path_tokens.pop()
        else:
            cand_path_tokens.append(path_tokens[idx])

    cleaned_cand_path = "/"+"/".join(cand_path_tokens)
    curr_dir = cleaned_cand_path

def filesystem_mkfs():
    root_inode = create_inode(Inode_Type.DIR)
    root_dir_table=[(".",root_inode.get("inode")),("..",root_inode.get("inode"))]

    #create the root directory table in memory
    DISK_MEMORY[INODE_BITMAP][0] = 1
    DISK_MEMORY[INODE_OFFSET][0] = root_inode
    DISK_MEMORY[DATA_BITMAP][0] = 1
    # print(f"Inode bitmap: {len(inode_bitmap)}")
    # print(f"data bitmap: {len(data_bitmap)}")
    DISK_MEMORY[DATA_OFFSET] = root_dir_table # write the table into memory
    #looks stupid why not just store the inode after data is stored? but empty inodes are created first
    root_inode = get_inode(ROOT_INODE_NUM)
    root_inode["data_ptrs"].append(DATA_OFFSET)
    root_inode["size"] =len(str(root_dir_table))
    root_inode["blocks"] = 1


#Cli parser - simple shell
def parser_init():
    parser = argparse.ArgumentParser(
                    prog='File system shell',
                    description='Simple command like to plan with the file system ',
                    epilog='help for the help menu and exit to exit the shell')


    subparsers=parser.add_subparsers(title="Command",dest="command",help="subparser help command")

    exit_parser=subparsers.add_parser("exit",help='Exit the shell')

    ls_parser = subparsers.add_parser('ls', help='List the directory content')
    ls_parser.add_argument('path',nargs="?",default=".",type=str,help="file/dir path")
    ls_parser.add_argument('-a',default=False,action='store_true')
    ls_parser.add_argument('-l',default=False,action='store_true')

    ls_parser = subparsers.add_parser('mkdir', help='Create a new directory')
    ls_parser.add_argument('paths',nargs="+",help="file/dir path")
    ls_parser.add_argument('-p',default=False,action='store_true')

    cd_parser = subparsers.add_parser('cd', help='Change the current working directory')
    cd_parser.add_argument('path',nargs="?",default=".",type=str,help="file/dir path")

    pwd_parser = subparsers.add_parser('pwd', help='Print the name of the current working directory')

    stat_parser= subparsers.add_parser('stat', help='Display file or file system status')
    stat_parser.add_argument('path',nargs="?",default=".",type=str,help="file/dir path")

    return parser

def curr_dir_for_prompt(curr_dir):
    if curr_dir == "/":
       return curr_dir

    return curr_dir.split("/")[-1]

def main():
    global curr_dir
    parser=parser_init()

    while True:
        user=USERS[CURR_UID]
        user_input= input(f"[{user} {curr_dir_for_prompt(curr_dir)}]$ ")
        input_tokens = user_input.split(" ")

        parsed_args=parser.parse_args(input_tokens)

        match parsed_args.command:
            case "ls":
                try:
                    ls(parsed_args.path,parsed_args.a,parsed_args.l)
                except Exception as e:
                    print(f"ls: cannot access {parsed_args.path}: {e}")
            case "exit":
                return
            case "cd":
                try:
                    cd(parsed_args.path)
                except Exception as e:
                    print(f"cd: cannot access {parsed_args.path}: {e}")
            case "pwd":
                print(curr_dir)
            case "mkdir":
                try:
                   for path in parsed_args.paths:
                       mkdir(path,parsed_args.p)
                except Exception as e:
                    print(f"mkdir: cannot create directory {path}: {e}")
            case "stat":
                try:
                    stat(parsed_args.path)
                except Exception as e:
                    print(f"stat: cannot statx {parsed_args.path}: {e}")

if __name__ == "__main__":
    memory_init()
    filesystem_mkfs()
    main()
