.. _Model:

`class` Model
=============================

Similar to the :django:`Model class in Django <models/instances>`, `Model` is
the base class of all user defined models in the frontend. The implementation
varies between the frontend languages, but generally, the `Model` base class
enforces the existance of an read-only `id` field. In addition, a `Model`
subclass can be serialized/deserialized from/to an JSON representation.

**Inheritance**

id `(required)`
    An `id` field must be defined. If the language allows, `id` should be read-only.


`static` objects `(optional)`
    A static member of the `CollectionManager`_ type for the model class, used
    to quickly access the `CollectionManager`_ instead of having to create a
    new one.

Others
    Any optional fields of native types, `RelatedObjectManager`_, or
    `RelatedCollectionManager`_ types.


**Example**

.. tabs::

    .. code-tab:: ts

        class Product extends Model {
            static readonly objects = new CollectionManager(Product)
            id: number = 0
            barcode: string = ""
            brand_id: number?
            get brand() { return new RelatedObjectManager(Brand, this, "brand") }
            get purchasers() { return new RelatedCollectionManager(Person, this, "purchasers") }
        }

