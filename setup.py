from setuptools import setup, find_packages


with open("README.rst", 'r') as f:
    long_description = f.read()


setup(
   name='ccam_calibration',
   version='0.5.1',
   description='calibrate raw ccam files to rad and ref files',
   long_description=long_description,
   author='Colleen O\'Shea',
   author_email='colleen.oshea@jhuapl.edu',
   packages=['ccam_calibration', 'ccam_calibration.utils'],
   install_requires=['numpy', 'jinja2', 'matplotlib'],
)
