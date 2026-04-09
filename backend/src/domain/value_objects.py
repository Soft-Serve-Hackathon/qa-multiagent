"""Domain value objects — immutable types used across the domain."""
import uuid


def generate_trace_id() -> str:
    """Generate a new UUID v4 trace identifier."""
    return str(uuid.uuid4())


# Severity SLA map (hours)
SEVERITY_SLA_HOURS: dict[str, int] = {
    "P1": 1,
    "P2": 4,
    "P3": 24,
    "P4": 168,  # 1 week
}

# Severity emoji for Slack messages
SEVERITY_EMOJI: dict[str, str] = {
    "P1": ":red_circle:",
    "P2": ":orange_circle:",
    "P3": ":yellow_circle:",
    "P4": ":white_circle:",
}

# Medusa.js module → file mapping
MEDUSA_MODULE_FILES: dict[str, list[str]] = {
    "cart": [
        "packages/medusa/src/services/cart.ts",
        "packages/medusa/src/api/routes/store/carts/index.ts",
    ],
    "order": [
        "packages/medusa/src/services/order.ts",
        "packages/medusa/src/api/routes/store/orders/index.ts",
    ],
    "payment": [
        "packages/medusa/src/services/payment.ts",
        "packages/medusa/src/services/payment-provider.ts",
    ],
    "inventory": [
        "packages/medusa/src/services/inventory.ts",
        "packages/medusa/src/services/product-variant-inventory.ts",
    ],
    "product": [
        "packages/medusa/src/services/product.ts",
        "packages/medusa/src/api/routes/store/products/index.ts",
    ],
    "customer": [
        "packages/medusa/src/services/customer.ts",
        "packages/medusa/src/api/routes/store/auth/index.ts",
    ],
    "shipping": [
        "packages/medusa/src/services/shipping.ts",
        "packages/medusa/src/services/fulfillment.ts",
    ],
    "discount": [
        "packages/medusa/src/services/discount.ts",
        "packages/medusa/src/api/routes/store/carts/index.ts",
    ],
}

ALLOWED_MIME_TYPES: set[str] = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "text/plain",
    "application/octet-stream",  # .log files often appear as this
}

ALLOWED_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg", ".txt", ".log"}
