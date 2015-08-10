==============
Coding Trytond
==============

This page discusses a sample of the Trytond coding idioms available.

Models and Fields
=================

See also `official model documentation`_, `unofficial model documentation`_.

In Trytond, ModelSQL classes correspond to database tables, and Fields, when
used as attributes of ModelSQL classes, correspond to columns of the table.
For example (simplified from the standard ``Party`` module):

::

  class Party(ModelSQL, ModelView):
      "Party"
      __name__ = 'party.party'

      name = fields.Char('Name')
      lang = fields.Many2One("ir.lang", 'Language')
      code_readonly = fields.Function(fields.Boolean('Code Readonly'),
          'get_code_readonly')

When a `database update`_ is performed, the system goes through all of the
ModelSQL classes registered to the Pool and makes sure that all of the tables
and columns that are supposed to be there are present.  (But it does not check
further characteristics of columns or tables--requiring some updates to be
manually specified using the ``__register__`` method of ModelSQL.

Fields
------

The many types and attributes of Fields are not covered here, but are available
in the `official fields documentation`_.


Migrations with __register__
============================

Database modifications other than adding tables and columns must be manually
address through overriding the ``__register__`` method of the relevant class.
Many migrations can be accomplished using Trytond's built-in ``TableHandler``
class, the capabilities of which are set out in docstrings of the
``TableHandlerInterface`` class of ``trytond/backend/table.py``.  What
``TableHandler`` cannot achieve can be done with either:

::

  Transaction().cursor.execute([arbitrary SQL])

or 

::

  Transaction().cursor.execute(cls.__table__().[a method call])

Any ``__register__`` function must also call the senior-class's
``__register__``, using

::

  super(AClassName, cls).__register__(module_name)

The ``super`` call may occur before, after, or among other table/column
modifying calls, depending whether it is those modifications should be done
before or after the the automatic ``__register__`` action of creating tables
and/or columns that the Python code requires, but that are missing from the
database.

An example of ``__register__`` to remove the ``required`` constraint from a
field is:

::

   @classmethod
   def __register__(cls, module_name):
        super(AClassName, cls).__register__(module_name)

        TableHandler = backend.get('TableHandler')
        cursor = Transaction().cursor
        table = TableHandler(cursor, cls, module_name)

        table.not_null_action(the_field_name, action='remove')


Modules
=======

See also the `official module documentation`_ and `unofficial module documentation`_.

Modules have the following characteristics:

  #. A tryton.cfg file, which is a simple file that: (1) states the version of
     Trytond the modules is written for; (2) lists the other modules the
     module depends on; (3) lists the XML files contained in this module
     (which define model instances that get automatically written to the
     database as part of the module base configuration).  The files look like:

     ::

       version=[version number]
       depends:
           one
           module
           per
           line
       xml:
           a_file.xml
           another_file.xml

  #. An __init__.py file, which serves to register each Class that is one of
     the three object types with the Pool.  The code is uninventive and
     follows this pattern:

     ::

       from trytond.pool import Pool

       # now go through all the .py files in your modules and import each Class
       from my_python_file import (  # repeat for all your files
           AClass, AnotherClass
       )

       def register():
           """
           The register function calls Pool.register 3 times (once each for
           models, reports, and wizards.  The arguments to Pool.register are
           (1) the classes passed positionally (and in the correct
           order--you cannot register one unless its dependencies are
           already registered); (2) keyword argument, module='module_name',
           and (3) keyword argument type_='object_type' (ie, model, wizard
           or report.
           """

           Pool.register(
               List,
               All,
               The,
               Classes,
               Of,
               That,
               Type,
               modules='my_module', type_='model'  # or type_='report' or 'wizard'
           )
           # add two more calls of Pool.register.

  #. A setup.py file (preferred but not strictly necessary).  A template
     setup.py for Trytond modules is `provided here`_.  Local modules that are
     not distributed on PyPi_ can be installed using setup.py by navigating to
     the parent folder of the modules and running

     ::

       pip install [-e] modulename/  # trailing slash for local-folder
       # -e option makes the code editable, good for development

Domains and PYSON: Retreiving and Filtering Records
===================================================

See `official domain documentation`_, `unofficial domain documentation`_,
`official PYSON documentation`_.

Domains provide a concise language for retrieving and filtering instances of
ModelSQL.  A domain is a list of tuples, each having three elements, as
follows:

::

  ('field_name', 'operator', 'operand')

There is an implied ``and`` between each of the tuples, meaning that an
instance meets the domain only if it satisfies each tuple.  However, this can
be overridden to specify that some tuples have an ``or`` relationship.

``field_name`` refers to a field on the model being searched by the domain.
``operator`` is any of a large set of operators in the documentation.  Any of
the three elements could, instead of a string, be a PYSON expression that
evaluates to a string.  An example of a simple domain is:

::

  [('first_name', '=', 'Fred')]

This would retrieve all instances whose ``first_name`` field is "Fred".  If
``field_name`` is a relational field, then the fields of that relational field
can be references through ``.`` notation, to arbitrary depth.  E.g.,
``field_name.associated_field.attribute``.

The true power of domains, however, is not apparent until they are used with
PYSON.  PYSON is another language, distinct from domains, that evaluates an
expression against the current evaluation context, allowing for dynamic
injection of values into domains.  For a typical use case of a domain with
PYSON, assume that a you are modeling a customer referral service that has
models ``Customer``, ``Vendor``, and ``Service``.  Each ``Customer`` is in need
of a particular ``Service`` (stored in a ``service`` field), and each
``Vendor`` provides a particular ``Service`` (stored in a ``service_provided``
field) .  ``Customer`` has a ``Vendor`` field, indicating what ``Vendor`` they
were referred to.  By adding the following domain to this ``Vendor`` field,
you can restrict the options for ``Vendors`` to only those that provide the
``Service`` needed by that ``Customer``.

::

  [('service_provided', '=', trytond.pyson.Eval('service')]

By doing this, the PYSON expression will look at the ``service`` field of the
``Customer``, and feed it to the domain, which will then restrict the
``Vendors`` selection to those who ``service_provided`` field matches the
requirement.

As a debugging tool, it is helpful to examine what a PYSON expression will
return, given a particular evaluation context.  This can be done interactively,
as follows:

::

  def PYSON_tester(psyon_expression, context):
    from trytond.pyson import PYSONDecoder, PYSONEncoder
    encoded_pyson = PYSONEncoder().encode(pyson_expression)
    return PYSONDecoder(context).decode(encoded_pyson)

In the above example, ``pyson_expression`` would be
``trytond.pyson.Eval('service')``, while ``context`` would be a dictionary
passed to the function to simulate the evaluation context.

Validate, Errors and Warnings
=============================

Any ModelSQL call may define a ``validate`` method to establish a specification
that records must meet.  ``validate`` will automatically be called when any
record is saved, and should be written as:

::

    @classmethod
    def validate(cls, records):
        # always call parent class's validate
        super(ClassName, cls).validate(records)

        for rec in records:
            if fails_my_test(rec):
                cls.raise_user_error('an_error')
                # or raise_user_warning

Errors and Warnings
-------------------
All models and wizards inherit are subclasses of
``trytond.error.WarningErrorMixin``.  As a result, each model class has an
``_error_messages`` attribute, which is a dictionary of ``[error name]:
[display message for user]``.  Developers may create custom errors by adding to
this dictionary.  Because this is a case of altering, but not totally
overriding, an attribute of a parent class, it should be done in the new
model's ``__setup__`` method.  For example:

::
   
    @classmethod
    def __setup__(cls):
        super(ClassName, cls).__setup__()
        cls._error_messages.update({'custom_error': 'Custom Message'})

When calling ``raise_user_error`` (or ``warning``), you must pass the name of
the error, and may also pass further clarifying information.  The custom
message can be written to include string formatting signifiers, which can be
filled in with additional arguments passed.  See `official error
documentation`_.  Warnings differ from errors in that the user has the option
to ignore them.
        

System users and access permissions
===================================
See `unofficial access-control documentation`_. 


Automatic Interactions to Change Fields
=======================================

Sometimes we want a change in one field to cause another field to change.
Trytond allows this with ``on_change_[fieldname]`` and
``on_change_with_[fieldname]``. 
See `official on_change[_with] documentation`_,
`unofficial on_change[_with] documentation`_.  (Note: syntax in this area
changed significantly between Tryton 3.0 and 3.2.)

Dynamic Field Attributes
========================

Fields have these attributes, which all default to ``False``: ``readonly``
(must be filled-in to save), ``readonly`` (cannot be written), and ``hidden`` (
not shown in the user interface).  These attributes can be set either
statically, as in:

.::

  name = fields.Char('Name', required=True)

or dynamically, as in:

::

  from trytond.pyson import Bool, Eval
  name = fields.Char('Name', states={
      'required': Bool(Eval('foo'))
  }

``Eval`` looks at the current EvaluationContext and determines the value of
``foo``, and ``Bool`` reduces that value to a Boolean, thus establishing
whether the field ``name`` is ``required`` in that particular situation.

.. _`unofficial module documentation`: http://tryton-documentation.readthedocs.org/en/latest/developer_guide/example_library_1.html#module-structure
.. _`official module documentation`: http://doc.tryton.org/3.6/trytond/doc/topics/modules/index.html#topics-modules
.. _`provided here`: https://hg.tryton.org/tryton-tools/file/tip/contrib-module-setup.tmpl
.. _`official model documentation`: http://doc.tryton.org/3.2/trytond/doc/topics/models/index.html#topics-models
.. _`unofficial model documentation`: http://tryton-documentation.readthedocs.org/en/latest/developer_guide/basic_concepts.html#pool 
.. _`database update`: https://code.google.com/p/tryton/wiki/Update
.. _`official fields documentation`: http://doc.tryton.org/3.2/trytond/doc/ref/models/fields.html#ref-models-fields
.. _PyPi: https://pypi.python.org/pypi
.. _`official domain documentation`: http://doc.tryton.org/3.2/trytond/doc/topics/domain.html?highlight=domain
.. _`unofficial domain documentation`: http://tryton-documentation.readthedocs.org/en/latest/developer_guide/domains.html?highlight=domain
.. _`official PYSON documentation`: http://doc.tryton.org/3.2/trytond/doc/ref/pyson.html?highlight=pyson
.. _`unofficial access-control documentation`: http://tryton-documentation.readthedocs.org/en/latest/installation_configuration/access_management.html?highlight=access
.. _`official error documentation`: http://doc.tryton.org/3.2/trytond/doc/ref/models/models.html?highlight=user_error#trytond.model.Model.raise_user_error
.. _`unofficial on_change[_with] documentation`: http://tryton-documentation.readthedocs.org/en/latest/developer_guide/example_library_2.html?highlight=on_change
.. _`official on_change[_with] documentation`: http://doc.tryton.org/3.2/trytond/doc/topics/models/fields_on_change.html?highlight=on_change
