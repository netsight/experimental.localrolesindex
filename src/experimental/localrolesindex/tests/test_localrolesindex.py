import unittest
from experimental.localrolesindex.localrolesindex import LocalRolesIndex


class TestNode(unittest.TestCase):

    def setUp(self):
        pass

    def test_insert_single_node(self):
        self.fail()

    def test_insert_node_with_descendants(self):
        self.fail()


class Dummy(object):

    def __init__(self, path, local_roles, local_roles_block=False):
        self.path = path
        self.allowedRolesAndUsers = local_roles
        self.__ac_local_roles_block__ = local_roles_block
        self.id = path.split('/')[-1]

    def __str__(self):
        return '<Dummy: %s>' % self.id

    __repr__ = __str__

    def getId(self):
        return self.id

    def getPhysicalPath(self):
        return self.path.split('/')


class TestLocalRolesIndex(unittest.TestCase):
    """
    Test LocalRolesIndex objects.
    """
    _old_log_write = None

    def setUp(self):
        """
        """
        self._index = LocalRolesIndex('allowedRolesAndUsers')
        self._marker = []
        self._values = [
            (0, Dummy('/a', ['Anonymous'])),
            (1, Dummy('/a/b', ['Anonymous'])),
            (2, Dummy('/a/b/c', ['Anonymous', 'Authenticated'])),
            (3, Dummy('/a/b/c/a', ['Anonymous', 'Authenticated'])),
            (4, Dummy('/a/b/c/d', ['Anonymous', 'Authenticated'])),
            (5, Dummy('/a/b/c/e', ['Anonymous', 'Authenticated'],
                      local_roles_block=True)),
            (6, Dummy('/a/b/c/e/f', ['Authenticated'])),
            (7, Dummy('/a/b/c/e/f/g', ['Reviewer'])),
        ]

    def tearDown(self):
        """
        """

    def _populate_index(self):
        for (k, v) in self._values:
            self._index.index_object(k, v)

    def test_interfaces(self):
        from Products.PluginIndexes.interfaces import IPluggableIndex
        from Products.PluginIndexes.interfaces import ISortIndex
        from Products.PluginIndexes.interfaces import IUniqueValueIndex
        from zope.interface.verify import verifyClass

        verifyClass(IPluggableIndex, LocalRolesIndex)
        verifyClass(ISortIndex, LocalRolesIndex)
        verifyClass(IUniqueValueIndex, LocalRolesIndex)

    def test_add_object_without_local_roles(self):
        self._populate_index()
        self.assertFalse(self._index.index_object(999, None))

    def test_empty(self):
        self.assertEqual(len(self._index), 0)
        assert len(self._index.referencedObjects()) == 0
        self.assertEqual(self._index.numObjects(), 0)

        self.assertIsNone(self._index.getEntryForObject(1234))
        self.assertEqual(self._index.getEntryForObject(1234, self._marker),
                         self._marker)
        self._index.unindex_object(1234)

        assert self._index.hasUniqueValuesFor('allowedRolesAndUsers')
        assert not self._index.hasUniqueValuesFor('notAnIndex')
        assert len(self._index.uniqueValues('allowedRolesAndUsers')) == 0

    def test_index_object_noop(self):
        self.fail()

    def test_index_object(self):
        self._populate_index()
        docs, used = self._index._apply_index(
            {'allowedRolesAndUsers': ['Anonymous']},
        )
        self.assertEqual(tuple(docs), (0, 1, 2, 3, 4, 5, ))
        self.assertEqual(used, (self._index.id,))

        docs, used = self._index._apply_index(
            {'allowedRolesAndUsers': ['Authenticated']},
        )
        self.assertEqual(tuple(docs), (2, 3, 4, 5, 6, ))
        self.assertEqual(used, (self._index.id,))

        docs, used = self._index._apply_index(
            {'allowedRolesAndUsers': ['Member']},
        )
        self.assertEqual(tuple(docs), ())
        self.assertEqual(used, (self._index.id,))

    def test_populated(self):
        self._populate_index()
        values = self._values

        self.assertEqual(len(self._index.referencedObjects()), len(values))

    def _query_index(self, local_roles, operator='or'):
        result, _ = self._index._apply_index({
            'allowedRolesAndUsers': {
                'query': local_roles,
                'operator': operator
            }
        })
        return list(result)

    def test_reindex_change_no_recurse(self):
        self._populate_index()
        result = self._query_index(['Anonymous', 'Authenticated'], operator='and')
        self.assertEqual(list(result), [2, 3, 4, 5])
        self._index.index_object(
            4,
            Dummy('/a/b/c/d', ['Anonymous', 'Authenticated', 'Editor'])
        )
        result = self._query_index(['Anonymous', 'Authenticated'], operator='and')
        self.assertEqual(list(result), [2, 3, 4, 5])
        result = self._query_index(['Editor'], operator='and')
        self.assertEqual(list(result), [4, ])
        self._index.index_object(
            2,
            Dummy('/a/b/c', ['Contributor'])
        )
        result = self._query_index(['Contributor'])
        self.assertEqual(list(result), [2, ])
        result = self._query_index(['Anonymous', 'Authenticated'], operator='and')
        self.assertEqual(list(result), [3, 4, 5])

    def test_reindex_change_recurse(self):
        self._populate_index()
        self._index.index_object(
            2,
            Dummy('/a/b/c', ['Contributor'])
        )
        result = self._query_index(['Contributor'])
        self.assertEqual(list(result), [2, 3, 4, 5])
        result = self._query_index(['Anonymous', 'Authenticated'])
        self.assertEqual(list(result), [0, 1, 3, 4, 5, 6])

    def test_reindex_no_change(self):
        self._populate_index()
        expected = Dummy('/a/b/c/d/e/f/g', ['Reviewer'])
        self._index.index_object(7, expected)
        result, used = self._index._apply_index(
            {'allowedRolesAndUsers': ['Reviewer']}
        )
        result = result.keys()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 7)
        self._index.index_object(7, expected)
        result, used = self._index._apply_index(
            {'allowedRolesAndUsers': ['Reviewer']}
        )
        result = result.keys()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 7)

    def test_noindexing_when_noattribute(self):
        to_index = Dummy('/a/b/c/d/e/f/g', ['Anonymous'])
        self._index.index_object(10, to_index, attr='UNKNOWN')
        self.assertFalse(self._index._unindex.get(10))
        self.assertFalse(self._index.getEntryForObject(10))

    def test_noindexing_when_raising_attribute(self):
        class FauxObject:
            def allowedRolesAndUsers(self):
                raise AttributeError

        to_index = FauxObject()
        self._index.index_object(10, to_index, attr='allowedRolesAndUsers')
        self.assertFalse(self._index._unindex.get(10))
        self.assertFalse(self._index.getEntryForObject(10))

    def test_noindexing_when_raising_typeeror(self):
        class FauxObject:
            def allowedRolesAndUsers(self, name):
                return 'allowedRolesAndUsers'

        to_index = FauxObject()
        self._index.index_object(10, to_index, attr='allowedRolesAndUsers')
        self.assertFalse(self._index._unindex.get(10))
        self.assertFalse(self._index.getEntryForObject(10))

    def test_value_removes(self):
        to_index = Dummy('/a/b/c', ['hello'])
        self._index.index_object(10, to_index, attr='allowedRolesAndUsers')
        self.assertTrue(self._index._unindex.get(10))

        to_index = Dummy('')
        self._index.index_object(10, to_index, attr='allowedRolesAndUsers')
        self.assertFalse(self._index._unindex.get(10))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestLocalRolesIndex))
    suite.addTest(unittest.makeSuite(TestNode))
    return suite
