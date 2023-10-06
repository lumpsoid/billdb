#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='billdb',
    version='0.1',
    packages=find_packages(),
    install_requires=[  #dependecies
        'requests',
        'lxml',
    ],
    extras_require={
        'api': [  # Optional dependency for the API feature
            'Flask',
            'gunicorn'
        ],
        'telegram': [  # Optional dependency for the telegram-bot feature
            'python-telegram-bot'
        ],
    }
)
