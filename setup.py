from setuptools import setup

setup(name='memail',
      version='0.01',
      description='Personalized Email Project for COS518',
      url='http://github.com/nicholasturner1/cos518',
      author='Nicholas Turner, Yuanzhi Li, Paul Jackson',
      author_email='nturner.stanford@gmail.com',
      license='MIT',
      packages=['memail'],

      install_requires=[
      'numpy',
      'scipy',
      'gensim',
      'nltk',
      'sklearn',
      'pip-autoremove'
      ],

      scripts=[
      'memail/bin/uninstall-memail.sh',
      'memail/bin/prepare-memail.py',
      'memail/bin/run-memail.py'],

       include_package_data=True)
