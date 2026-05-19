import { z } from 'zod';
import prisma from '../config/db';
import { env } from '../config/env';

// ─── Zod Schemas ───────────────────────────────────────────────

const createSupplierSchema = z.object({
  name: z.string().min(1),
  type: z.enum(['ALIEXPRESS', 'SPOCKET', 'CJ_DROPSHIPPING', 'DROPSERVING', 'CUSTOM']),
  baseUrl: z.string().url().optional(),
  apiKey: z.string().optional(),
  apiSecret: z.string().optional(),
  description: z.string().optional(),
  contactEmail: z.string().email().optional(),
  contactPhone: z.string().optional(),
  logoUrl: z.string().url().optional(),
  metadata: z.record(z.unknown()).optional(),
});

const updateSupplierSchema = z.object({
  name: z.string().min(1).optional(),
  baseUrl: z.string().url().optional(),
  apiKey: z.string().optional(),
  apiSecret: z.string().optional(),
  description: z.string().optional(),
  contactEmail: z.string().email().optional(),
  contactPhone: z.string().optional(),
  logoUrl: z.string().url().optional(),
  metadata: z.record(z.unknown()).optional(),
});

const connectSupplierSchema = z.object({
  supplierId: z.string().uuid(),
  externalAccountId: z.string().optional(),
  credentials: z.record(z.unknown()).optional(),
});

const importProductSchema = z.object({
  supplierId: z.string().uuid(),
  supplierProductId: z.string(),
  name: z.string().min(1),
  description: z.string().optional(),
  price: z.number().positive(),
  compareAtPrice: z.number().positive().optional(),
  sku: z.string().optional(),
  inventory: z.number().int().nonnegative().default(0),
  imageUrl: z.string().url().optional(),
  categoryId: z.string().uuid().optional(),
  status: z.enum(['draft', 'published', 'archived']).default('draft'),
});

const updateSupplierProductSchema = z.object({
  name: z.string().min(1).optional(),
  description: z.string().optional(),
  price: z.number().positive().optional(),
  compareAtPrice: z.number().positive().optional(),
  sku: z.string().optional(),
  inventory: z.number().int().nonnegative().optional(),
  imageUrl: z.string().url().optional(),
  categoryId: z.string().uuid().optional(),
  status: z.enum(['draft', 'published', 'archived']).optional(),
});

// ─── Supplier CRUD ─────────────────────────────────────────────

export async function createSupplier(tenantId: string, data: z.infer<typeof createSupplierSchema>) {
  const validated = createSupplierSchema.parse(data);

  const supplier = await prisma.supplier.create({
    data: {
      ...validated,
      tenantId,
    },
  });

  return supplier;
}

export async function getSuppliers(tenantId: string, filters?: {
  type?: string;
  status?: string;
  search?: string;
}) {
  const where: any = { tenantId };

  if (filters?.type) where.type = filters.type;
  if (filters?.status) where.status = filters.status;
  if (filters?.search) {
    where.OR = [
      { name: { contains: filters.search, mode: 'insensitive' } },
      { description: { contains: filters.search, mode: 'insensitive' } },
    ];
  }

  return prisma.supplier.findMany({
    where,
    orderBy: { createdAt: 'desc' },
    include: {
      _count: { select: { supplierAccounts: true, supplierProducts: true } },
    },
  });
}

export async function getSupplier(tenantId: string, supplierId: string) {
  return prisma.supplier.findFirst({
    where: { id: supplierId, tenantId },
    include: {
      supplierAccounts: {
        include: {
          store: { select: { name: true, slug: true } },
        },
      },
      supplierProducts: {
        include: {
          localProduct: { select: { name: true, status: true } },
        },
      },
    },
  });
}

export async function updateSupplier(tenantId: string, supplierId: string, data: z.infer<typeof updateSupplierSchema>) {
  const validated = updateSupplierSchema.parse(data);

  const supplier = await prisma.supplier.findFirst({
    where: { id: supplierId, tenantId },
  });

  if (!supplier) {
    throw new Error('Supplier not found');
  }

  return prisma.supplier.update({
    where: { id: supplierId },
    data: validated,
  });
}

export async function deleteSupplier(tenantId: string, supplierId: string) {
  const supplier = await prisma.supplier.findFirst({
    where: { id: supplierId, tenantId },
  });

  if (!supplier) {
    throw new Error('Supplier not found');
  }

  return prisma.supplier.delete({
    where: { id: supplierId },
  });
}

