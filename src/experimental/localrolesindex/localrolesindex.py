"""Defines an index for local role information.
"""
from collections import defaultdict

from App.special_dtml import DTMLFile
from Products.PluginIndexes.KeywordIndex.KeywordIndex import KeywordIndex

from .interfaces import IDecendantLocalRolesAware
from .shadowtree import Node


class _DummyObject(object):
    """Faux content item."""

    def __init__(self, aru, path):
        self._aru = aru
        self._path = path

    def getPhysicalPath(self):
        return self._path

    def allowedRolesAndUsers(self):
        return self._aru

    def getId(self):
        return self._path[-1]


class LocalRolesIndex(KeywordIndex):
    """Index local role information.

    This is a replacement for the KeyWordIndex used
    for 'allowedRolesAndUsers' in Plone 4.x

    Maintain a 'shadow tree' of nodes correspoding to the
    portal content tree.

    Indexing of decendant nodes will occur conditionally
    depenant on a portal content object supporting
    the IDecendantLocalRolesAware interface.
    """
    meta_type = 'LocalRolesIndex'
    query_options = ('query', 'operator')

    def __init__(self, *args, **kwargs):
        super(LocalRolesIndex, self).__init__(*args, **kwargs)
        self.clear()

    def clear(self):
        super(LocalRolesIndex, self).clear()
        self.shadowtree = Node()

    def index_object(self, documentId, obj, threshold=None):
        if obj is None:
            return 0
        if IDecendantLocalRolesAware.providedBy(obj):
            index_obj = self._index_object_recursive
        else:
            index_obj = self._index_object_one
        return index_obj(documentId, obj, threshold=threshold)

    def _index_object_one(self, documentId, obj, threshold=None, node=None):
        if node is None:
            node = Node.ensure_ancestry_to(obj, self.shadowtree)
        try:
            node.update_security_info(documentId, obj)
        except (TypeError, AttributeError):
            return 0
        index_object = super(LocalRolesIndex, self)._index_object
        return index_object(documentId, obj, threshold=threshold, attr=self.id)

    def _index_object_recursive(self, documentId, obj, threshold=None):
        node = Node.ensure_ancestry_to(obj, self.shadowtree)
        shared_tokens = defaultdict(list)
        shared_tokens[node.token].append(node)
        for descendant in node.descendants():
            shared_tokens[descendant.token].append(descendant)
        res = 0
        index_one = self._index_object_one
        unindex_object = super(LocalRolesIndex, self).unindex_object
        for old_token, nodes_group in shared_tokens.items():
            first_node = next(iter(nodes_group))
            first_obj = self.unrestrictedTraverse(first_node.physical_path)
            aru = first_obj.allowedRolesAndUsers()
            for node in nodes_group:
                unindex_object(node.document_id)
                dummy = _DummyObject(aru, node.physical_path)
                index_one(node.document_id, dummy, node=node)
                res += 1
        return res


def manage_addLocalRolesIndex(self, id, extra=None, REQUEST=None,
                              RESPONSE=None):
    """ZMI factory to add a local roles index.

    :param self: The context
    :param id: The id of the index when seated in the context.
    :param extra: Extra arguments for the index.
    :param REQUEST: The Zope request object.
    :param RESPONSE: The Zope response object.
    """
    if REQUEST is None:
        URL3 = None
    else:
        URL3 = REQUEST.URL3
    return self.manage_addIndex(id, 'LocalRolesIndex', extra,
                                REQUEST, RESPONSE, URL3)

manage_addLocalRolesIndexForm = DTMLFile('dtml/addLocalRolesIndex', globals())
