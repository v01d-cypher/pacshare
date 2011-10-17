from setuptools import setup, find_packages
import sys, os

version = '0.0'

setup(name='pacshare',
      version=version,
      description="Share pacman repositories on LAN",
      long_description="""\
      Allows sharing of packages between multiple clients on a LAN with zero configuration.
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Nevar',
      author_email='psi.neamf@gmail.com',
      url='',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points = {
          'console_scripts': [
              'xferclient = pacshare.xferclient:main',
          ],
        },
      )
