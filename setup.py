from setuptools import setup

setup(name='itop2inventory',
      version='1.6',
      description='Make itop an inventory for ansible',
      url='https://github.com/support-capensis/itop2ansible.git',
      author='support-capensis',
      author_email='support@capensis.fr',
      license='MIT',
      packages=['itop2inventory'],
      install_requires=[
          'requests',
          'configparser'
      ],
      data_files=[('/etc/itop2inventory', ['config.ini']),
                  ('/usr/local/sbin', ['itop-inventory'])
                  ],
      include_package_data=True,
      zip_safe=False)