class Dummy(object):

    def __init__(self, path, local_roles, local_roles_block=False):
        self.path = path
        self.aru = local_roles
        self.__ac_local_roles_block__ = local_roles_block
        self.id = path.split('/')[-1]

    def __str__(self):
        return '<Dummy: %s>' % self.id

    __repr__ = __str__

    def getId(self):
        return self.id

    def getPhysicalPath(self):
        return tuple(self.path.split('/'))

    def allowedRolesAndUsers(self):
        return self.aru


