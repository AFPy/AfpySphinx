from setuptools import setup, find_packages

version = '0.1.0'

setup(
    name='AfpySphinx',
    version=version,
    description="Some documents published on www.afpy.org",
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    install_requires=[
      "sphinx",
      "pyquery",
    ],
)
