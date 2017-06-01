try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Utility scripts for working with USAspending bulk downloads.',
    'author': 'Becky Sweger',
    'url': 'https://github.com/bsweger/usaspending-scripts',
    'download_url': 'https://github.com/bsweger/usaspending-scripts',
    'version': '0.1',
    'install_requires': ['pytest', 'requests', 'pandas', 'pyquery', 'click', 'us'],
    'packages': ['usaspending'],
    'scripts': [],
    'name': 'USAspending-scripts',
    'entry_points': {
        'console_scripts': [
            'usaspending_assistance = usaspending.usaspending_assistance:usaspending_assistance',
            'usaspending_contracts = usaspending.usaspending_contracts:usaspending_contract'
        ]
    }
}

setup(**config)
