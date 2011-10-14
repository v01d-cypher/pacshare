from setuptools import setup, find_packages
import sys, os

version = '0.0'

setup(name='pacshare',
      version=version,
      description="Share package repositories on LAN",
      long_description="""\
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
              'pacshare_xferclient = pacshare.xferclient:main',
          ],
        },
      )
