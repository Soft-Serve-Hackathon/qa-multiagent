/**
 * CartService - Manages shopping cart operations
 * Handles line item management, totals calculation, and checkout flow
 */

import { Cart, LineItem } from "../models"

export class CartService {
  private repository: CartRepository

  constructor(repository: CartRepository) {
    this.repository = repository
  }

  /**
   * Add item to cart with variant validation
   * @param cartId - Cart identifier
   * @param productId - Product to add
   * @param variantId - Product variant
   * @param quantity - Quantity to add
   * @returns Updated cart
   * @throws CartValidationError if variant not valid for customer
   */
  async addLineItem(
    cartId: string,
    productId: string,
    variantId: string,
    quantity: number
  ): Promise<Cart> {
    const cart = await this.repository.findOne(cartId)
    
    if (!cart) {
      throw new Error(`Cart ${cartId} not found`)
    }

    // Validate variant eligibility based on customer tier
    const validForCustomer = await this.validateVariantAccess(
      cart.customerId,
      variantId
    )

    if (!validForCustomer) {
      throw new CartValidationError(
        "Variant not available for this customer tier"
      )
    }

    // Add or update line item
    const lineItem = cart.lineItems.find(li => li.variantId === variantId)
    
    if (lineItem) {
      lineItem.quantity += quantity
    } else {
      cart.lineItems.push({
        productId,
        variantId,
        quantity,
        createdAt: new Date()
      })
    }

    return this.repository.save(cart)
  }

  /**
   * Calculate total including tax and shipping
   */
  async calculateTotal(cartId: string): Promise<number> {
    const cart = await this.repository.findOne(cartId)
    let subtotal = 0

    for (const item of cart.lineItems) {
      const variant = await this.getVariant(item.variantId)
      subtotal += variant.price * item.quantity
    }

    const tax = subtotal * 0.1 // 10% tax
    const shipping = 15 // Fixed shipping

    return subtotal + tax + shipping
  }

  private async validateVariantAccess(
    customerId: string,
    variantId: string
  ): Promise<boolean> {
    const customer = await this.repository.getCustomer(customerId)
    const variant = await this.getVariant(variantId)

    // Premium variants restricted to existing customers
    if (variant.isPremium && !customer.isVerified) {
      return false
    }

    return true
  }

  private async getVariant(variantId: string): Promise<any> {
    // Implementation would fetch from product service
    return {}
  }
}

export class CartValidationError extends Error {
  constructor(message: string) {
    super(message)
    this.name = "CartValidationError"
  }
}
