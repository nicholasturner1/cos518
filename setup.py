from setuptools import setup

setup(name='memail',
      version='0.04',
      description='Personalized Email Project for COS518',
      url='http://github.com/nicholasturner1/cos518',
      author='Nicholas Turner, Yuanzhi Li, Paul Jackson',
      author_email='nturner.stanford@gmail.com',
      license='MIT',
      packages=['memail'],

      install_requires=[
      'numpy==1.10.1',
      'scipy==0.16.0',
      'gensim',
      'nltk',
      'sklearn==0.16.1',
      'pip-autoremove'
      ],

      scripts=[
      'memail/bin/uninstall-memail.sh',
      'memail/bin/prepare-memail.py',
      'memail/bin/run-memail.py'],

       include_package_data=True)
