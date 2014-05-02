import unittest
from experimental.localrolesindex.tests.utils import Dummy


class TestNode(unittest.TestCase):

    def setUp(self):
        self.root = self.make_one()

    def get_target_class(self):
        from experimental.localrolesindex.shadowtree import Node
        return Node

    def make_one(self, *args, **kw):
        cls = self.get_target_class()
        return cls(*args, **kw)

    def test_update_security_info(self):
        node = self.make_one('foobar', parent=self.root)
        self.assertEqual(node.id, 'foobar')
        self.assertIs(node.__parent__, self.root)
        self.assertIsNone(node.token)
        self.assertIsNone(node.physical_path)
        self.assertFalse(node.block_inherit_roles)
        node.update_security_info(Dummy('/foobar', ['Editor'], local_roles_block=True))
        self.assertEqual(node.id, 'foobar')
        self.assertIs(node.__parent__, self.root)
        self.assertIsInstance(node.token, int)
        self.assertEqual(node.physical_path, ('', 'foobar'))
        self.assertTrue(node.block_inherit_roles)

    def test_ensure_path_to_one_deep(self):
        dummy = Dummy('/a', ['Anonymous'])
        Node = self.get_target_class()
        leaf = Node.ensure_path_to(self.root, dummy)
        self.assertIn('a', self.root, list(self.root.keys()))
        self.assertEqual(self.root['a'].id, leaf.id)
        self.assertIsNone(leaf.__parent__.__parent__)
        self.assertEqual(leaf.physical_path, dummy.getPhysicalPath())
        self.assertEqual(leaf.id, 'a')
        self.assertIsInstance(leaf.token, int)
        self.assertFalse(leaf.block_inherit_roles)

    def test_ensure_path_to_many_deep(self):
        dummy = Dummy('/a/b/c', ['Anonymous'])
        Node = self.get_target_class()
        leaf = Node.ensure_path_to(self.root, dummy)

        b = leaf.__parent__
        self.assertEqual(b.id, 'b')
        self.assertIsNone(b.physical_path)
        self.assertIsNone(b.token)
        self.assertFalse(b.block_inherit_roles)

        a = b.__parent__
        self.assertEqual(a.id, 'a')
        self.assertIsNone(a.physical_path)
        self.assertIsNone(a.token)
        self.assertFalse(a.block_inherit_roles)

        self.assertEqual(leaf.__parent__.id, 'b')
        self.assertEqual(leaf.physical_path, dummy.getPhysicalPath())
        self.assertEqual(leaf.id, 'c')
        self.assertIsInstance(leaf.token, int)
        self.assertFalse(leaf.block_inherit_roles)

    def test_search(self):
        self.fail()


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestNode))
    return suite
