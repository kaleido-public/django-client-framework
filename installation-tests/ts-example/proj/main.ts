import { Ajax } from "django-client-framework"
import { Product } from "./models"

Ajax.url_prefix = "http://localhost:8000"

async function main() {
    let product = await Product.objects.get({})
    let nike = await product.brand.get()
}

main()
