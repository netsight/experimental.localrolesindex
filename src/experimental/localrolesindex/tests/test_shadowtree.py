import unittest
from experimental.localrolesindex.tests.utils import Dummy


class TestNode(unittest.TestCase):

    def setUp(self):
        # self.treestruct = {
        #     'id': 'plone-site',
        #     'local_roles': [],
        #     'A': {
        #         'children': {
        #             'B': {
        #                 'children': None
        #             },
        #             'C': {
        #                 'children': {
        #                     'children': {
        #                         'D': {
        #                             'children': None
        #                         },
        #                         'E': {
        #                             'children': {
        #                                 'F': {
        #                                     'children': None
        #                                 }
        #                             }
        #                         }
        #                     }
        #                 }
        #             }
        #         }
        #     }
        # }
        # t={
        #     'A': None,
        #     'B': 'A',
        #     'C': 'A',
        #
        #     'F': 'E',
        # }
        self.root = self.make_one('portal')

    def make_one(self, *args, **kw):
        from experimental.localrolesindex.shadowtree import Node

        return Node(*args, **kw)

    def test_add_descendant_one_deep(self):
        dummy = Dummy('/a', ['Anonymous'])
        leaf = self.root.add_descendant(dummy)
        self.assertEqual(leaf.__parent__.id, 'portal')
        self.assertEqual(self.root['a'].physical_path, dummy.getPhysicalPath())
        self.assertEqual(leaf.id, 'a')
        self.assertIsInstance(leaf.token, int)
        self.assertFalse(leaf.block_inherit_roles)

    def test_add_descendant_many_deep(self):
        dummy = Dummy('/a/b/c', ['Anonymous'])
        leaf = self.root.add_descendant(dummy)
        self.assertEqual(leaf.__parent__.id, 'b')
        self.assertEqual(self.root['a']['b']['c'].physical_path, dummy.getPhysicalPath())
        self.assertEqual(leaf.id, 'c')
        self.assertIsInstance(leaf.token, int)
        self.assertFalse(leaf.block_inherit_roles)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestNode))
    return suite
