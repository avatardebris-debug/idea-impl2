import prisma from '../config/db';
import { env } from '../config/env';

// ─── Discount Code Types ───────────────────────────────────────────────────────────────────

export interface DiscountCode {
  id: string;
  code: string;
  storeId: string;
  type: 'percentage' | 'fixed' | 'free_shipping';
  value: number;
  usageLimit: number | null;
  currentUsage: number;
  startDate: Date;
  endDate: Date | null;
  isActive: boolean;
  minimumOrderAmount: number | null;
  createdAt: Date;
  updatedAt: Date;
}

export interface AppliedDiscount {
  code: string;
  type: 'percentage' | 'fixed' | 'free_shipping';
  value: number;
  discountAmount: number;
  minimumOrderAmount: number | null;
  isValid: boolean;
  errorMessage?: string;
}

// ─── Discount Code Service ───────────────────────────────────────────────────────────────────

export class DiscountCodeService {
  /**
   * Create a new discount code
   */
  static async createDiscountCode(
    storeId: string,
    ownerId: string,
    data: {
      code: string;
      type: 'percentage' | 'fixed' | 'free_shipping';
      value: number;
      usageLimit?: number;
      startDate?: Date;
      endDate?: Date;
      minimumOrderAmount?: number;
    }
  ): Promise<{ success: boolean; discountCode?: DiscountCode; error?: string }> {
    try {
      // Check if code already exists
      const existing = await prisma.discountCode.findFirst({
        where: { code: data.code.toUpperCase(), storeId },
      });

      if (existing) {
        return { success: false, error: 'Discount code already exists' };
      }

      // Validate value based on type
      if (data.type === 'percentage' && (data.value < 1 || data.value > 100)) {
        return { success: false, error: 'Percentage must be between 1 and 100' };
      }

      if (data.type === 'fixed' && data.value < 0) {
        return { success: false, error: 'Fixed amount must be non-negative' };
      }

      const discountCode = await prisma.discountCode.create({
        data: {
          code: data.code.toUpperCase(),
          storeId,
          type: data.type,
          value: data.value,
          usageLimit: data.usageLimit || null,
          startDate: data.startDate || new Date(),
          endDate: data.endDate || null,
          isActive: true,
          minimumOrderAmount: data.minimumOrderAmount || null,
        },
      });

      return { success: true, discountCode };
    } catch (error) {
      return { success: false, error: 'Failed to create discount code' };
    }
  }

  /**
   * Get all discount codes for a store
   */
  static async getDiscountCodes(storeId: string): Promise<DiscountCode[]> {
    return prisma.discountCode.findMany({
      where: { storeId },
      orderBy: { createdAt: 'desc' },
    });
  }

  /**
   * Get a specific discount code
   */
  static async getDiscountCode(code: string, storeId: string): Promise<DiscountCode | null> {
    return prisma.discountCode.findFirst({
      where: { code: code.toUpperCase(), storeId },
    });
  }

