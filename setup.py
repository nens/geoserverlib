from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='geoserverlib',
      version=version,
      description="GeoServer Python client library",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='geoserver python',
      author='Sander Smits',
      author_email='sander.smits@nelen-schuurmans.nl',
      url='',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'requests'    
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
