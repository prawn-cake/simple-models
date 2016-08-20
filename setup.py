from setuptools import setup

setup(
    name='simple-models',
    version='0.5.0',
    packages=['simplemodels'],
    install_required=['six==1.9.0'],
    url='https://github.com/prawn-cake/simple-models',
    license='MIT',
    author='Maksim Ekimovskii',
    author_email='ekimovsky.maksim@gmail.com',
    description='Library for building declarative dict-like structures to get '
                'more power and safety in your API applications',
    classifiers=[
        'Intended Audience :: Developers',

        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
    ]
)
