from App.special_dtml import DTMLFile
from Products.PluginIndexes.KeywordIndex.KeywordIndex import KeywordIndex
from Products.PluginIndexes.common.UnIndex import UnIndex
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
        return super(LocalRolesIndex, self)._index_object(documentId, obj, threshold, attr)

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
        super(LocalRolesIndex, self)._index_object(documentId, obj, threshold, attr)


    def unindex_object(self, documentId):
        pass


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