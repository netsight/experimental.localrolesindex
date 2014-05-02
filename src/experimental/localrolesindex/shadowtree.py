import BTrees


class Node(BTrees.family64.OO.BTree):
    """
    - insert node (with descendants)
    - delete a node
    """
    __parent__ = None
    id = None
    block_inherit_roles = False
    token = None
    physical_path = None

    def __init__(self, id='', parent=None):
        super(Node, self).__init__()
        self.id = id
        self.__parent__ = parent

    @classmethod
    def ensure_path_to(cls, root, obj):
        """Retieve the shadow node for corresponding object.

        Ensures that each ancestor upon its path is present in the shadow tree.
        Only the leaf return will be guarenteed to contain local role information.

        :param cls: Node class
        :param root: The root node of the shadow tree
        :param obj: 
        :returns: 
        :rtype: 

        """
        node = root
        for comp in filter(bool, obj.getPhysicalPath()):
            if comp not in node:
                parent = node
                node = cls(parent=parent, id=comp)
                parent[node.id] = node
            else:
                node = node[comp]
        node.update_security_info(obj)
        return node

    def update_security_info(self, obj):
        self.physical_path = obj.getPhysicalPath()
        self.block_inherit_roles = getattr(obj, '__ac_local_roles_block__', False)
        self.token = hash((tuple(obj.allowedRolesAndUsers),
                           self.block_inherit_roles, ))
        assert (self.id == obj.getId())
