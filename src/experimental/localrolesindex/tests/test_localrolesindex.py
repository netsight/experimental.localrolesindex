import unittest
from .utils import Dummy


class TestLocalRolesIndex(unittest.TestCase):
    """Tests for LocalRolesIndex objects."""

    _old_log_write = None

    def setUp(self):
        """
        """
        self._index = self._make_one('allowedRolesAndUsers')
        self._marker = []
        self._values = dict([
            (0, Dummy('/a', ['Anonymous'])),
            (1, Dummy('/a/b', ['Anonymous'])),
            (2, Dummy('/a/b/c', ['Anonymous', 'Authenticated'])),
            (3, Dummy('/a/b/c/a', ['Anonymous', 'Authenticated'])),
            (4, Dummy('/a/b/c/d', ['Anonymous', 'Authenticated'])),
            (5, Dummy('/a/b/c/e', ['Anonymous', 'Authenticated'],
                      local_roles_block=True)),
            (6, Dummy('/a/b/c/e/f', ['Authenticated'])),
            (7, Dummy('/a/b/c/e/f/g', ['Reviewer'])),
        ])
        self._index.unrestrictedTraverse = lambda path_tuple: self.dummy_mapping\
            .get(
            path_tuple)

    @property
    def dummy_mapping(self):
        return {dummy.getPhysicalPath(): dummy for dummy in self._values.values()}

    def tearDown(self):
        """
        """

    def _get_target_class(self):
        from ..localrolesindex import LocalRolesIndex
        return LocalRolesIndex

    def _make_one(self, *args, **kw):
        cls = self._get_target_class()
        return cls(*args, **kw)

    def _populate_index(self):
        for (k, v) in self._values.items():
            self._index._index_object_one(k, v, attr=self._index.id)

    def test_interfaces(self):
        from Products.PluginIndexes.interfaces import IPluggableIndex
        from Products.PluginIndexes.interfaces import ISortIndex
        from Products.PluginIndexes.interfaces import IUniqueValueIndex
        from zope.interface.verify import verifyClass
        LocalRolesIndex = self._get_target_class()

        verifyClass(IPluggableIndex, LocalRolesIndex)
        verifyClass(ISortIndex, LocalRolesIndex)
        verifyClass(IUniqueValueIndex, LocalRolesIndex)

    def test_add_object_without_local_roles(self):
        self._populate_index()
        try:
            self._index.index_object(999, None)
        except Exception:
            self.fail('Should not raise (see KeywordIndex tests)')

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

    def _effect_change(self, document_id, obj):       
        self._values[document_id] = obj
        self._index.index_object(
            document_id,
            obj
        )
       
    def test_reindex_change_no_recurse(self):
        self._populate_index()
        result = self._query_index(['Anonymous', 'Authenticated'], operator='and')
        self.assertEqual(list(result), [2, 3, 4, 5])
        self._effect_change(
            4, 
            Dummy('/a/b/c/d', ['Anonymous', 'Authenticated', 'Editor'])
        )
        result = self._query_index(['Anonymous', 'Authenticated'], operator='and')
        self.assertEqual(list(result), [2, 3, 4, 5])
        result = self._query_index(['Editor'], operator='and')
        self.assertEqual(list(result), [4, ])
        self._effect_change(
            2,
            Dummy('/a/b/c', ['Contributor'])
        )
        result = self._query_index(['Contributor'])
        self.assertEqual(list(result), [2, ])
        result = self._query_index(['Anonymous', 'Authenticated'], operator='and')
        self.assertEqual(list(result), [3, 4, 5])

    def test_reindex_change_recurse(self):
        self._populate_index()
        self._effect_change(
            2,
            Dummy('/a/b/c', ['Contributor'])
        )
        result = self._query_index(['Contributor'])
        self.assertEqual(set(result), {2, 3, 4})
        result = self._query_index(['Anonymous', 'Authenticated'])
        self.assertEqual(set(result), {0, 1, 5, 6})

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

    def test_noindexing_when_raising_attributeerror(self):
        class FauxObject(Dummy):
            def allowedRolesAndUsers(self):
                raise AttributeError

        to_index = FauxObject('/a/b', ['Role'])
        self._index.index_object(10, to_index)
        self.assertFalse(self._index._unindex.get(10))
        self.assertFalse(self._index.getEntryForObject(10))

    def test_noindexing_when_raising_typeeror(self):
        class FauxObject(Dummy):
            def allowedRolesAndUsers(self, name):
                return 'allowedRolesAndUsers'

        to_index = FauxObject('/a/b', ['Role'])
        self._index.index_object(10, to_index)
        self.assertFalse(self._index._unindex.get(10))
        self.assertFalse(self._index.getEntryForObject(10))

    def test_value_removes(self):
        to_index = Dummy('/a/b/c', ['hello'])
        self._index.index_object(10, to_index)
        self.assertTrue(self._index._unindex.get(10))

        to_index = Dummy('/a/b/c', [])
        self._index.index_object(10, to_index)
        self.assertFalse(self._index._unindex.get(10))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestLocalRolesIndex))
    return suite
