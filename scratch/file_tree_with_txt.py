from collections import deque

class FileTreeNode:
    def __init__(self,name,parent=None):
        self.name = name
        self.parent = parent
        self.children = []

    def __repr__(self):
        return f"{self.name}:{self.parent.name}"


def buildFileTree(file_sys,parent=None):
    if not file_sys:
        return None

    built_nodes=[]

    for item in file_sys:
        curr_node = FileTreeNode(item,parent)
        child_nodes= buildFileTree(file_sys[item],curr_node)
        if child_nodes:
            curr_node.children.extend(child_nodes)
        built_nodes.append(curr_node)

    return built_nodes

def dfs(file_tree):
    print(file_tree)
    for child in file_tree.children:
        dfs(child)

def walk(curr_node,idx,path):
    if not curr_node:
        return "No file or dir"
    if idx==len(path):
        return curr_node

    if path[idx] == ".":
        return walk(curr_node,idx+1,path)
    elif path[idx] == "..":
        return walk(curr_node.parent,idx+1,path)

    for child in curr_node.children:
        if child.name==path[idx]:
            return walk(child,idx+1,path)
    return "No file or dir"

file_sys = {
    "/":{
    "bin":{ "zsh":None, "bash":None },
    "usr":{ "lib":{ "xorg.list":None }, "bin":None }
    }
}


root=buildFileTree(file_sys,None)[0]
print(walk(root,0,["bin","..","fake","..","bin","zsh"]))
