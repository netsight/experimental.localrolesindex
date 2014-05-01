from App.special_dtml import DTMLFile
from Products.PluginIndexes.common.UnIndex import UnIndex


class LocalRolesIndex(UnIndex):
    """
    TODO: Docstring
    """
    meta_type = 'LocalRolesIndex'
    query_options = ('query', )

    def _index_object(self, documentId, obj, threshold=None, attr=''):
        """

        :param documentId:
        :param obj:
        :param threshold:
        :param attr:
        :return:
        """
        roles = getattr(obj, 'allowedRolesAndUsers', None)
        if not roles:
            return False
        return False

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