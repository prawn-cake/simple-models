Changelog
=========

0.6.2 (2019-06-17)
--------------------
* Loose requirements versions

0.6.1 (2017-06-11)
--------------------
* [Bugfix] #24: Prevent to create an instance of document with ALLOW_EXTRA_FIELDS enabled and which has overlapping data keys it gets

0.6.0 (2017-06-04)
------------------
* [Improvement] Clearer interface for the ListField, it ignores user 'validators' parameter
* [Breaking] Change `Document's` `__init__` signature: move attributes from `**kwargs` to `data`, add additional `**kwargs`.
* [Breaking] Remove dictionary as a storage from `Document`.

0.5.2 (2016-10-31)
------------------
* [Improvement] Improve Document.create(...) method robustness

0.5.1 (2016-10-01)
------------------
* [Feature] Support ListField having only one type of items + added MutableSequence interface
* [Improvement] MutableMapping interface for the DictField
* [Bugfix] ListField of Documents returns proper documents instances (https://github.com/prawn-cake/simple-models/issues/13)

0.5.0 (2016-08-20)
------------------
* [Improvement] Protected fields interface via Document.create(...)
* [Improvement] Added ListField list of Documents support
* [Improvement] DocumentField: added lazy model assignment with name

0.4.1 (2016-06-01)
------------------
* [Bugfix] Fix OMIT_MISSED_FIELDS behavior
* [Improvement] Follow consistency and raise ValidationError instead of ValueError on choices validation if failed

0.4.0 (2016-04-08)
------------------
* [Feature] Implemented Document.Meta AttributeDict based options
* [Improvement] Renamed Meta.OMIT_NOT_PASSED_FIELDS -> Meta.OMIT_MISSED_FIELDS
* [Feature] Post-init model validation
* [Feature] New DictField

0.3.7 (2015-12-11)
------------------
* New SimpleField required attribute handling (moved to validate() method)
* Implemented documents multiple inheritance
* More wise fields descriptors setters strategy on init and on __setattr__
* Split up SimpleField validation chain into several steps to adapt it
* for better overriding in case of inheritance (cleaner ListField
* implementation)

0.3.6 (2015-12-11)
------------------
* Fixed OMIT_NOT_PASSED_FIELDS to work with defaults
* Updated SimpleField.required attribute handling;
* Implemented models inheritance, refactoring DocumentMeta class;
* Significant improvements in SimpleField.validate method - divide it into composition methods;

0.3.5 (2015-12-10)
------------------
* Fixed CharField max_length validator; fixed AttributeDict setter
* Use common SimpleField value setter for descriptors and for Document init.
* Updated CharField, forbid to store None value, store '' instead; Simplified Document init

0.3.4 (2015-12-09)
------------------
* Implemented Document.IGNORE_NONE_ON_INIT feature.
* Code clean up and minor fixes

0.3.3 (2015-11-26)
------------------
* Allow None values for non required fields. [Maksim Ekimovskii]
* Code refactoring: moved helpers to utils.py, removed helpers.py, minor

0.3.2 (2015-10-10)
------------------
* Implement ListField, make it json serialize compatible for python2/3; Fixed

0.3.1 (2015-10-09)
------------------
* Initialize callable default values at document init point; Added new
* Implemented ListField, added tests; Forbid mutable default parameters;

0.3.0 (2015-09-27)
------------------
* Implemented choices feature, removed redundant code, updated tests and

0.2.5 (2015-09-19)
------------------
* Implemented ALLOW_EXTRA_FIELDS document attribute; Improve python 3
* Fixed README. [Maksim Ekimovskii]
* Implemented new validators pipeline; Added new immutable field option;
* Validate model defaults; Fixed working with nested models; Added
* Replace SimpleField get_name() with property name. [Maksim Ekimovskii]
* Remove get_instance constructor; Fixed tests. [Maksim Ekimovskii]
* Code refactoring, remove deprecated type parameter from SimpleField;

0.2.4 (2015-04-25)
------------------
* Implemented new feature - optional SimpleField name; Added tests;
* Exception refactoring. [Maksim Ekimovskii]
* Added new field attribute 'error_text' to help to debug validation
* Fixed DictEmbeddedDocument set default functionality + validation;
* Integrate six lib to python 2 to 3 compatibility. [Maksim Ekimovskii]

0.2.1 (2015-02-12)
------------------
* Updated docs; added test_coverage make commandl updated travis cfg.
* Added new SimpleField validator feature -> it will be replace 'type'
* Added strip_kwargs method for DictEmbeddedDocument. [Maksim
* Models refactoring, improve readability; added .coveragerc. [Maksim
* Rename _type -> type SimpleField attribute. [Maksim Ekimovskii]
* Fix DictEmbeddedDocument type casting; Updated tests; Updated
* Updated validators, integrate it to field setter and document
* Rewritten field storage logic to prevent memory leaks, store all

