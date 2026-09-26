## Parts Of The Project

FileSystem Internals
Disk Array : Memory 64 bit  and Just a Blocks
Underlying Data structures :
    Inode 
    Conceptual Tree 
Access Functions: 
    read(), write(),open() -> files
    readdir() , writedir(),createdir()->  directory
    stat() -> to view inodes 
    unlink() , link() 

Psuedo - Shell like for using the FileSystem:
Simple Parser:redirection support for adding contents to files 
Commands : 
    iter 1 :ls ( - l / - a), stat , mkdir(- p) , touch
    iter 2 :rm (-r), echo   
    iter 3 :cat , ln

    


