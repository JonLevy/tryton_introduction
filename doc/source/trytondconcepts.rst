================================
Tryton Daemon (Trytond) Concepts
================================

The Trytond kernel provides a framework for modeling objects of interest to the
programmer in Python and storing them in a database.  The framework
makes common needs for handling instances of these objects easy through idioms
described in the official documentation_, and `unofficial documentation`.

Understanding the ideas described in this page makes learning the practical
details of the Tryton daemon easier.

Object Types, Modules, the Pool, Inheritance, and __setup__
===========================================================

Object Types
------------

Trytond establishes three types of objects: models, reports, and wizards.

Models typically represent the real-world things the particular Trytond
implementation is written to keep track of.  E.g., an implementation for a car
dealership might have models such as: car, salesman, customer, etc.  There are
two important subclasses of ``Model``: ``ModelSQL`` (used to persist data to
the database), and ``ModelView`` (any model that will will render a graphical
view).  Almost all models used in implementations multiply inherit from both
ModelSQL and ModelView.  Exceptions include: (1) certain windows (typically used
in wizards) present fill-in-form views where inputs guide the execution of the
wizard are not stored to the database, and thus only inherit from
``ModelView``), but guide the execution of the wizard; and (2) intersection
models used to support a Many2Many relation, which do not need to be displayed
to the user and, thus, typically only inherit from ``ModelSQL``.
 
Reports are templates in the Open Document format that are used to generate
documentary reports for users.  Wizards are used to guide users through
step-by-step procedures.

The three object types follow a similar class definition requirement.  For
example:

::

  class AModel(ModelSQL, ModelView):
      """Docstrings are mandatory"""

      __name__ = 'my_module.a_model'  # __name__ is required; follows 
                                      # this convention.
      [snip]


Modules
-------

Trytond is designed to be highly extensible through modules, which are Python
packages that define Trtyond new objects and/or enhance objects defined in
other modules.

The Pool
--------

The Pool functions as a dictionary from which Classes are retrieved by their
__name__ attribute (ie, the dictionary entries are [class __name__]:[class
object]).  This means that, in Tryton, when you want to work with a
class object, you use a different syntax than Python standard.

::

  # Python standard syntax NOT FOR TRYTON
  from a_module import AClass

  # The Tryton way
  from trytond.pool import Pool
  AClass = Pool().get('a_module.a_class')

Pool can take a database name as an optional argument, although this is
rarely used because the default value is the database of the current
Transaction, which is almost always the desired behavior.

Inheritance
-----------

The structure of its modules, and the implementation of the Pool, allow Trytond
to use a unique, and very powerful, idiom for inheritance.

When a class is registered to the Pool (in ``__init__.py``), Trytond checks to see
if an entry already exists for the class's ``__name__``.  If it does, then Trytond
creates a new class which multiply inherits from existing class object in the
Pool, and the new class object being registered, and replaces the value with
that new class.  This means that (within the three Trytond object types) any
two classes (typically from different modules) with the same ``__name__``
attribute become joined in a single class.  An optional idiom for identifying a
class as extending an existing model is to declare that class using Python 2
old-class syntax (which is the same as Python 3 syntax), e.g., ``AClass:``
rather than ``AClass(object):``.  In order for this to work, the class's
metaclass must be set to ``PoolMeta``, so as to make it loadable in the Pool.
Often ``PoolMeta`` is set at the module level.

This overcomes obstacles that the normal Python inheritance approach poses for
extensibility through modules.  For example, a widely used module defines the
class ``Party``, with the ``__name__`` ``party.party``.  If two separate modules both
depend on party and extent the Party class (by adding attributes to it), then,
from the point of view of traditional Python inheritance, the two dependent
modules have created two separate classes.  In order to make Party a single
class again, one would need to edit one of the two modules to inherit from the
other, rather than directly from ``Party``.  Trytond inheritance, however, avoids
this problem, making it extremely easy to share modules among developers.  

Modifying Inherited Attributes with __setup__
---------------------------------------------

It is often desirable for an inheriting class to modify, but not totally
overwrite, an attribute of its parent class (or, in the case of Trytond-style
inheritance, its more senior sibling/s).  For method attributes, Tryton uses
Python's built-in super_ function to achieve this goal.  For non-method
attributes, however, the idiom for Tryton models is to place these modification
in a ``__setup__`` method.  For example:

::

  @classmethod
  def __setup__(cls):
      super(Attachment, cls).__setup__()
      cls.an_attribute.update({'new': 'value'})

Tryton runs each model's ``__setup__`` while loading the Pool.

One of the most common uses of ``__setup__`` is to alter characteristics of a
Field.  In doing this, you can assume that the arguments with which the field
was instantiated have become attributes of the field.  I.e., the field follows
the common Python instantiation pattern:

::

  class AClass(object):

      def __init__(self, foo):
          self.foo = foo

Naturally, this would not need to be the case; a class could do something
different with an argument that instantiates it.  But, in coding ``__setup__``
methods, it is safe to assume that fields follow this pattern.


The Transaction
===============

Each interaction in Trytond takes place within a Transaction, which is a
thread-local singleton.  Calling Transaction() either starts a new Transaction
and returns it, or, if there is already a Transaction in the current thread,
simply returns that Transaction.  As a result of this, the standard idiom it
call Transaction() whenever referencing it, other than at import.

Each Transaction has a ``context`` dictionary that persists throughout the
transaction can can be used to store information for use in distant parts of
the codebase (although this is somewhat of a hack and overuse will lead to
maintenance difficulties):

::

  # To store a value for use elsewhere in code
  Transaction().context['foo'] = 'bar'

  # An approach less prone to unforeseen consequences, temporarily
  # updates the context
  with Transaction().set_context({'foo': bar}):
      [do stuff]
      # upon exiting the 'with' the original context is restored

