:author: Matt Russell <mattr@netsight.co.uk>
:date: 2014-05-04

Notes
=====

The portal's (Plone site) never gets reindexed, reindex* are no-ops,
see:
portal.reindexObject*.__module__ in debug shell (Implementation is Products.CMFPlone.Portal.PloneSite)


Do we target plone-4.x or plone-5.x?
I vote for the later, since a lot of code has change wrt calls to reindexObjectSecurity
This does, of course, have consequences for plone.intranet.


Where to implement index optisiation?
-------------------------------------
At time of writing, experimental.localrolesindex tries to do the optimisation in
an index. 

Whilst I think the algorithm ('deciding whether indexing is required based on hash of local roles)
and mechanism ('shadowtree') are good, I think the implementing these in an index is not the right place.

Why?
Because in order to index descendants, we need to selectively wakeup objects from the site's content tree (ZODB),
and doing so requires calling either:

  - index.(un)restrictedTraverse  - plone.api.content.get

These methods do not wrap the object in IIndexableObject, which is required in order to access the
required 'allowedRolesAndUsers' attribute.
In order to adapt to wrapper for the content object (IIndexableObject), we require the portal catalog::
   
  >>> getMultiAdapter((obj, catalog), IIndexableObject)

In order to obtain a reference to the catalog from within an index, we'd have to access the catalog.

Using Aquisition is not possible:

>>> aq_parent(catalog.Indexes['path'])
None

This is because:

>>> catalog.Indexes[index_name].getPhysicalPath() == (index_name,)


Solution
--------
The sharing view (plone.app.worflow.browser.sharing.SharingView) is
the only *view* in plone which invokes reindexObjectSecurity, which is the call we want
to change the behaviour of in order to do the optimisation.

All the call sites of :method:`reindexObjectSecurity`:

:find-command:

  find omelette/ -type f -follow -not -name 'test_*' -name '*.py' -exec grep -HnE '[a-z]+\.reindexObjectSec' {} \;


  omelette/Products/CMFPlone/PloneTool.py:878:        obj.reindexObjectSecurity()
  omelette/Products/CMFCore/WorkflowTool.py:639:            ob.reindexObjectSecurity()
  omelette/Products/CMFCore/MembershipTool.py:446:            obj.reindexObjectSecurity()
  omelette/Products/CMFCore/MembershipTool.py:466:            obj.reindexObjectSecurity()
  omelette/plone/app/workflow/browser/sharing.py:109:                self.context.reindexObjectSecurity()
  omelette/plone/app/workflow/browser/sharing.py:549:            context.reindexObjectSecurity()
  omelette/plone/app/workflow/browser/sharing.py:606:            self.context.reindexObjectSecurity()
  omelette/plone/app/iterate/subscribers/workflow.py:61:    event.working_copy.reindexObjectSecurity(et)


For all call sites other than the sharing view, 
we can provide two adapters which adapts the :term:`context` in each case to something like the following:

 :code-block: python

class ILocalRoleSharingOptimiser(zope.interface.Interface):
    """Marker."""


@zope.interface.implementer(ICatalogAware, ILocalRolesSharingOptimiser) # ICatalogAware covers DX and AT
@zope.component.adapter(IPortalContent) # adapt any content object (DX and AT)
class LocalRoleIndexingOptimiser(object):

    def __init__(self, context):
    	self.context = context
	# lookup a persistent utility we use to store the shadow tree
	# GS migration step will have created the shadow tree and need to have indexed all content
	# before we can use it
	# e.g annotation on the portal catalog
    	self._shadowtree = IAnnotations(api.portal.get_tool('portal_catalog'))

    # forward every other attribute to context or raise AttributeError
    def __getattr__(self, name):
        return getattr(self.context, name)

    def reindexObjectSecurity(self, obj):
    	# use the shadow tree a la experiemental.localrolesindex.localrolesindex.LocalRolesIndex
    	...
	pass


For the sharing view, provide a subclass of plone.app.workflow.browser.sharing.SharingView
which just adapts the context to be LocalRolesIndexingOptimiser and
configure this via an overrides.zcml in our product, which overrides plone.app.workflow.browser.configure.zcml:

:code-block: python

class SharingView(plone.app.workflow.browser.sharinga.SharingView):
  
   def __init__(self, context, request):
       context = ILocalRolesSharingOptimiser(context, context)
       super(SharingView, self).__init__(context, request)

:code-block: xml
     
<configure
    xmlns="http://namespaces.zope.org/zope"
    xmlns:browser="http://namespaces.zope.org/browser">

    <browser:page
        name="sharing"
        for="*"
        class="experiemental.localrolesindex.browser.views.SharingView"
        permission="plone.DelegateRoles"
    />

    <browser:page
        name="updateSharingInfo"
        for="*"
        class=".sharing.SharingView"
        attribute="updateSharingInfo"
        permission="plone.DelegateRoles"
        />

</configure>






 

    
