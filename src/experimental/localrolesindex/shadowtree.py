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

    def add_descendant(self, obj):
        node = type(self)(parent=self, id=obj.getId())
        node.physical_path = obj.getPhysicalPath()
        node.block_inherit_roles = getattr(obj, '__ac_local_roles_block__', False)
        node.token = hash((tuple(obj.allowedRolesAndUsers),
                           node.block_inherit_roles, ))
        assert (node.id == obj.getId())
        self[node.id] = node
        return node
