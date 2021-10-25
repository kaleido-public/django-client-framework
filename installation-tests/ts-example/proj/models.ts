import {
    Model,
    CollectionManager,
    RelatedObjectManager,
    RelatedCollectionManager,
} from "django-client-framework"

class Product extends Model {
    _model_name = "Product"
    static readonly objects = new CollectionManager(Product)
    get brand() {
        return new RelatedObjectManager(Brand, this, "brand")
    }
    id!: string
    barcode: string = ""
    brand_id?: number
}

class Brand extends Model {
    _model_name = "Brand"
    static readonly objects = new CollectionManager(Brand)
    get products() {
        return new RelatedCollectionManager(Product, this, "products")
    }
    id!: string
    name: string = ""
}

export { Product, Brand }
