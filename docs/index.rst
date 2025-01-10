================================================================
The Common Western Music Notation Recognition Framework (COMREF)
================================================================

.. toctree::
    :maxdepth: 2

    comref_converter


-----------------
Converting to MTN
-----------------

Each converter to MTN is written as a derivation of the :py:class:`comref_converter.translator_base.Translator` class.

.. autoclass:: comref_converter.translator_base.Translator
    :members:
    :undoc-members:
    :private-members:
    :show-inheritance:
    :no-index:


-------------------
Converting from MTN
-------------------

Once a Score object is produced