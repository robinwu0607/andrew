"""A setuptools based setup module.

See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
from os import path, walk, listdir

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Get requirements list.
with open(path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    requirement_list = f.read().splitlines()

data_files = []
for root, _, files in walk(path.join(here, 'andrew/web/gui')):
    # print(root)
    for f in listdir(root):
        if '.gitignore' in f:
            continue
        if path.isfile(path.join(root, f)):
            data_files.append(path.join(root, f))

# print(data_files)

setup(
    name='andrew',  # Required
    version='0.0.1',  # Required
    description='Andrew - Paramiko based Remote Execution',  # Optional
    long_description=long_description,  # Optional
    url='https://github.com/',  # Optional
    author='Robin Wu',  # Optional
    author_email='robinwu.qw@gmail.com',  # Optional
    classifiers=[  # Optional
        'Development Status :: 5 - Production/Stable',
        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Maintenance Tools',
        'Topic :: Functional Testing :: Platform',
        # Pick your license as you wish
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='Paramiko Fabric Ansible',  # Optional
    packages=find_packages(exclude=['docs', 'tests']),  # Required
    include_package_data=True,
    platforms='Linux',
    python_requires='>=3.6.5',
    install_requires=requirement_list,  # Optional
    data_files=data_files,  # Optional
)

# python3 setup.py bdist_wheel
