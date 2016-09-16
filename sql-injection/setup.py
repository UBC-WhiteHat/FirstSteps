from setuptools import setup, find_packages

setup(
    name='sql_injection_server',
    packages=find_packages(),
    install_requires=[
        'py-postgresql',
    ],
    entry_points: {
        'console_scripts': [
            'sql_injection_server=sql_injection_server:main',
        ]
    }
)