// ─── Supplier Account Management ───────────────────────────────

export async function connectSupplierAccount(
  tenantId: string,
  storeId: string,
  userId: string,
  data: z.infer<typeof connectSupplierSchema>
) {
  const validated = connectSupplierSchema.parse(data);

  const supplier = await prisma.supplier.findFirst({
    where: { id: validated.supplierId, tenantId },
  });

  if (!supplier) {
    throw new Error('Supplier not found');
  }

  const existingAccount = await prisma.supplierAccount.findFirst({
    where: {
      supplierId: validated.supplierId,
      storeId,
    },
  });

  if (existingAccount) {
    throw new Error('Supplier account already connected');
  }

  return prisma.supplierAccount.create({
    data: {
      supplierId: validated.supplierId,
      storeId,
      userId,
      externalAccountId: validated.externalAccountId || null,
      credentials: validated.credentials || null,
      status: 'PENDING_VERIFICATION',
    },
    include: {
      supplier: true,
      store: { select: { name: true, slug: true } },
    },
  });
}

export async function disconnectSupplierAccount(tenantId: string, storeId: string, supplierId: string) {
  const account = await prisma.supplierAccount.findFirst({
    where: {
      supplierId,
      storeId,
    },
  });

  if (!account) {
    throw new Error('Supplier account not found');
  }

  return prisma.supplierAccount.delete({
    where: { id: account.id },
  });
}

export async function getSupplierAccounts(tenantId: string, storeId: string) {
  return prisma.supplierAccount.findMany({
    where: { storeId },
    include: {
      supplier: true,
      store: { select: { name: true, slug: true } },
    },
    orderBy: { createdAt: 'desc' },
  });
}

// ─── Supplier Product Import ───────────────────────────────────

export async function importSupplierProduct(
  tenantId: string,
  storeId: string,
  userId: string,
  data: z.infer<typeof importProductSchema>
) {
  const validated = importProductSchema.parse(data);

  const supplierProduct = await prisma.supplierProduct.findFirst({
    where: {
      supplierId: validated.supplierId,
      supplierProductId: validated.supplierProductId,
    },
  });

  if (!supplierProduct) {
    throw new Error('Supplier product not found');
  }

  // Check if already imported
  const existing = await prisma.supplierProduct.findFirst({
    where: {
      storeId,
      supplierProductId: validated.supplierProductId,
    },
  });

  if (existing) {
    throw new Error('Product already imported from this supplier');
  }

  const product = await prisma.product.create({
    data: {
      name: validated.name,
      description: validated.description,
      price: validated.price,
      compareAtPrice: validated.compareAtPrice,
      sku: validated.sku,
      inventory: validated.inventory,
      status: validated.status,
      images: validated.imageUrl ? [validated.imageUrl] : [],
      categoryId: validated.categoryId,
      tenantId,
      storeId,
    },
  });

  const importedProduct = await prisma.supplierProduct.create({
    data: {
      supplierId: validated.supplierId,
      supplierProductId: validated.supplierProductId,
      name: validated.name,
      description: validated.description,
      price: validated.price,
      compareAtPrice: validated.compareAtPrice,
      inventory: validated.inventory,
      imageUrl: validated.imageUrl,
      sku: validated.sku,
      status: validated.status,
      tenantId,
      storeId,
      localProductId: product.id,
      syncStatus: 'COMPLETED',
      lastSyncAt: new Date(),
    },
    include: {
      localProduct: true,
      supplier: true,
    },
  });

  return importedProduct;
}

export async function getImportedProducts(
  tenantId: string,
  storeId: string,
  filters?: {
    supplierId?: string;
    syncStatus?: string;
    search?: string;
  }
) {
  const where: any = { storeId };

  if (filters?.supplierId) where.supplierId = filters.supplierId;
  if (filters?.syncStatus) where.syncStatus = filters.syncStatus;
  if (filters?.search) {
    where.OR = [
      { name: { contains: filters.search, mode: 'insensitive' } },
      { sku: { contains: filters.search, mode: 'insensitive' } },
    ];
  }

  return prisma.supplierProduct.findMany({
    where,
    include: {
      supplier: true,
      localProduct: { select: { name: true, price: true, status: true, inventory: true } },
    },
    orderBy: { updatedAt: 'desc' },
  });
}

