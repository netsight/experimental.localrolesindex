:author: Matt Russell <mattr@netsight.co.uk>
:date: 2014-05-04

Notes
=====

The portal's (Plone site) never gets re-indexed, reindex* are no-ops,
see:
portal.reindexObject*.__module__ in debug shell (Implementation is Products.CMFPlone.Portal.PloneSite)


Do we target plone-4.x or plone-5.x?
I vote for the later, since a lot of code has change wrt calls to reindexObjectSecurity
This does, of course, have consequences for plone.intranet.

experimental.localrolesindex testing on plone 4 + plone 5
----------------------------------------------------------
In my testing of my branch oft MattH's latest commit (b94df8482a87172492c6383e6a7a90c5fa8b08f2):

plone 4 +  5 (see buildout config herewith: plone5.cfg):
 
  Javascript errors in sharing tab have thwarted in my attempts to test this effectively.

  Does work::

    - removing initial kw index for ARU in ZMI
    - installing the new LocalRolesIndex in ZMI and reindexing all content

  What does not work::
    
    - re-starting the server and doing anything with local roles (ZMI, sharing)
    - shadowtree does not contain the correct ids (None's)


Where to implement index optimisation?
--------------------------------------
At time of writing, experimental.localrolesindex tries to do the optimisation in
an index. 

Whilst I think the algorithm ('deciding whether indexing is required based on hash of local roles)
and mechanism ('shadowtree') are good starting point, 
I think the site where we are currently implementing this (i.e a kw index subclass) is not the right place.

Why?
Because in order to index descendants, we need to selectively wakeup objects from the site's content tree (ZODB),
and doing so requires calling:

  - index.(un)restrictedTraverse

Note that we cannot use plone.api.content.get in the index, since a site may be using a catalog other than the 
global portal_catalog.
Thus our only way of getting at the catalog which our index is seated in is to use aquistion.

It 'feels' wrong for the index to be acquiring its parent catalog and using that in order to retrieve an indexable
version of the object it's traversing to.
In fact, it just feels wrong for the index itself to be traversing to content.

------------------------------
Possible alternative solutions
------------------------------

1. Implement an adapter for the context of reindexObjectSecurity calls
----------------------------------------------------------------------

The sharing view (plone.app.worflow.browser.sharing.SharingView) is
the only *view* in plone which invokes reindexObjectSecurity, which is the call we want
to change the behaviour of in order to do the optimisation.

ler All the call sites of `reindexObjectSecurity`:

:find-command:

  find omelette/ -type f -follow -not -name 'test_*' -name '*.py' -exec grep -HnE '[a-z]+\.reindexObjectSec' {} \;

:find-results:
  file, match, (comment, context-needs-wrapping-in-proposed-adapter)
  omelette/Products/CMFPlone/PloneTool.py:878:        obj.reindexObjectSecurity() (caller = acquireLocalRoles, doesn't appear to be used anymore, 0)
  omelette/Products/CMFCore/WorkflowTool.py:639:            ob.reindexObjectSecurity() (caller = _notifyCreated, 1)
  omelette/Products/CMFCore/MembershipTool.py:446:            obj.reindexObjectSecurity() (caller = setLocalRoles,  1)
  omelette/Products/CMFCore/MembershipTool.py:466:            obj.reindexObjectSecurity() (caller = deleteLocalRoles, 1)
  omelette/plone/app/workflow/browser/sharing.py:109:                self.context.reindexObjectSecurity() (caller = handle_form, 1)
  omelette/plone/app/workflow/browser/sharing.py:549:            context.reindexObjectSecurity() (caller = update_inherit, 1)
  omelette/plone/app/workflow/browser/sharing.py:606:            self.context.reindexObjectSecurity() (caller = update_role_settings, 1)
  omelette/plone/app/iterate/subscribers/workflow.py:61:    event.working_copy.reindexObjectSecurity(et) (caller = handleCheckout, 1)


Provide an adapter which adapts the `context` in each case where
context-needs-wrapping-in-proposed-adapter to something like the following:

 :code-block: python

class IARUIndexOptimiser(zope.interface.Interface):
    """Marker."""


@zope.interface.implementer(ICatalogAware, IARUIndexOptimiser) # ICatalogAware covers DX and AT
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
    	# implemenation a la experiemental.localrolesindex.localrolesindex.LocalRolesIndex.index_object
    	...
	

For the sharing view, provide a subclass of plone.app.workflow.browser.sharing.SharingView
which adapts the context to be LocalRolesIndexingOptimiser and
configure this via an overrides.zcml in our product, which overrides plone.app.workflow.browser.configure.zcml:

:code-block: python

class SharingView(plone.app.workflow.browser.sharinga.SharingView):
  
   def __init__(self, context, request):
       context = ILocalRolesSharingOptimiser(context, context)
       super(SharingView, self).__init__(context, request)

   # The rest of implementation is same as subclass's.
   # subclass behaviour alterted because self.context will be a LocalRolesIndexingOptimiser if
   # the adapter has been registered.

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






 

    
