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

    def __repr__(self):
        return 'Node("%s")' % self.id

    @classmethod
    def ensure_path_to(cls, root, obj):
        """Retieve the shadow node for corresponding object.

        Ensures that each ancestor upon its path is present in the shadow tree.
        Only the leaf return will be guarenteed to contain local role information.

        :param cls: Node class
        :param root: The root node of the shadow tree
        :param obj: The content object.
        :returns: The leaf shadow 
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
        return node

    def update_security_info(self, obj):
        self.physical_path = obj.getPhysicalPath()
        self.block_inherit_roles = getattr(obj, '__ac_local_roles_block__', False)
        self.token = hash((tuple(obj.allowedRolesAndUsers),
                           self.block_inherit_roles, ))
        assert (self.id == obj.getId())

    def descendants(self, ignore_block=False):
        """Generates descendant nodes, optionally those that have local roles blocked.

        :param ignore_block: If False, and a node has block_local_roles set 
                             to True, do not descend to any of its children.
        """
        for node in self.values():
            if node.block_inherit_roles and not ignore_block:
                continue
            yield node
            for descendant in node.descendants(ignore_block=ignore_block):
                yield descendant
            


