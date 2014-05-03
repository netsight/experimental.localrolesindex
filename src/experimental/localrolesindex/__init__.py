from . import localrolesindex


def initialize(context):
    context.registerClass(
        localrolesindex.LocalRolesIndex,
        permission='Add Pluggable Index',
        constructors=(
            localrolesindex.manage_addLocalRolesIndexForm,
            localrolesindex.manage_addLocalRolesIndex
        ),
        visibility=None
    )
