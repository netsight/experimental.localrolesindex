from collections import defaultdict

from App.special_dtml import DTMLFile
from Products.PluginIndexes.KeywordIndex.KeywordIndex import KeywordIndex

from experimental.localrolesindex.shadowtree import Node


class LocalRolesIndex(KeywordIndex):
    """
    TODO: Docstring
    """
    meta_type = 'LocalRolesIndex'
    query_options = ('query', 'operator')

    def __init__(self, *args, **kwargs):
        super(LocalRolesIndex, self).__init__(*args, **kwargs)
        self.shadowtree = Node()

    def _index_object(self, documentId, obj, threshold=None, attr=''):
        """
        - Create shadow tree nodes to path of obj (if not exists)
        :param documentId:
        :param obj:
        :param threshold:
        :param attr:
        :return:
        """
        if not attr:
            attr = self.id
        if False:
            return self._index_object_one(documentId, obj, threshold=threshold, attr=attr)
        return self._index_object_recursive(documentId, obj, threshold=threshold,
                                            attr=attr)

    def _index_object_one(self, documentId, obj, threshold=None, node=None, attr=''):
        if node is None:
            node = Node.ensure_path_to(self.shadowtree, obj)
        node.update_security_info(documentId, obj)
        index_object = super(LocalRolesIndex, self)._index_object
        return index_object(documentId, obj, threshold=threshold, attr=attr)

    def _index_object_recursive(self, documentId, obj, threshold=None, attr=''):
        """
        - Index current object (super)
        - Walk shadow tree to get children
        - ReIndex children

        :param documentId:
        :param obj:
        :param threshold:
        :param attr:
        """
        class DummyObject(object):
            def __init__(self, aru, path):
                self._aru = aru
                self._path = path

            def getPhysicalPath(self):
                return self._path

            def allowedRolesAndUsers(self):
                return self._aru

            def getId(self):
                return self._path[-1]

        node = Node.ensure_path_to(self.shadowtree, obj)
        shared_tokens = defaultdict(list)
        shared_tokens[node.token].append(node)
        for descendant in node.descendants():
            shared_tokens[descendant.token].append(descendant)

        res = 0
        for old_token, nodes_group in shared_tokens.items():
            current_group = iter(nodes_group)
            first_node = next(current_group)
            first_obj = self.unrestrictedTraverse(
                first_node.physical_path
            )
            aru = first_obj.allowedRolesAndUsers()
            for node in nodes_group:
                super(LocalRolesIndex, self).unindex_object(node.document_id)
                dummy = DummyObject(
                    aru,
                    node.physical_path
                )
                self._index_object_one(
                    node.document_id,
                    dummy,
                    node=node,
                    attr=attr
                )
                res += 1
        return res

    # def unindex_object(self, documentId):
    #     pass


def manage_addLocalRolesIndex(self, id, extra=None, REQUEST=None,
                              RESPONSE=None):
    """
    Add a local roles index
    :param self:
    :param id:
    :param extra:
    :param REQUEST:
    :param RESPONSE:
    """
    if REQUEST is None:
        URL3 = None
    else:
        URL3 = REQUEST.URL3
    return self.manage_addIndex(id, 'LocalRolesIndex', extra,
                                REQUEST, RESPONSE, URL3)

manage_addLocalRolesIndexForm = DTMLFile('dtml/addLocalRolesIndex', globals())
