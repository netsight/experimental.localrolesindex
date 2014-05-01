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
            (5, Dummy('/a/b/c/e', ['Anonymous', 'Authenticated'], local_roles_block=True)),
            (6, Dummy('/a/b/c/e/f', ['Anonymous'])),
        ]
        self._noop_req = {'notAnIndex': 123}
        self._all_req = {'allowedRolesAndUsers': ['a']}
        self._some_req = {'allowedRolesAndUsers': ['e']}
        self._overlap_req = {'allowedRolesAndUsers': ['c', 'e']}
        self._string_req = {'allowedRolesAndUsers': 'a'}

    def tearDown(self):
        """
        """

    def _populateIndex(self):
        for k, v in self._values:
            self._index.index_object(k, v)

    def _checkApply(self, req, expectedValues):
        result, used = self._index._apply_index(req)
        self.assertEqual(used, ('allowedRolesAndUsers',))
        self.assertEqual(
            len(result),
            len(expectedValues)
        )

        if hasattr(result, 'keys'):
            result = result.keys()
        for k, v in expectedValues:
            self.assertIn(k, result)

    def test_interfaces(self):
        from Products.PluginIndexes.interfaces import IPluggableIndex
        from Products.PluginIndexes.interfaces import ISortIndex
        from Products.PluginIndexes.interfaces import IUniqueValueIndex
        from zope.interface.verify import verifyClass

        verifyClass(IPluggableIndex, LocalRolesIndex)
        verifyClass(ISortIndex, LocalRolesIndex)
        verifyClass(IUniqueValueIndex, LocalRolesIndex)

    def test_add_object_without_local_roles(self):
        self._populateIndex()
        self.assertFalse(self._index.index_object(999, None))

    def test_empty(self):
        self.assertEqual(len(self._index), 0)
        assert len(self._index.referencedObjects()) == 0
        self.assertEqual(self._index.numObjects(), 0)

        assert self._index.getEntryForObject(1234) is None
        assert (self._index.getEntryForObject(1234, self._marker)
                 is self._marker), self._index.getEntryForObject(1234)
        self._index.unindex_object(1234)

        assert self._index.hasUniqueValuesFor('allowedRolesAndUsers')
        assert not self._index.hasUniqueValuesFor('notAnIndex')
        assert len(self._index.uniqueValues('allowedRolesAndUsers')) == 0

        assert self._index._apply_index(self._noop_req) is None
        self._checkApply(self._all_req, [])
        self._checkApply(self._some_req, [])
        self._checkApply(self._overlap_req, [])
        self._checkApply(self._string_req, [])

    def test_populated(self):
        self._populateIndex()
        values = self._values

        #assert len( self._index ) == len( values )
        assert len(self._index.referencedObjects()) == len(values)

        assert self._index.getEntryForObject(1234) is None
        assert ( self._index.getEntryForObject(1234, self._marker)
                 is self._marker )
        self._index.unindex_object(1234)  # nothrow
        self.assertEqual(self._index.indexSize(), len(values) - 1)

        for k, v in values:
            entry = self._index.getEntryForObject(k)
            entry.sort()
            kw = sortedUnique(v.allowedRolesAndUsers())
            self.assertEqual(entry, kw)

        assert len(self._index.uniqueValues('allowedRolesAndUsers')) == len(values) - 1
        assert self._index._apply_index(self._noop_req) is None

        self._checkApply(self._all_req, values[:-1])
        self._checkApply(self._some_req, values[5:7])
        self._checkApply(self._overlap_req, values[2:7])
        self._checkApply(self._string_req, values[:-1])

    def test_reindex_change(self):
        self._populateIndex()
        expected = Dummy('/x/y', ['Anonymous'])
        self._index.index_object(6, expected)
        result, used = self._index._apply_index({'allowedRolesAndUsers': ['x', 'y']})
        result = result.keys()
        assert len(result) == 1
        assert result[0] == 6
        result, used = self._index._apply_index(
            {'allowedRolesAndUsers': ['a', 'b', 'c', 'e', 'f']}
        )
        result = result.keys()
        assert 6 not in result

    def test_reindex_no_change(self):
        self._populateIndex()
        expected = Dummy('/a/b/c', ['Anonymous'])
        self._index.index_object(8, expected)
        result, used = self._index._apply_index(
            {'allowedRolesAndUsers': ['allowedRolesAndUsers', 'notAnIndex']})
        result = result.keys()
        assert len(result) == 1
        assert result[0] == 8
        self._index.index_object(8, expected)
        result, used = self._index._apply_index(
            {'allowedRolesAndUsers': ['allowedRolesAndUsers', 'notAnIndex']})
        result = result.keys()
        assert len(result) == 1
        assert result[0] == 8

    def test_noindexing_when_noattribute(self):
        to_index = Dummy('/a/b/c/d/e/f/g', ['Anonymous'])
        self._index._index_object(10, to_index, attr='UNKNOWN')
        self.assertFalse(self._index._unindex.get(10))
        self.assertFalse(self._index.getEntryForObject(10))

    def test_noindexing_when_raising_attribute(self):
        class FauxObject:
            def allowedRolesAndUsers(self):
                raise AttributeError

        to_index = FauxObject()
        self._index._index_object(10, to_index, attr='allowedRolesAndUsers')
        self.assertFalse(self._index._unindex.get(10))
        self.assertFalse(self._index.getEntryForObject(10))

    def test_noindexing_when_raising_typeeror(self):
        class FauxObject:
            def allowedRolesAndUsers(self, name):
                return 'allowedRolesAndUsers'

        to_index = FauxObject()
        self._index._index_object(10, to_index, attr='allowedRolesAndUsers')
        self.assertFalse(self._index._unindex.get(10))
        self.assertFalse(self._index.getEntryForObject(10))

    def test_value_removes(self):
        to_index = Dummy('/a/b/c', ['hello'])
        self._index._index_object(10, to_index, attr='allowedRolesAndUsers')
        self.assertTrue(self._index._unindex.get(10))

        to_index = Dummy('')
        self._index._index_object(10, to_index, attr='allowedRolesAndUsers')
        self.assertFalse(self._index._unindex.get(10))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestLocalRolesIndex))
    suite.addTest(unittest.makeSuite(TestNode))
    return suite
