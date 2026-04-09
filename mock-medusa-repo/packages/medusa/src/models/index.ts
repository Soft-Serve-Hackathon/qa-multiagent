/**
 * Type definitions for Medusa.js models
 */

export interface Cart {
  id: string
  customerId: string
  lineItems: LineItem[]
  total: number
  createdAt: Date
  updatedAt: Date
}

export interface LineItem {
  productId: string
  variantId: string
  quantity: number
  createdAt: Date
}

export interface Product {
  id: string
  title: string
  description: string
  variants: ProductVariant[]
}

export interface ProductVariant {
  id: string
  productId: string
  title: string
  price: number
  isPremium?: boolean
}

export interface Order {
  id: string
  customerId: string
  cartId: string
  status: OrderStatus
  total: number
  items: LineItem[]
  cancellationReason?: string
  createdAt: Date
  updatedAt: Date
}

export enum OrderStatus {
  PENDING = "pending",
  CONFIRMED = "confirmed",
  PROCESSING = "processing",
  SHIPPED = "shipped",
  DELIVERED = "delivered",
  CANCELLED = "cancelled",
  RETURNED = "returned"
}

export interface PaymentSession {
  id: string
  status: string
  provider: string
  amount: number
  createdAt: Date
}

export interface Stock {
  productId: string
  quantity: number
  lastUpdated: Date
}

export interface Reservation {
  id: string
  orderId: string
  productId: string
  quantity: number
  reservedAt: Date
  expiresAt: Date
}

export interface Customer {
  id: string
  email: string
  firstName: string
  lastName: string
  isVerified: boolean
}
