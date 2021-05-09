import re
from setuptools import setup

import voodoodal

setup(
    name="voodoodal-Val",
    version=voodoodal.__version__,
    url="https://github.com/valq7711/voodoodal",
    license=voodoodal.__license__,
    author=voodoodal.__author__,
    author_email="valq7711@gmail.com",
    maintainer=voodoodal.__author__,
    maintainer_email="valq7711@gmail.com",
    description="voodoodal",
    py_modules=['voodoodal'],
    platforms="any",
    scripts=['voodoodal.py'],
    keywords='pydal python autocomplete',
    classifiers=[
        "Development Status :: 1 - Planning",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires='>=3.6',
)
