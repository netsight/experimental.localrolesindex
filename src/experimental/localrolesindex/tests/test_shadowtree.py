import unittest
from .utils import Dummy

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
        self.assertIsNone(leaf.physical_path)
        self.assertEqual(leaf.id, 'a')
        self.assertIsNone(leaf.token)
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
        self.assertIsNone(leaf.physical_path)
        self.assertIsNone(leaf.token)
        self.assertFalse(leaf.block_inherit_roles)

    def test_ensure_path_to_many_deep_no_change(self):
        dummy = Dummy('/a/b/c', ['Anonymous'])
        Node = self.get_target_class()
        leaf1 = Node.ensure_path_to(self.root, dummy)
        leaf2 = Node.ensure_path_to(self.root, dummy)
        self.assertIs(leaf1, leaf2)

    def test_ensure_path_to_changes_leaf_only(self):
        dummy = Dummy('/a/b/c', ['Anonymous'])
        Node = self.get_target_class()
        leaf1 = Node.ensure_path_to(self.root, dummy)
        self.assertFalse(self.root['a']['b'].block_inherit_roles)
        self.root['a']['b'].block_inherit_roles = True
        leaf2 = Node.ensure_path_to(self.root, dummy)
        self.assertIs(leaf1, leaf2)
        self.assertTrue(self.root['a']['b'].block_inherit_roles)

    def test_descendants_empty(self):
        node = self.make_one('foo')
        self.assertEqual(list(node.descendants()), [])
        self.assertEqual(list(node.descendants(ignore_block=False)), [])

    def test_descendants_deep(self):
        dummy1 = Dummy('/a/b/c1/d1/e1', ['Anonymous'])
        dummy2 = Dummy('/a/b/c2/d2/e2/f2', ['Editor'])
        Node = self.get_target_class()
        Node.ensure_path_to(self.root, dummy1)
        leaf = Node.ensure_path_to(self.root, dummy2)
        
        descendant_ids = list(node.id for node in self.root.descendants())
        expected_order = ['a', 'b', 'c1', 'd1', 'e1', 'c2', 'd2', 'e2', 'f2']
        self.assertEqual(descendant_ids, expected_order)

    def test_descendants_deep_with_ignore_block(self):
        dummy1 = Dummy('/a/b/c1/d1/e1', ['Anonymous'])
        dummy2 = Dummy('/a/b/c2/d2/e2/f2', ['Editor'])
        Node = self.get_target_class()
        Node.ensure_path_to(self.root, dummy1)
        leaf = Node.ensure_path_to(self.root, dummy2)

        self.root['a']['b']['c2']['d2'].block_inherit_roles = True

        descendants = self.root.descendants(ignore_block=False)
        descendant_ids = list(node.id for node in descendants)
        expected_order = ['a', 'b', 'c1', 'd1', 'e1', 'c2']
        self.assertEqual(descendant_ids, expected_order)

        descendants = self.root.descendants(ignore_block=True)
        descendant_ids = list(node.id for node in descendants)
        expected_order = ['a', 'b', 'c1', 'd1', 'e1', 'c2', 'd2', 'e2', 'f2']
        self.assertEqual(descendant_ids, expected_order)

    
    # Throw this away when we don't need to refer to concepts.
    # def test_throw_away(self):
    #     dummy1 = Dummy('/a/b/c1/d1/e1', ['Anonymous'])
    #     dummy2 = Dummy('/a/b/c2/d2/e2/f2', ['Editor'])
    #     Node = self.get_target_class()
    #     Node.ensure_path_to(self.root, dummy1)
    #     leaf = Node.ensure_path_to(self.root, dummy2)

    #     self.root['a']['b']['c2']['d2'].block_inherit_roles = True
    #     LOCAL_ROLES = ['R1', 'R2', 'R3']
    #     import random
    #     for node in self.root.descendants(ignore_block=False):
    #         lr = random.sample(LOCAL_ROLES, 2)
    #         dummy = Dummy(node.id, lr)
    #         node.update_security_info(dummy)
        
    #     from collections import defaultdict
    #     shared_tokens = defaultdict(set)
    #     for node in self.root.descendants(ignore_block=True):
    #         print('Node: %s, Parent: %s' % (node.id, node.__parent__.id))
    #         shared_tokens[node.token].add(node)
    #     from pprint import pprint
    #     print('Shared Tokens:')
    #     pprint(dict(shared_tokens))

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestNode))
    return suite
