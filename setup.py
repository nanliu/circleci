from setuptools import setup

install_requires = []

with open('requirements.txt', 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            install_requires.append(line)

setup(
    name='circleci',
    version='0.1',
    description='CircleCI helpers',
    long_description=open('README.md').read(),
    author='Nan Liu',
    license='License :: Apache2',
    scripts=[
        'bin/build_container',
        'bin/circleci_namespace_gc',
        'bin/circleci_trigger',
        'bin/gh_status',
        'bin/integration',
        'bin/digests_to_custom_values',
    ],
    packages=['circleci'],
    include_package_data=True,
    install_requires=install_requires)
