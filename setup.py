from setuptools import setup

setup(
    name='MongoSchemaImportExport',
    version='0.2',
    packages=['mongo_import_export_schema'],
    license='Creative Commons Attribution-Noncommercial-Share Alike license',
    description='Import and export metadata about mongodb databases and collections',
    classifiers=[
        "Programming Language :: Python",
    ],
    author="Jonathan Mackenzie",
    url="https://github.com/jonnoftw/mongo_import_export_schema",
    keywords=["pymongo mongodb schema import export"],
    long_description=open('README.md').read(),
    requires=['pymongo'],
    entry_points={
        'console_scripts': [
            'mongo-schema-export=mongo_import_export_schema.mongo_schema_export:main',
            'mongo-schema-import=mongo_import_export_schema.mongo_schema_import:main'
        ]}
)
