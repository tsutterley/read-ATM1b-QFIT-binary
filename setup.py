from setuptools import setup, find_packages
setup(
	name='read-ATM1b-QFIT-binary',
	version='1.0.0.5',
	description='Reads Level-1b Airborne Topographic Mapper (ATM) QFIT binary data products',
	url='https://github.com/tsutterley/read-ATM1b-QFIT-binary',
	author='Tyler Sutterley',
	author_email='tsutterl@uw.edu',
	license='MIT',
	classifiers=[
		'Development Status :: 3 - Alpha',
		'Intended Audience :: Science/Research',
		'Topic :: Scientific/Engineering :: Physics',
		'License :: OSI Approved :: MIT License',
		'Programming Language :: Python :: 2',
		'Programming Language :: Python :: 2.7',
	],
	keywords='NSIDC IceBridge ILATM1b ILNSA1b',
	packages=find_packages(),
	install_requires=['numpy','h5py','lxml','future'],
)
