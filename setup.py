from setuptools import setup, find_packages


with open("README.rst", 'r') as f:
    long_description = f.read()


setup(
   name='ccam_prospect',
   version='1.2.2',
   description='calibrate raw ccam files to rad and ref files',
   long_description=long_description,
   author='Colleen O\'Shea',
   author_email='colleen.oshea@jhuapl.edu',
   packages=['ccam_prospect', 'ccam_prospect.utils', 'ccam_prospect.constants', 'ccam_prospect.sol76', 'ccam_prospect.templates'],
   package_data={'ccam_prospect': ['constants/*', 'sol76/*', 'templates/*']
   },
   install_requires=['numpy', 'jinja2', 'matplotlib'],
)
