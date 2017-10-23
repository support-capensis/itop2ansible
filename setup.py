from setuptools import setup

setup(name='itop2inventory',
      version='0.1',
      description='Make itop an inventory for ansible',
      url='https://github.com/support-capensis/itop2ansible.git',
      author='Gregory OToole',
      author_email='gotoole@capensis.fr',
      license='MIT',
      packages=['itop2inventory'],
      install_requires=[
          'requests',
          'configparser'
      ],
      zip_safe=False)