Transactions automatically have one *database cursor*, and can be given
additional ones.  The cursor works as a transaction in the
traditional `database sense`_ of a collection of actions that are managed such
that, if any single one fails to commit to the database, all of them are
cancelled.  By default, actions take place within the default cursor and that
cursor will be rolled back (ie, its effects undone) on any unhandled error.
Otherwise, the default cursor commits (saves to database).  It is possible to
add additional cursors with ``Transaction().new_cursor()`` (and so, in effect,
nest database transactions).  Unlike the default cursor, for which rollback and
commit are automatic, for the new_cursor, these should be explicitly handled.
For example:

::

  with Transaction().new_cursor() as tx:
      try:
          [something]
      except:
          tx.rollback()
      else:
          tx.commit()


XML Files, Built-In Modules, and Views
======================================

XML Files
---------

Modules contain XML files (registered in the module's tryton.cfg file) whose
purpose is to specify instances of ModelSQL classes that are part of the module
configuration and are added to the database when the module is installed, or
when a Trytond-administration `database update`_ operation is performed.

The XML files take the form:

::

  <?xml version="1.0"?>
  <tryton>
      <data>
          <record model="a model __name__" id="a unique id">
              <field name="field name">field value</field>

              [additional fields]

          </record>

          [more records]

      </data>
  </tryton>

The XML files can be used to create instances of any ModelSQL class, but their
most essential use is creating model instances of the built-in modules.

Built-in Modules: ir and res
----------------------------

Trytond has two built-in modules, ir and res, that are essential to
implementation of Trytond, itself.  It is a testament to how powerful and
flexible the Trytond kernel is that it is  used to model not only that tangible
materials that Trytond users/customers will most often be interested in, but
also the abstract concepts involved in these modules.

The ``ir`` module provides Trytond's ways to define the user interface.  By far, the
most common purpose of Trytond XML files is to create instances of models defined in
``ir``.  For example, to define how users interact with a particular subclass
of ModelView, an XML file would define an instance of ``ir.ui.view``.  See
`view documentation`_.  When a client program wants instructions on how to render
a view  for a particular model class, it will call that class's ``fields_view_get``
method, which searches for relevant ``ir.ui.view`` instances, uses them to
build those instructions, and passes the instructions to the client, which is
then responsible for using them to render the view.

The ``res`` module establishes models for, among other things, system users, user groups,
and access permissions.

Trytond Kernel, Server, and Dispatcher
======================================

Because it follows the `3-tier`_ design pattern (rather than, for example,
the `model view controller`_ one), Trytond is well-suited to serving data not
only to the Tryton graphical interface, but to other interfaces, as well.

Trytond includes a stable server that is frequently used in deployments.
However, this built-in server is not the only way to make use of the Trytond
kernel.  The Nereid_ project is an example of using the Trytond kernel as the
backbone of a Flask-based web framework.  Trytond patches have also been written
to enter the Trytond kernel through the WSGI_ protocol, and the Trytond
maintainers have indicated that WSGI support will become a native Trytond feature
in an upcoming release, which will make running the kernel through an
alternative server a straight-forward endeavor.

A common entry point for servers accessing the Trytond kernel is the ``dispatcher``
function found at ``trytond.protocols.dispatcher.dispatch``.  Any server can access
the Trytond kernel through this function [#]_.  An example of monkeypatching the
dispatcher to create error-reporting middleware is `trytond sentry`_.

Alternatively, a server could circumvent the dispatcher, while still making use
of the Trytond kernel, if the server uses the Trytond ``Transaction`` API to handle
starting and stopping database transaction, similarly to interactive
Trytond usage.  A example of this approach is the Nereid_ ``application.py``.

Although the most common usage of Trytond is to serve requests for Tryton
graphical client, it is not restricted to that purpose.  Any program that sets
up a Trytond environment and either interacts with the dispatcher or explicitly
governs transaction start and stop can make use of the Trytond kernel.
Further, programs `other than the Tryton graphical client`_ can make calls to
servers running Trytond.


.. _documentation: http://doc.tryton.org/3.2/
.. _`unofficial documentation`: http://tryton-documentation.readthedocs.org/en/latest/
.. _Nereid: https://nereid.readthedocs.org/en/develop/
.. _WSGI: http://downloads.tryton.org/TUL2014/WSGI_Deployment.pdf
.. _`trytond sentry`: https://github.com/openlabs/trytond-sentry
.. _`database sense`: https://en.wikipedia.org/wiki/Database_transaction
.. _`database update`: https://code.google.com/p/tryton/wiki/Update
.. _`view documentation`: http://doc.tryton.org/3.0/trytond/doc/topics/views/index.html#topics-views
.. _super: https://rhettinger.wordpress.com/2011/05/26/super-considered-super/
.. [#] To do this, the API of the dispatcher must be respected.  The dispatcher takes
       the follow positional arguments: host; port; protocol (either 'JSON-RPC' or 'XML-RPC');
       database name (Trytond supports accessing multiple databases from a single kernel instance);
       user (user id); session (session id); object_type (in normal workflow, this will be 'model',
       'report', or 'wizard', though it may differ for system-maintenance calls); object name (the
       name registered in the Pool); method (the method of the object being called); finally, 
       all of the arguments to that method as trailing positional arguments.
.. _`other than the Tryton graphical client`: https://code.google.com/p/tryton/wiki/RemoteCalls
.. _`3-tier`: https://github.com/faif/python-patterns/blob/master/3-tier.py
.. _`model view controller`: https://github.com/faif/python-patterns/blob/master/mvc.py
