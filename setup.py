import setuptools

# TODO: Replace <sun_template> with your repo name

setuptools.setup(
    name='<sun_module>',
    version='0.0.1',
    packages=setuptools.find_packages(),
    test_suite="tests",
    url='https://github.com/SunriseProductions/<sun_module>',
    install_requires=[
        '<repository_name> @ git+ssh://git@github.com/SunriseProductions/<repository_name>',
        'sun_api @ git+ssh://git@github.com/SunriseProductions/sun_api'  # e.g.
    ],
    license='',
    author='Sunrise Productions',
    author_email='tech@sunrise.co.za',
    description='Template repo for use at Sunrise Productions'
)
