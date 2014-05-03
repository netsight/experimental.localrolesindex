import unittest

import zope.interface

from ..interfaces import IDecendantLocalRolesAware
from .utils import Dummy


class TestLocalRolesIndex(unittest.TestCase):
    """Tests for LocalRolesIndex objects."""

    def setUp(self):
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
        self._index.unrestrictedTraverse = self.dummy_mapping.get

    @property
    def dummy_mapping(self):
        return {
            dummy.getPhysicalPath(): dummy
            for dummy in self._values.values()
        }

    def _get_target_class(self):
        from ..localrolesindex import LocalRolesIndex
        return LocalRolesIndex

    def _make_one(self, *args, **kw):
        cls = self._get_target_class()
        return cls(*args, **kw)

    def _populate_index(self):
        for (k, v) in self._values.items():
            self._index._index_object_one(k, v)

    def _query_index(self, local_roles, operator='or'):
        result, used = self._index._apply_index({
            'allowedRolesAndUsers': {
                'query': local_roles,
                'operator': operator
            }
        })
        self.assertEqual(used, (self._index.id,))
        return list(result)

    def _check_index(self, local_roles, expected, operator='or'):
        actual = set(self._query_index(local_roles, operator=operator))
        self.assertEqual(actual, set(expected))

    def _effect_change(self, document_id, obj):
        self._values[document_id] = obj
        self._index.index_object(
            document_id,
            obj
        )

    def test_interfaces(self):
        from Products.PluginIndexes.interfaces import IPluggableIndex
        from Products.PluginIndexes.interfaces import ISortIndex
        from Products.PluginIndexes.interfaces import IUniqueValueIndex
        from zope.interface.verify import verifyClass
        LocalRolesIndex = self._get_target_class()
        verifyClass(IPluggableIndex, LocalRolesIndex)
        verifyClass(ISortIndex, LocalRolesIndex)
        verifyClass(IUniqueValueIndex, LocalRolesIndex)

    def test_index_populated(self):
        self._populate_index()
        values = self._values
        self.assertEqual(len(self._index.referencedObjects()), len(values))

    def test_index_clear(self):
        self._populate_index()
        values = self._values
        self.assertEqual(len(self._index.referencedObjects()), len(values))
        self._index.clear()
        self.assertEqual(len(self._index.referencedObjects()), 0)
        self.assertEqual(list(self._index.shadowtree.descendants()), [])

    def test_index_object_noop(self):
        self._populate_index()
        try:
            self._index.index_object(999, None)
        except Exception:
            self.fail('Should not raise (see KeywordIndex tests)')

    def test_index_empty(self):
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
        self._check_index(['Anonymous'], (0, 1, 2, 3, 4, 5))
        self._check_index(['Authenticated'], (2, 3, 4, 5, 6))
        self._check_index(['Member'], ())

    def test__index_object_on_change_no_recurse(self):
        self._populate_index()
        result = self._query_index(['Anonymous', 'Authenticated'],
                                   operator='and')
        self.assertEqual(list(result), [2, 3, 4, 5])
        self._effect_change(
            4,
            Dummy('/a/b/c/d', ['Anonymous', 'Authenticated', 'Editor'])
        )
        self._check_index(['Anonymous', 'Authenticated'],
                          [2, 3, 4, 5],
                          operator='and')
        self._check_index(['Editor'], [4], operator='and')
        self._effect_change(
            2,
            Dummy('/a/b/c', ['Contributor'])
        )
        self._check_index(['Contributor'], {2})
        self._check_index(['Anonymous', 'Authenticated'], {3, 4, 5},
                          operator='and')

    def test__index_object_on_change_recurse(self):
        self._populate_index()
        self._values[2].aru = ['Contributor']
        dummy = self._values[2]
        zope.interface.alsoProvides(dummy, IDecendantLocalRolesAware)
        self._effect_change(2, dummy)
        self._check_index(['Contributor'], {2, 3, 4})
        self._check_index(['Anonymous', 'Authenticated'], {0, 1, 5, 6})

    def test_reindex_no_change(self):
        self._populate_index()
        obj = self._values[7]
        self._effect_change(7, obj)
        self._check_index(['Reviewer'], {7})
        self._effect_change(7, obj)
        self._check_index(['Reviewer'], {7})

    def test_index_object_when_raising_attributeerror(self):
        class FauxObject(Dummy):
            def allowedRolesAndUsers(self):
                raise AttributeError
        to_index = FauxObject('/a/b', ['Role'])
        self._index.index_object(10, to_index)
        self.assertFalse(self._index._unindex.get(10))
        self.assertFalse(self._index.getEntryForObject(10))

    def test_index_object_when_raising_typeeror(self):
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
        self.assertIn(10, self._index._unindex)

        to_index = Dummy('/a/b/c', [])
        self._index.index_object(10, to_index)
        self.assertNotIn(10, self._index._unindex)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestLocalRolesIndex))
    return suite