  /**
   * Validate a discount code
   */
  static async validateDiscountCode(
    code: string,
    storeId: string,
    orderAmount: number
  ): Promise<AppliedDiscount> {
    const discountCode = await this.getDiscountCode(code, storeId);

    if (!discountCode) {
      return {
        code,
        type: 'percentage',
        value: 0,
        discountAmount: 0,
        minimumOrderAmount: null,
        isValid: false,
        errorMessage: 'Invalid discount code',
      };
    }

    // Check if active
    if (!discountCode.isActive) {
      return {
        code: discountCode.code,
        type: discountCode.type,
        value: discountCode.value,
        discountAmount: 0,
        minimumOrderAmount: discountCode.minimumOrderAmount,
        isValid: false,
        errorMessage: 'This discount code is no longer active',
      };
    }

    // Check date range
    const now = new Date();
    if (now < discountCode.startDate) {
      return {
        code: discountCode.code,
        type: discountCode.type,
        value: discountCode.value,
        discountAmount: 0,
        minimumOrderAmount: discountCode.minimumOrderAmount,
        isValid: false,
        errorMessage: 'This discount code is not yet active',
      };
    }

    if (discountCode.endDate && now > discountCode.endDate) {
      return {
        code: discountCode.code,
        type: discountCode.type,
        value: discountCode.value,
        discountAmount: 0,
        minimumOrderAmount: discountCode.minimumOrderAmount,
        isValid: false,
        errorMessage: 'This discount code has expired',
      };
    }

    // Check usage limit
    if (discountCode.usageLimit && discountCode.currentUsage >= discountCode.usageLimit) {
      return {
        code: discountCode.code,
        type: discountCode.type,
        value: discountCode.value,
        discountAmount: 0,
        minimumOrderAmount: discountCode.minimumOrderAmount,
        isValid: false,
        errorMessage: 'This discount code has reached its usage limit',
      };
    }

    // Check minimum order amount
    if (discountCode.minimumOrderAmount && orderAmount < discountCode.minimumOrderAmount) {
      return {
        code: discountCode.code,
        type: discountCode.type,
        value: discountCode.value,
        discountAmount: 0,
        minimumOrderAmount: discountCode.minimumOrderAmount,
        isValid: false,
        errorMessage: `Minimum order amount is $${discountCode.minimumOrderAmount}`,
      };
    }

    // Calculate discount amount
    let discountAmount = 0;
    if (discountCode.type === 'percentage') {
      discountAmount = (orderAmount * discountCode.value) / 100;
    } else if (discountCode.type === 'fixed') {
      discountAmount = Math.min(discountCode.value, orderAmount);
    }
    // For free_shipping, discountAmount is 0 but shipping will be waived

    return {
      code: discountCode.code,
      type: discountCode.type,
      value: discountCode.value,
      discountAmount,
      minimumOrderAmount: discountCode.minimumOrderAmount,
      isValid: true,
    };
  }

  /**
   * Apply a discount code to an order
   */
  static async applyDiscountCode(orderId: string, code: string, storeId: string): Promise<{ success: boolean; discountAmount?: number; error?: string }> {
    const order = await prisma.order.findUnique({
      where: { id: orderId },
      select: { total: true, status: true },
    });

    if (!order) {
      return { success: false, error: 'Order not found' };
    }

    if (order.status !== 'PENDING') {
      return { success: false, error: 'Discount can only be applied to pending orders' };
    }

    const validation = await this.validateDiscountCode(code, storeId, order.total);

    if (!validation.isValid) {
      return { success: false, error: validation.errorMessage };
    }

    // Update order with discount
    await prisma.order.update({
      where: { id: orderId },
      data: {
        discountCode: code,
        discountAmount: validation.discountAmount,
        total: order.total - validation.discountAmount,
      },
    });

    // Increment usage count
    await prisma.discountCode.update({
      where: { code: code.toUpperCase(), storeId },
      data: { currentUsage: { increment: 1 } },
    });

    return { success: true, discountAmount: validation.discountAmount };
  }

  /**
   * Deactivate a discount code
   */
  static async deactivateDiscountCode(code: string, storeId: string): Promise<{ success: boolean; error?: string }> {
    try {
      await prisma.discountCode.update({
        where: { code: code.toUpperCase(), storeId },
        data: { isActive: false },
      });

      return { success: true };
    } catch (error) {
      return { success: false, error: 'Failed to deactivate discount code' };
    }
  }

  /**
   * Delete a discount code
   */
  static async deleteDiscountCode(code: string, storeId: string): Promise<{ success: boolean; error?: string }> {
    try {
      await prisma.discountCode.delete({
        where: { code: code.toUpperCase(), storeId },
      });

      return { success: true };
    } catch (error) {
      return { success: false, error: 'Failed to delete discount code' };
    }
  }
}
