/**
 * InventoryService - Manages product stock levels and reservations
 * Handles inventory reservations for orders and stock updates
 */

import { Product, Stock, Reservation } from "../models"

export class InventoryService {
  private reservations: Map<string, Reservation[]> = new Map()

  /**
   * Check if product is in stock
   * @param productId - Product identifier
   * @param quantity - Quantity needed
   * @returns true if available
   */
  async isInStock(productId: string, quantity: number): Promise<boolean> {
    const product = await this.getProduct(productId)
    const stock = await this.getStock(productId)
    const reserved = await this.getReservedQuantity(productId)

    const available = stock.quantity - reserved

    return available >= quantity
  }

  /**
   * Reserve inventory for an order
   * @param orderId - Order being placed
   * @param productId - Product to reserve
   * @param quantity - Quantity to reserve
   */
  async reserveStock(
    orderId: string,
    productId: string,
    quantity: number
  ): Promise<Reservation> {
    const isAvailable = await this.isInStock(productId, quantity)

    if (!isAvailable) {
      throw new StockUnavailableError(
        `Insufficient stock for product ${productId}`
      )
    }

    const reservation: Reservation = {
      id: `res_${Date.now()}`,
      orderId,
      productId,
      quantity,
      reservedAt: new Date(),
      expiresAt: new Date(Date.now() + 10 * 60 * 1000) // 10 min expiry
    }

    const existing = this.reservations.get(productId) || []
    existing.push(reservation)
    this.reservations.set(productId, existing)

    return reservation
  }

  /**
   * Update stock after order confirmation
   */
  async updateStock(productId: string, quantity: number): Promise<Stock> {
    const stock = await this.getStock(productId)
    stock.quantity -= quantity
    stock.lastUpdated = new Date()

    return stock
  }

  private async getReservedQuantity(productId: string): Promise<number> {
    const now = new Date()
    const reservations = this.reservations.get(productId) || []
    
    return reservations
      .filter(r => r.expiresAt > now)
      .reduce((sum, r) => sum + r.quantity, 0)
  }

  private async getProduct(productId: string): Promise<Product> {
    // Would fetch actual product
    return { id: productId }
  }

  private async getStock(productId: string): Promise<Stock> {
    // Would fetch from inventory database
    return { productId, quantity: 0 }
  }
}

export class StockUnavailableError extends Error {
  constructor(message: string) {
    super(message)
    this.name = "StockUnavailableError"
  }
}
