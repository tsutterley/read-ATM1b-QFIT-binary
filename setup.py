from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='read-ATM1b-QFIT-binary',
    version='1.0.0.7',
    description='Reads Level-1b Airborne Topographic Mapper (ATM) QFIT binary data products',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/tsutterley/read-ATM1b-QFIT-binary',
    author='Tyler Sutterley',
    author_email='tsutterl@uw.edu',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Physics',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='NSIDC IceBridge ILATM1b ILNSA1b',
    packages=find_packages(),
    install_requires=['numpy','h5py','lxml','future'],
    scripts = ['nsidc_convert_ILATM1b.py']
)
