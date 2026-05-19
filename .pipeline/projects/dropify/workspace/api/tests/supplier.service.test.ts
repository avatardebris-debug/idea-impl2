import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import * as supplierService from '../src/services/supplier.service';
import prisma from '../src/config/db';

// Mock prisma
vi.mock('../src/config/db', () => ({
  default: {
    supplier: {
      create: vi.fn(),
      findMany: vi.fn(),
      findUnique: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
    },
    supplierAccount: {
      create: vi.fn(),
      findMany: vi.fn(),
      findUnique: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
    },
    supplierProduct: {
      create: vi.fn(),
      findMany: vi.fn(),
      findFirst: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
    },
    product: {
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
      findUnique: vi.fn(),
    },
    inventorySync: {
      create: vi.fn(),
      findMany: vi.fn(),
    },
    fulfillment: {
      create: vi.fn(),
      findFirst: vi.fn(),
      findUnique: vi.fn(),
      update: vi.fn(),
    },
    order: {
      findUnique: vi.fn(),
      update: vi.fn(),
    },
  },
}));

describe('Supplier Service', () => {
  const mockTenantId = 'tenant-123';
  const mockStoreId = 'store-456';
  const mockUserId = 'user-789';

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('createSupplier', () => {
    it('should create a new supplier', async () => {
      const supplierData = {
        name: 'Test Supplier',
        type: 'ALIEXPRESS' as const,
        baseUrl: 'https://api.aliexpress.com',
        apiKey: 'test-key',
        description: 'Test description',
        contactEmail: 'test@example.com',
        contactPhone: '1234567890',
        logoUrl: 'https://example.com/logo.png',
        metadata: { region: 'US' },
      };

      const mockSupplier = {
        id: 'supplier-123',
        ...supplierData,
        status: 'ACTIVE',
        tenantId: mockTenantId,
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      (prisma.supplier.create as any).mockResolvedValue(mockSupplier);

      const result = await supplierService.createSupplier(mockTenantId, supplierData);

      expect(result).toEqual(mockSupplier);
      expect(prisma.supplier.create).toHaveBeenCalledWith({
        data: {
          ...supplierData,
          status: 'ACTIVE',
          tenantId: mockTenantId,
        },
      });
    });

    it('should throw error if supplier already exists', async () => {
      const supplierData = {
        name: 'Existing Supplier',
        type: 'ALIEXPRESS' as const,
      };

      (prisma.supplier.create as any).mockRejectedValue(new Error('Unique constraint failed'));

      await expect(supplierService.createSupplier(mockTenantId, supplierData)).rejects.toThrow('Supplier already exists');
    });
  });

  describe('getSuppliers', () => {
    it('should return all suppliers for a tenant', async () => {
      const mockSuppliers = [
        { id: 'supplier-1', name: 'Supplier 1', type: 'ALIEXPRESS', status: 'ACTIVE' },
        { id: 'supplier-2', name: 'Supplier 2', type: 'SPOCKET', status: 'ACTIVE' },
      ];

      (prisma.supplier.findMany as any).mockResolvedValue(mockSuppliers);

      const result = await supplierService.getSuppliers(mockTenantId);

      expect(result).toEqual(mockSuppliers);
      expect(prisma.supplier.findMany).toHaveBeenCalledWith({
        where: { tenantId: mockTenantId },
        orderBy: { createdAt: 'desc' },
      });
    });

    it('should filter by type', async () => {
      const mockSuppliers = [{ id: 'supplier-1', name: 'Supplier 1', type: 'ALIEXPRESS', status: 'ACTIVE' }];

      (prisma.supplier.findMany as any).mockResolvedValue(mockSuppliers);

      await supplierService.getSuppliers(mockTenantId, { type: 'ALIEXPRESS' });

      expect(prisma.supplier.findMany).toHaveBeenCalledWith({
        where: { tenantId: mockTenantId, type: 'ALIEXPRESS' },
        orderBy: { createdAt: 'desc' },
      });
    });
  });

  describe('getSupplier', () => {
    it('should return a supplier by ID', async () => {
      const mockSupplier = { id: 'supplier-123', name: 'Test Supplier', type: 'ALIEXPRESS', status: 'ACTIVE' };

      (prisma.supplier.findUnique as any).mockResolvedValue(mockSupplier);

      const result = await supplierService.getSupplier(mockTenantId, 'supplier-123');

      expect(result).toEqual(mockSupplier);
      expect(prisma.supplier.findUnique).toHaveBeenCalledWith({
        where: { id: 'supplier-123', tenantId: mockTenantId },
      });
    });

    it('should return null if supplier not found', async () => {
      (prisma.supplier.findUnique as any).mockResolvedValue(null);

      const result = await supplierService.getSupplier(mockTenantId, 'non-existent');

      expect(result).toBeNull();
    });
  });

  describe('updateSupplier', () => {
    it('should update a supplier', async () => {
      const updateData = { name: 'Updated Supplier' };
      const mockSupplier = { id: 'supplier-123', name: 'Updated Supplier', type: 'ALIEXPRESS', status: 'ACTIVE' };

      (prisma.supplier.findUnique as any).mockResolvedValue({ id: 'supplier-123' });
      (prisma.supplier.update as any).mockResolvedValue(mockSupplier);

      const result = await supplierService.updateSupplier(mockTenantId, 'supplier-123', updateData);

      expect(result).toEqual(mockSupplier);
      expect(prisma.supplier.update).toHaveBeenCalledWith({
        where: { id: 'supplier-123' },
        data: updateData,
      });
    });

    it('should throw error if supplier not found', async () => {
      (prisma.supplier.findUnique as any).mockResolvedValue(null);

      await expect(
        supplierService.updateSupplier(mockTenantId, 'non-existent', { name: 'Updated' })
      ).rejects.toThrow('Supplier not found');
    });
  });

  describe('deleteSupplier', () => {
    it('should delete a supplier', async () => {
      (prisma.supplier.findUnique as any).mockResolvedValue({ id: 'supplier-123' });
      (prisma.supplier.delete as any).mockResolvedValue({ id: 'supplier-123' });

      await supplierService.deleteSupplier(mockTenantId, 'supplier-123');

      expect(prisma.supplier.delete).toHaveBeenCalledWith({
        where: { id: 'supplier-123' },
      });
    });

    it('should throw error if supplier not found', async () => {
      (prisma.supplier.findUnique as any).mockResolvedValue(null);

      await expect(supplierService.deleteSupplier(mockTenantId, 'non-existent')).rejects.toThrow('Supplier not found');
    });
  });

  describe('connectSupplierAccount', () => {
    it('should connect a supplier account', async () => {
      const accountData = {
        supplierId: 'supplier-123',
        externalAccountId: 'ext-123',
        credentials: { token: 'test-token' },
      };

      const mockAccount = {
        id: 'account-123',
        ...accountData,
        storeId: mockStoreId,
        status: 'ACTIVE',
        tenantId: mockTenantId,
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      (prisma.supplierAccount.create as any).mockResolvedValue(mockAccount);

      const result = await supplierService.connectSupplierAccount(mockTenantId, mockStoreId, mockUserId, accountData);

      expect(result).toEqual(mockAccount);
      expect(prisma.supplierAccount.create).toHaveBeenCalledWith({
        data: {
          ...accountData,
          storeId: mockStoreId,
          status: 'ACTIVE',
          tenantId: mockTenantId,
          createdBy: mockUserId,
        },
      });
    });
  });

  describe('disconnectSupplierAccount', () => {
    it('should disconnect a supplier account', async () => {
      (prisma.supplierAccount.findFirst as any).mockResolvedValue({ id: 'account-123' });
      (prisma.supplierAccount.update as any).mockResolvedValue({ id: 'account-123', status: 'DISCONNECTED' });

      await supplierService.disconnectSupplierAccount(mockTenantId, mockStoreId, 'supplier-123');

      expect(prisma.supplierAccount.update).toHaveBeenCalledWith({
        where: { id: 'account-123' },
        data: { status: 'DISCONNECTED' },
      });
    });

    it('should throw error if account not found', async () => {
      (prisma.supplierAccount.findFirst as any).mockResolvedValue(null);

      await expect(
        supplierService.disconnectSupplierAccount(mockTenantId, mockStoreId, 'supplier-123')
      ).rejects.toThrow('Supplier account not found');
    });
  });

  describe('importSupplierProduct', () => {
    it('should import a supplier product', async () => {
      const productData = {
        supplierId: 'supplier-123',
        supplierProductId: 'ext-prod-123',
        name: 'Test Product',
        price: 29.99,
        inventory: 100,
        sku: 'SKU-123',
        status: 'draft' as const,
      };

      const mockProduct = { id: 'product-123' };
      const mockSupplierProduct = {
        id: 'sp-123',
        ...productData,
        localProductId: 'product-123',
        syncStatus: 'COMPLETED',
        tenantId: mockTenantId,
        storeId: mockStoreId,
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      (prisma.product.findFirst as any).mockResolvedValue(null);
      (prisma.product.create as any).mockResolvedValue(mockProduct);
      (prisma.supplierProduct.create as any).mockResolvedValue(mockSupplierProduct);

      const result = await supplierService.importSupplierProduct(mockTenantId, mockStoreId, mockUserId, productData);

      expect(result).toEqual(mockSupplierProduct);
      expect(prisma.product.create).toHaveBeenCalled();
      expect(prisma.supplierProduct.create).toHaveBeenCalled();
    });

    it('should throw error if product already imported', async () => {
      const productData = {
        supplierId: 'supplier-123',
        supplierProductId: 'ext-prod-123',
        name: 'Test Product',
        price: 29.99,
      };

      (prisma.product.findFirst as any).mockResolvedValue({ id: 'existing-product' });

      await expect(
        supplierService.importSupplierProduct(mockTenantId, mockStoreId, mockUserId, productData)
      ).rejects.toThrow('Product already imported from this supplier');
    });
  });

  describe('syncInventory', () => {
    it('should sync inventory for a supplier account', async () => {
      const mockAccount = {
        id: 'account-123',
        supplierProducts: [
          { id: 'sp-1', supplierProductId: 'ext-1', inventory: 100, localProductId: 'product-1' },
          { id: 'sp-2', supplierProductId: 'ext-2', inventory: 50, localProductId: 'product-2' },
        ],
      };

      (prisma.supplierAccount.findUnique as any).mockResolvedValue(mockAccount);
      (prisma.supplierAccount.update as any).mockResolvedValue({ id: 'account-123' });
      (prisma.inventorySync.create as any).mockResolvedValue({ id: 'sync-1' });
      (prisma.product.update as any).mockResolvedValue({ id: 'product-1' });

      const result = await supplierService.syncInventory('account-123');

      expect(result.success).toBe(2);
      expect(result.failed).toBe(0);
      expect(prisma.supplierAccount.update).toHaveBeenCalledWith(
        { id: 'account-123' },
        { syncStatus: 'COMPLETED', lastSyncAt: expect.any(Date) }
      );
    });

    it('should handle sync failures', async () => {
      const mockAccount = {
        id: 'account-123',
        supplierProducts: [
          { id: 'sp-1', supplierProductId: 'ext-1', inventory: 100, localProductId: 'product-1' },
        ],
      };

      (prisma.supplierAccount.findUnique as any).mockResolvedValue(mockAccount);
      (prisma.supplierAccount.update as any).mockResolvedValue({ id: 'account-123' });
      (prisma.inventorySync.create as any).mockResolvedValue({ id: 'sync-1' });
      (prisma.product.update as any).mockRejectedValue(new Error('Sync failed'));

      const result = await supplierService.syncInventory('account-123');

      expect(result.success).toBe(0);
      expect(result.failed).toBe(1);
      expect(result.errors.length).toBe(1);
    });
  });

  describe('createFulfillment', () => {
    it('should create a fulfillment for a paid order', async () => {
      const mockOrder = {
        id: 'order-123',
        orderNumber: 'ORD-001',
        paymentStatus: 'PAID',
        tenantId: mockTenantId,
        items: [
          {
            productId: 'product-1',
            quantity: 2,
            price: 29.99,
            product: {
              supplierProduct: {
                id: 'sp-1',
                supplierId: 'supplier-123',
              },
            },
          },
        ],
      };

      const mockFulfillment = {
        id: 'fulfillment-123',
        orderId: 'order-123',
        supplierId: 'supplier-123',
        status: 'PENDING',
        cost: 0,
        notes: 'Auto-fulfillment triggered for order ORD-001',
        metadata: {
          items: [{ productId: 'product-1', quantity: 2, price: 29.99 }],
        },
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      (prisma.order.findUnique as any).mockResolvedValue(mockOrder);
      (prisma.fulfillment.findFirst as any).mockResolvedValue(null);
      (prisma.fulfillment.create as any).mockResolvedValue(mockFulfillment);
      (prisma.order.update as any).mockResolvedValue({ id: 'order-123', status: 'FULFILLED' });

      const result = await supplierService.createFulfillment('order-123', 'supplier-123');

      expect(result).toEqual(mockFulfillment);
      expect(prisma.order.update).toHaveBeenCalledWith(
        { where: { id: 'order-123' } },
        { status: 'FULFILLED' }
      );
    });

    it('should throw error if order is not paid', async () => {
      const mockOrder = {
        id: 'order-123',
        paymentStatus: 'PENDING',
        items: [],
      };

      (prisma.order.findUnique as any).mockResolvedValue(mockOrder);

      await expect(supplierService.createFulfillment('order-123', 'supplier-123')).rejects.toThrow(
        'Order must be paid before fulfillment'
      );
    });

    it('should throw error if fulfillment already exists', async () => {
      const mockOrder = {
        id: 'order-123',
        paymentStatus: 'PAID',
        items: [],
      };

      (prisma.order.findUnique as any).mockResolvedValue(mockOrder);
      (prisma.fulfillment.findFirst as any).mockResolvedValue({ id: 'existing-fulfillment' });

      await expect(supplierService.createFulfillment('order-123', 'supplier-123')).rejects.toThrow(
        'Fulfillment already exists for this order'
      );
    });
  });

  describe('updateFulfillmentStatus', () => {
    it('should update fulfillment status to SHIPPED', async () => {
      const mockFulfillment = {
        id: 'fulfillment-123',
        orderId: 'order-123',
        status: 'PENDING',
        trackingNumber: null,
        trackingUrl: null,
        carrier: null,
        cost: 0,
      };

      const updatedFulfillment = {
        ...mockFulfillment,
        status: 'SHIPPED',
        trackingNumber: 'TRACK123',
        trackingUrl: 'https://track.example.com/TRACK123',
        carrier: 'FedEx',
        cost: 15.99,
      };

      (prisma.fulfillment.findUnique as any).mockResolvedValue(mockFulfillment);
      (prisma.fulfillment.update as any).mockResolvedValue(updatedFulfillment);
      (prisma.order.update as any).mockResolvedValue({ id: 'order-123', status: 'SHIPPED' });

      const result = await supplierService.updateFulfillmentStatus(
        'fulfillment-123',
        'SHIPPED',
        'TRACK123',
        'https://track.example.com/TRACK123',
        'FedEx',
        15.99
      );

      expect(result.status).toBe('SHIPPED');
      expect(result.trackingNumber).toBe('TRACK123');
      expect(prisma.order.update).toHaveBeenCalledWith(
        { where: { id: 'order-123' } },
        { status: 'SHIPPED' }
      );
    });
  });

  describe('getSupplierDirectory', () => {
    it('should return active suppliers', async () => {
      const mockSuppliers = [
        { id: 'supplier-1', name: 'Supplier 1', type: 'ALIEXPRESS', status: 'ACTIVE' },
        { id: 'supplier-2', name: 'Supplier 2', type: 'SPOCKET', status: 'ACTIVE' },
      ];

      (prisma.supplier.findMany as any).mockResolvedValue(mockSuppliers);

      const result = await supplierService.getSupplierDirectory();

      expect(result).toEqual(mockSuppliers);
      expect(prisma.supplier.findMany).toHaveBeenCalledWith({
        where: { status: 'ACTIVE' },
        select: expect.any(Object),
        orderBy: expect.any(Object),
      });
    });

    it('should filter by type', async () => {
      const mockSuppliers = [{ id: 'supplier-1', name: 'Supplier 1', type: 'ALIEXPRESS', status: 'ACTIVE' }];

      (prisma.supplier.findMany as any).mockResolvedValue(mockSuppliers);

      await supplierService.getSupplierDirectory({ type: 'ALIEXPRESS' });

      expect(prisma.supplier.findMany).toHaveBeenCalledWith({
        where: { status: 'ACTIVE', type: 'ALIEXPRESS' },
        select: expect.any(Object),
        orderBy: expect.any(Object),
      });
    });
  });
});