export async function updateImportedProduct(
  tenantId: string,
  storeId: string,
  supplierProductId: string,
  data: z.infer<typeof updateSupplierProductSchema>
) {
  const validated = updateSupplierProductSchema.parse(data);

  const supplierProduct = await prisma.supplierProduct.findFirst({
    where: {
      supplierProductId,
      storeId,
    },
  });

  if (!supplierProduct) {
    throw new Error('Imported product not found');
  }

  const updated = await prisma.supplierProduct.update({
    where: { id: supplierProduct.id },
    data: validated,
  });

  // Also update local product if it exists
  if (supplierProduct.localProductId) {
    await prisma.product.update({
      where: { id: supplierProduct.localProductId },
      data: {
        name: validated.name,
        description: validated.description,
        price: validated.price,
        compareAtPrice: validated.compareAtPrice,
        sku: validated.sku,
        inventory: validated.inventory,
        status: validated.status,
      },
    });
  }

  return updated;
}

export async function deleteImportedProduct(tenantId: string, storeId: string, supplierProductId: string) {
  const supplierProduct = await prisma.supplierProduct.findFirst({
    where: {
      supplierProductId,
      storeId,
    },
  });

  if (!supplierProduct) {
    throw new Error('Imported product not found');
  }

  // Delete local product if exists
  if (supplierProduct.localProductId) {
    await prisma.product.delete({
      where: { id: supplierProduct.localProductId },
    });
  }

  return prisma.supplierProduct.delete({
    where: { id: supplierProduct.id },
  });
}

// ─── Inventory Sync Engine ─────────────────────────────────────

export async function syncInventory(supplierAccountId: string) {
  const account = await prisma.supplierAccount.findUnique({
    where: { id: supplierAccountId },
    include: {
      supplierProducts: true,
    },
  });

  if (!account) {
    throw new Error('Supplier account not found');
  }

  await prisma.supplierAccount.update({
    where: { id: supplierAccountId },
    data: {
      syncStatus: 'IN_PROGRESS',
      lastSyncAt: new Date(),
    },
  });

  const results: { success: number; failed: number; errors: string[] } = {
    success: 0,
    failed: 0,
    errors: [],
  };

  for (const product of account.supplierProducts) {
    try {
      // In a real implementation, this would call the supplier's API
      // For now, we simulate a sync by updating the local inventory
      const syncRecord = await prisma.inventorySync.create({
        data: {
          supplierProductId: product.id,
          syncStatus: 'COMPLETED',
          lastSyncAt: new Date(),
        },
      });

      // Update local product inventory
      if (product.localProductId) {
        await prisma.product.update({
          where: { id: product.localProductId },
          data: {
            inventory: product.inventory,
          },
        });
      }

      results.success++;
    } catch (error) {
      results.failed++;
      results.errors.push(`Failed to sync product ${product.supplierProductId}: ${error instanceof Error ? error.message : 'Unknown error'}`);

      await prisma.inventorySync.create({
        data: {
          supplierProductId: product.id,
          syncStatus: 'FAILED',
          error: error instanceof Error ? error.message : 'Unknown error',
        },
      });
    }
  }

  await prisma.supplierAccount.update({
    where: { id: supplierAccountId },
    data: {
      syncStatus: results.failed === 0 ? 'COMPLETED' : 'FAILED',
    },
  });

  return results;
}

export async function getSyncHistory(supplierAccountId: string, limit: number = 50) {
  return prisma.inventorySync.findMany({
    where: {
      supplierProduct: {
        supplierAccount: {
          id: supplierAccountId,
        },
      },
    },
    include: {
      supplierProduct: {
        include: {
          supplier: true,
          localProduct: { select: { name: true } },
        },
      },
    },
    orderBy: { createdAt: 'desc' },
    take: limit,
  });
}

// ─── Fulfillment Automation ─────────────────────────────────────

