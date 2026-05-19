import { describe, it, expect, beforeEach, vi, Mock } from 'vitest';
import { ThemeService } from '../services/theme.service';
import { AnalyticsService } from '../services/analytics.service';
import { DiscountCodeService } from '../services/discount.service';

// Mock prisma
vi.mock('../config/db', () => ({
  default: {
    theme: {
      findMany: vi.fn(),
      findUnique: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
    },
    store: {
      findUnique: vi.fn(),
      findFirst: vi.fn(),
      update: vi.fn(),
    },
    order: {
      findMany: vi.fn(),
      update: vi.fn(),
    },
    product: {
      findMany: vi.fn(),
    },
    discountCode: {
      findFirst: vi.fn(),
      findMany: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
    },
  },
}));

describe('ThemeService', () => {
  describe('getThemes', () => {
    it('should return all themes when no filters provided', async () => {
      const mockThemes = [
        { id: '1', name: 'Minimal', category: 'minimal', price: 0, isOfficial: true },
        { id: '2', name: 'Bold', category: 'bold', price: 9.99, isOfficial: false },
      ];
      vi.mocked((await import('../config/db')).default.theme.findMany).mockResolvedValue(mockThemes);

      const result = await ThemeService.getThemes({});
      expect(result).toHaveLength(2);
    });

    it('should filter by category', async () => {
      const mockThemes = [{ id: '1', name: 'Minimal', category: 'minimal', price: 0, isOfficial: true }];
      vi.mocked((await import('../config/db')).default.theme.findMany).mockResolvedValue(mockThemes);

      const result = await ThemeService.getThemes({ category: 'minimal' });
      expect(result).toHaveLength(1);
      expect(result[0].category).toBe('minimal');
    });

    it('should filter by isOfficial', async () => {
      const mockThemes = [{ id: '1', name: 'Official', category: 'minimal', price: 0, isOfficial: true }];
      vi.mocked((await import('../config/db')).default.theme.findMany).mockResolvedValue(mockThemes);

      const result = await ThemeService.getThemes({ isOfficial: true });
      expect(result).toHaveLength(1);
      expect(result[0].isOfficial).toBe(true);
    });
  });

  describe('applyTheme', () => {
    it('should apply a theme to a store', async () => {
      const mockTheme = { id: '1', name: 'Minimal', price: 0, isOfficial: true };
      vi.mocked((await import('../config/db')).default.theme.findUnique).mockResolvedValue(mockTheme);
      vi.mocked((await import('../config/db')).default.store.update).mockResolvedValue({ id: 'store1', theme: '1' } as any);

      const result = await ThemeService.applyTheme('store1', '1', 'user1');
      expect(result.success).toBe(true);
    });

    it('should fail if theme not found', async () => {
      vi.mocked((await import('../config/db')).default.theme.findUnique).mockResolvedValue(null);

      const result = await ThemeService.applyTheme('store1', '999', 'user1');
      expect(result.success).toBe(false);
      expect(result.error).toBe('Theme not found');
    });
  });

  describe('customizeColors', () => {
    it('should update theme colors', async () => {
      vi.mocked((await import('../config/db')).default.store.update).mockResolvedValue({ id: 'store1', themeColors: { primary: '#FF0000' } } as any);

      const result = await ThemeService.customizeColors('store1', { primary: '#FF0000' });
      expect(result.success).toBe(true);
    });
  });
});

