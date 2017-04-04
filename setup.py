from setuptools import setup, find_packages

setup(name='powerDNSAdmin',
      version='1.0.0',
      description='PowerDNS admin UI',
      url='https://github.com/ngoduykhanh/PowerDNS-Admin/',
      author='Khanh Ngo',
      author_email='ngokhanhit@gmail.com',
      license='MIT',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False)
