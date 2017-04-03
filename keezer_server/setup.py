from setuptools import setup

setup(
	name='keezer_server',
	packages=['keezer_server'],
	include_package_data=True,
	install_requires=[
		'flask',
	],
	setup_requires=[
		'pytest-runner',
	],
	tests_require=[
		'pytest',
	],
)
