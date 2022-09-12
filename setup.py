import re
from setuptools import setup


def get_module_var(varname):
    regex = re.compile(fr"^{varname}\s*\=\s*['\"](.+?)['\"]", re.M)
    mobj = next(regex.finditer(open("voodoodal/__init__.py").read()))
    return mobj.groups()[0]


__author__ = get_module_var('__author__')
__license__ = get_module_var('__license__')
__version__ = get_module_var('__version__')


setup(
    name="voodoodal",
    version=__version__,
    url="https://github.com/valq7711/voodoodal",
    license=__license__,
    author=__author__,
    author_email="valq7711@gmail.com",
    maintainer=__author__,
    maintainer_email="valq7711@gmail.com",
    description="voodoodal - model builder for pydal",
    long_description="voodoodal - model builder for pydal",
    long_description_content_type='text/plain',
    platforms="any",
    keywords='python pydal autocomplete',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    install_requires=[
        "pydal",
    ],
    python_requires='>=3.7',
    packages=['voodoodal'],
)