describe('AnalyticsService', () => {
  describe('getSalesSummary', () => {
    it('should calculate total revenue', async () => {
      const mockOrders = [
        { id: '1', total: 100, createdAt: new Date(), items: [] },
        { id: '2', total: 200, createdAt: new Date(), items: [] },
      ];
      vi.mocked((await import('../config/db')).default.order.findMany).mockResolvedValue(mockOrders as any);

      const result = await AnalyticsService.getSalesSummary('store1', new Date('2024-01-01'), new Date('2024-12-31'));
      expect(result.totalRevenue).toBe(300);
      expect(result.totalOrders).toBe(2);
      expect(result.averageOrderValue).toBe(150);
    });
  });

  describe('getProductPerformance', () => {
    it('should return top selling products', async () => {
      const mockOrders = [
        {
          id: '1',
          items: [
            { productId: 'p1', quantity: 2, price: 50 },
            { productId: 'p2', quantity: 1, price: 100 },
          ],
        },
      ];
      vi.mocked((await import('../config/db')).default.order.findMany).mockResolvedValue(mockOrders as any);

      const result = await AnalyticsService.getProductPerformance('store1', new Date('2024-01-01'), new Date('2024-12-31'));
      expect(result.topSellingProducts).toHaveLength(2);
    });
  });

  describe('getCustomerAnalytics', () => {
    it('should calculate customer metrics', async () => {
      const mockOrders = [
        { id: '1', userId: 'u1', total: 100, createdAt: new Date(), customerName: 'John' },
        { id: '2', userId: 'u1', total: 200, createdAt: new Date(), customerName: 'John' },
        { id: '3', userId: 'u2', total: 150, createdAt: new Date(), customerName: 'Jane' },
      ];
      vi.mocked((await import('../config/db')).default.order.findMany).mockResolvedValue(mockOrders as any);

      const result = await AnalyticsService.getCustomerAnalytics('store1', new Date('2024-01-01'), new Date('2024-12-31'));
      expect(result.totalCustomers).toBe(2);
      expect(result.customerLifetimeValue).toBe(150);
      expect(result.topCustomers).toHaveLength(2);
    });
  });

  describe('getTrafficAnalytics', () => {
    it('should return simulated traffic data', async () => {
      const result = await AnalyticsService.getTrafficAnalytics('store1', new Date('2024-01-01'), new Date('2024-12-31'));
      expect(result.totalVisits).toBeGreaterThan(0);
      expect(result.uniqueVisitors).toBeGreaterThan(0);
      expect(result.topPages).toHaveLength(5);
      expect(result.trafficSources).toHaveLength(5);
    });
  });

  describe('getInventoryAlerts', () => {
    it('should return low stock alerts', async () => {
      const mockProducts = [
        { id: 'p1', name: 'Product 1', inventory: 5, variants: [] },
        { id: 'p2', name: 'Product 2', inventory: 0, variants: [] },
        { id: 'p3', name: 'Product 3', inventory: 50, variants: [] },
      ];
      vi.mocked((await import('../config/db')).default.product.findMany).mockResolvedValue(mockProducts as any);

      const result = await AnalyticsService.getInventoryAlerts('store1');
      expect(result).toHaveLength(2); // p1 (low) and p2 (out)
    });
  });
});

