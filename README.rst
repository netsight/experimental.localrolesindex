.. image:: https://api.travis-ci.org/netsight/experimental.localrolesindex.png
  :target: https://travis-ci.org/netsight/experimental.localrolesindex

.. image:: https://coveralls.io/repos/netsight/experimental.localrolesindex/badge.png
  :target: https://coveralls.io/r/netsight/experimental.localrolesindex


experimental.localrolesindex
============================

This package provides a specialised index for ZCatalog which reduces the number of
objects that need to be examined in order to maintain local roles and user information.

When indexing an portal content, if the potral content
implements the interface::

  experimental.localrolesindex.interfaces.IDecendantLocalRolesAware

then indexing of decendant nodes will occur.

The tentative idea is to replace the existing KeywordIndex
with the LocalRolesIndex defined herewith for 'allowedRolesAndUsers',
and then to to change::

  Products.CMFCore.CMFCatalogAware.CatalogAware.reindexObjectSecurity

such that instead of reindexing object security for  each descendant via a catalog query,
it should instead call reindexObject once on the portal object and allow the experiemental 
LocalRolesIndex to determine which children need to be reindexed.
