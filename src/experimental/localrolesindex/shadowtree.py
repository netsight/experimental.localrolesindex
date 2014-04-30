import BTrees


class Node(BTrees.family64.OO.BTree):
    """
    - insert node (with descendants)
    - delete a node
    """
    __parent__ = None

    def __init__(self, obj=None, parent=None):
        super(BTrees.family64.OO.BTree, self).__init__()
        self.__parent__ = parent
        self.block_inherit_roles = getattr(obj, '__ac_local_roles_block__', False)
        self.token = hash((obj.allowedRolesAndUsers,
                           self.block_inherit_roles, ))
        self.id = obj.getId()