describe('DiscountCodeService', () => {
  describe('createDiscountCode', () => {
    it('should create a percentage discount', async () => {
      vi.mocked((await import('../config/db')).default.discountCode.findFirst).mockResolvedValue(null);
      vi.mocked((await import('../config/db')).default.discountCode.create).mockResolvedValue({
        id: 'dc1',
        code: 'SAVE10',
        type: 'percentage',
        value: 10,
        storeId: 'store1',
        usageLimit: null,
        currentUsage: 0,
        startDate: new Date(),
        endDate: null,
        isActive: true,
        minimumOrderAmount: null,
        createdAt: new Date(),
        updatedAt: new Date(),
      } as any);

      const result = await DiscountCodeService.createDiscountCode('store1', 'user1', {
        code: 'SAVE10',
        type: 'percentage',
        value: 10,
      });
      expect(result.success).toBe(true);
    });

    it('should fail if code already exists', async () => {
      vi.mocked((await import('../config/db')).default.discountCode.findFirst).mockResolvedValue({ id: 'dc1' } as any);

      const result = await DiscountCodeService.createDiscountCode('store1', 'user1', {
        code: 'SAVE10',
        type: 'percentage',
        value: 10,
      });
      expect(result.success).toBe(false);
      expect(result.error).toBe('Discount code already exists');
    });

    it('should fail if percentage is invalid', async () => {
      const result = await DiscountCodeService.createDiscountCode('store1', 'user1', {
        code: 'SAVE150',
        type: 'percentage',
        value: 150,
      });
      expect(result.success).toBe(false);
      expect(result.error).toBe('Percentage must be between 1 and 100');
    });
  });

  describe('validateDiscountCode', () => {
    it('should validate a valid discount code', async () => {
      const mockDiscount = {
        id: 'dc1',
        code: 'SAVE10',
        type: 'percentage',
        value: 10,
        storeId: 'store1',
        usageLimit: null,
        currentUsage: 0,
        startDate: new Date('2024-01-01'),
        endDate: new Date('2024-12-31'),
        isActive: true,
        minimumOrderAmount: null,
        createdAt: new Date(),
        updatedAt: new Date(),
      };
      vi.mocked((await import('../config/db')).default.discountCode.findFirst).mockResolvedValue(mockDiscount as any);

      const result = await DiscountCodeService.validateDiscountCode('SAVE10', 'store1', 100);
      expect(result.isValid).toBe(true);
      expect(result.discountAmount).toBe(10);
    });

    it('should fail if code is expired', async () => {
      const mockDiscount = {
        id: 'dc1',
        code: 'SAVE10',
        type: 'percentage',
        value: 10,
        storeId: 'store1',
        usageLimit: null,
        currentUsage: 0,
        startDate: new Date('2023-01-01'),
        endDate: new Date('2023-12-31'),
        isActive: true,
        minimumOrderAmount: null,
        createdAt: new Date(),
        updatedAt: new Date(),
      };
      vi.mocked((await import('../config/db')).default.discountCode.findFirst).mockResolvedValue(mockDiscount as any);

      const result = await DiscountCodeService.validateDiscountCode('SAVE10', 'store1', 100);
      expect(result.isValid).toBe(false);
      expect(result.errorMessage).toBe('This discount code has expired');
    });

    it('should fail if minimum order amount not met', async () => {
      const mockDiscount = {
        id: 'dc1',
        code: 'SAVE10',
        type: 'percentage',
        value: 10,
        storeId: 'store1',
        usageLimit: null,
        currentUsage: 0,
        startDate: new Date('2024-01-01'),
        endDate: new Date('2024-12-31'),
        isActive: true,
        minimumOrderAmount: 50,
        createdAt: new Date(),
        updatedAt: new Date(),
      };
      vi.mocked((await import('../config/db')).default.discountCode.findFirst).mockResolvedValue(mockDiscount as any);

      const result = await DiscountCodeService.validateDiscountCode('SAVE10', 'store1', 30);
      expect(result.isValid).toBe(false);
      expect(result.errorMessage).toBe('Minimum order amount is $50');
    });
  });

  describe('applyDiscountCode', () => {
    it('should apply a discount to an order', async () => {
      const mockOrder = { id: 'o1', total: 100, status: 'PENDING' };
      const mockDiscount = {
        id: 'dc1',
        code: 'SAVE10',
        type: 'percentage',
        value: 10,
        storeId: 'store1',
        usageLimit: null,
        currentUsage: 0,
        startDate: new Date('2024-01-01'),
        endDate: new Date('2024-12-31'),
        isActive: true,
        minimumOrderAmount: null,
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      vi.mocked((await import('../config/db')).default.order.findUnique).mockResolvedValue(mockOrder as any);
      vi.mocked((await import('../config/db')).default.discountCode.findFirst).mockResolvedValue(mockDiscount as any);
      vi.mocked((await import('../config/db')).default.order.update).mockResolvedValue({} as any);
      vi.mocked((await import('../config/db')).default.discountCode.update).mockResolvedValue({} as any);

      const result = await DiscountCodeService.applyDiscountCode('o1', 'SAVE10', 'store1');
      expect(result.success).toBe(true);
      expect(result.discountAmount).toBe(10);
    });
  });
});