export async function createFulfillment(orderId: string, supplierId: string) {
  const order = await prisma.order.findUnique({
    where: { id: orderId },
    include: {
      items: {
        include: {
          product: {
            include: {
              supplierProduct: true,
            },
          },
        },
      },
    },
  });

  if (!order) {
    throw new Error('Order not found');
  }

  if (order.paymentStatus !== 'PAID') {
    throw new Error('Order must be paid before fulfillment');
  }

  // Check if fulfillment already exists
  const existing = await prisma.fulfillment.findFirst({
    where: { orderId },
  });

  if (existing) {
    throw new Error('Fulfillment already exists for this order');
  }

  // Find supplier product for this order item
  const orderItem = order.items.find((item) => item.product.supplierProduct);
  if (!orderItem?.product.supplierProduct) {
    throw new Error('No supplier product found for order items');
  }

  const fulfillment = await prisma.fulfillment.create({
    data: {
      orderId,
      supplierId,
      status: 'PENDING',
      cost: 0,
      notes: `Auto-fulfillment triggered for order ${order.orderNumber}`,
      metadata: {
        items: order.items.map((item) => ({
          productId: item.productId,
          quantity: item.quantity,
          price: Number(item.price),
        })),
      },
    },
    include: {
      order: { select: { orderNumber: true, customerEmail: true } },
      supplier: true,
    },
  });

  // Update order status
  await prisma.order.update({
    where: { id: orderId },
    data: {
      status: 'FULFILLED',
    },
  });

  return fulfillment;
}

export async function updateFulfillmentStatus(
  fulfillmentId: string,
  status: 'PENDING' | 'PROCESSING' | 'SHIPPED' | 'DELIVERED' | 'FAILED' | 'CANCELLED' | 'RETRYING',
  trackingNumber?: string,
  trackingUrl?: string,
  carrier?: string,
  cost?: number
) {
  const fulfillment = await prisma.fulfillment.findUnique({
    where: { id: fulfillmentId },
  });

  if (!fulfillment) {
    throw new Error('Fulfillment not found');
  }

  const updated = await prisma.fulfillment.update({
    where: { id: fulfillmentId },
    data: {
      status,
      trackingNumber: trackingNumber || fulfillment.trackingNumber,
      trackingUrl: trackingUrl || fulfillment.trackingUrl,
      carrier: carrier || fulfillment.carrier,
      cost: cost !== undefined ? cost : fulfillment.cost,
      updatedAt: new Date(),
    },
  });

  // Update order status based on fulfillment status
  if (status === 'SHIPPED' || status === 'DELIVERED') {
    await prisma.order.update({
      where: { id: fulfillment.orderId },
      data: {
        status: status === 'DELIVERED' ? 'DELIVERED' : 'SHIPPED',
      },
    });
  }

  return updated;
}

export async function getFulfillments(tenantId: string, filters?: {
  orderId?: string;
  status?: string;
  supplierId?: string;
}) {
  const where: any = {
    order: {
      tenantId,
    },
  };

  if (filters?.orderId) where.orderId = filters.orderId;
  if (filters?.status) where.status = filters.status;
  if (filters?.supplierId) where.supplierId = filters.supplierId;

  return prisma.fulfillment.findMany({
    where,
    include: {
      order: {
        select: {
          orderNumber: true,
          customerEmail: true,
          total: true,
          status: true,
        },
      },
      supplier: {
        select: {
          name: true,
          type: true,
        },
      },
    },
    orderBy: { createdAt: 'desc' },
  });
}

export async function getFulfillment(fulfillmentId: string) {
  return prisma.fulfillment.findUnique({
    where: { id: fulfillmentId },
    include: {
      order: {
        select: {
          orderNumber: true,
          customerEmail: true,
          total: true,
          status: true,
          items: {
            include: {
              product: {
                include: {
                  supplierProduct: true,
                },
              },
            },
          },
        },
      },
      supplier: true,
    },
  });
}

// ─── Supplier Directory ────────────────────────────────────────

export async function getSupplierDirectory(filters?: {
  type?: string;
  search?: string;
}) {
  const where: any = {
    status: 'ACTIVE',
  };

  if (filters?.type) where.type = filters.type;
  if (filters?.search) {
    where.OR = [
      { name: { contains: filters.search, mode: 'insensitive' } },
      { description: { contains: filters.search, mode: 'insensitive' }, },
    ];
  }

  return prisma.supplier.findMany({
    where,
    select: {
      id: true,
      name: true,
      type: true,
      description: true,
      logoUrl: true,
      contactEmail: true,
      contactPhone: true,
      _count: {
        select: {
          supplierAccounts: true,
        },
      },
    },
    orderBy: {
      supplierAccounts: {
        _count: 'desc',
      },
    },
  });
}

export async function getSupplierDetails(supplierId: string) {
  return prisma.supplier.findUnique({
    where: { id: supplierId, status: 'ACTIVE' },
    include: {
      supplierAccounts: {
        include: {
          store: { select: { name: true, slug: true } },
        },
      },
      _count: {
        select: {
          supplierAccounts: true,
          supplierProducts: true,
        },
      },
    },
  });
}
