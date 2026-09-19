from datetime import datetime,UTC
from enum import Enum


USERS = {1:"zora"}
GROUPS = {1:"zora"}
CURR_UID= 1
CURR_GID = 1

#Constants
BLOCK_SIZE = 8 * 1024 #4KB
MEM_BLOCK_COUNT = 64

DATA_OFFSET = 8 * BLOCK_SIZE
INODE_OFFSET = 3 * BLOCK_SIZE
INODE_COUNT = 0

# Idx 0 is the Super Block
# Idx 1-2 are the bitmap blocks
# Idx 3-7 are the inode blocks ( Each block consits of an inode array)
# Idx 8-63 are the data block (Used to store user data)
DISK_MEMORY = [None] * MEM_BLOCK_COUNT

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
            "Size":0,
            "data_ptrs":[]
            }


#Access Functions

def main():
    print(create_inode(Inode_Type.FILE))

if __name__ == "__main__":
    main()

