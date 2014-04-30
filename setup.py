##############################################################################
#
# Copyright (c) 2014 Netsight Internet Solutions
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

from setuptools import setup, find_packages

setup(name='experimental.localrolesindex',
      version = '0.1dev',
      url='https://github.com/wengole/experimental.localrolesindex',
      license='ZPL 2.1',
      description='Efficiently index local roles in a ZCatalog',
      author='Netsight Internet Solutions',
      author_email='dev@netsight.co.uk',
      long_description=open('README.rst').read() + '\n' +
                       open('CHANGES.rst').read(),
      packages=find_packages('src'),
      namespace_packages=['experimental'],
      package_dir={'': 'src'},
      install_requires=[
        'setuptools',
        'AccessControl',
        'Acquisition',
        'transaction',
        'Persistence',
        'zExceptions',
        'ZODB3',
        'Zope2 >= 2.13.0dev',
        'zope.interface',
        'BTrees',
      ],
      include_package_data=True,
      zip_safe=False,
      )