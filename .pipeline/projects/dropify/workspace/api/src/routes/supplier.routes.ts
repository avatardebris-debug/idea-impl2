import { Router } from 'express';
import { z } from 'zod';
import * as supplierService from '../services/supplier.service';
import { AuthRequest } from '../middleware/auth.middleware';

const router = Router();

// ─── Zod Schemas ──────────────────────────────────────────

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

const updateImportedProductSchema = z.object({
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

const syncInventorySchema = z.object({
  supplierAccountId: z.string().uuid(),
});

const createFulfillmentSchema = z.object({
  orderId: z.string().uuid(),
  supplierId: z.string().uuid(),
});

const updateFulfillmentSchema = z.object({
  status: z.enum(['PENDING', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'FAILED', 'CANCELLED', 'RETRYING']),
  trackingNumber: z.string().optional(),
  trackingUrl: z.string().optional(),
  carrier: z.string().optional(),
  cost: z.number().optional(),
});

// ─── Supplier CRUD Routes ─────────────────────────────────

router.post('/suppliers', async (req: AuthRequest, res, next) => {
  try {
    const validated = createSupplierSchema.parse(req.body);
    const supplier = await supplierService.createSupplier(req.tenantId, validated);
    res.status(201).json(supplier);
  } catch (error) {
    next(error);
  }
});

router.get('/suppliers', async (req: AuthRequest, res, next) => {
  try {
    const { type, status, search } = req.query;
    const suppliers = await supplierService.getSuppliers(req.tenantId, {
      type: type as string,
      status: status as string,
      search: search as string,
    });
    res.json(suppliers);
  } catch (error) {
    next(error);
  }
});

router.get('/suppliers/:id', async (req: AuthRequest, res, next) => {
  try {
    const supplier = await supplierService.getSupplier(req.tenantId, req.params.id);
    if (!supplier) {
      return res.status(404).json({ error: 'Supplier not found' });
    }
    res.json(supplier);
  } catch (error) {
    next(error);
  }
});

router.put('/suppliers/:id', async (req: AuthRequest, res, next) => {
  try {
    const validated = updateSupplierSchema.parse(req.body);
    const supplier = await supplierService.updateSupplier(req.tenantId, req.params.id, validated);
    res.json(supplier);
  } catch (error) {
    next(error);
  }
});

router.delete('/suppliers/:id', async (req: AuthRequest, res, next) => {
  try {
    await supplierService.deleteSupplier(req.tenantId, req.params.id);
    res.status(204).send();
  } catch (error) {
    next(error);
  }
});

// ─── Supplier Account Routes ─────────────────────────────

router.post('/stores/:storeId/supplier-accounts', async (req: AuthRequest, res, next) => {
  try {
    const validated = connectSupplierSchema.parse(req.body);
    const account = await supplierService.connectSupplierAccount(
      req.tenantId,
      req.params.storeId,
      req.userId,
      validated
    );
    res.status(201).json(account);
  } catch (error) {
    next(error);
  }
});

router.delete('/stores/:storeId/supplier-accounts/:supplierId', async (req: AuthRequest, res, next) => {
  try {
    await supplierService.disconnectSupplierAccount(req.tenantId, req.params.storeId, req.params.supplierId);
    res.status(204).send();
  } catch (error) {
    next(error);
  }
});

router.get('/stores/:storeId/supplier-accounts', async (req: AuthRequest, res, next) => {
  try {
    const accounts = await supplierService.getSupplierAccounts(req.tenantId, req.params.storeId);
    res.json(accounts);
  } catch (error) {
    next(error);
  }
});

// ─── Supplier Product Import Routes ─────────────────────

router.post('/stores/:storeId/import-products', async (req: AuthRequest, res, next) => {
  try {
    const validated = importProductSchema.parse(req.body);
    const product = await supplierService.importSupplierProduct(
      req.tenantId,
      req.params.storeId,
      req.userId,
      validated
    );
    res.status(201).json(product);
  } catch (error) {
    next(error);
  }
});

router.get('/stores/:storeId/imported-products', async (req: AuthRequest, res, next) => {
  try {
    const { supplierId, syncStatus, search } = req.query;
    const products = await supplierService.getImportedProducts(req.tenantId, req.params.storeId, {
      supplierId: supplierId as string,
      syncStatus: syncStatus as string,
      search: search as string,
    });
    res.json(products);
  } catch (error) {
    next(error);
  }
});

router.put('/stores/:storeId/imported-products/:supplierProductId', async (req: AuthRequest, res, next) => {
  try {
    const validated = updateImportedProductSchema.parse(req.body);
    const product = await supplierService.updateImportedProduct(
      req.tenantId,
      req.params.storeId,
      req.params.supplierProductId,
      validated
    );
    res.json(product);
  } catch (error) {
    next(error);
  }
});

router.delete('/stores/:storeId/imported-products/:supplierProductId', async (req: AuthRequest, res, next) => {
  try {
    await supplierService.deleteImportedProduct(req.tenantId, req.params.storeId, req.params.supplierProductId);
    res.status(204).send();
  } catch (error) {
    next(error);
  }
});

// ─── Inventory Sync Routes ─────────────────────────────

router.post('/sync-inventory', async (req: AuthRequest, res, next) => {
  try {
    const validated = syncInventorySchema.parse(req.body);
    const result = await supplierService.syncInventory(validated.supplierAccountId);
    res.json(result);
  } catch (error) {
    next(error);
  }
});

router.get('/sync-history/:supplierAccountId', async (req: AuthRequest, res, next) => {
  try {
    const limit = parseInt(req.query.limit as string) || 50;
    const history = await supplierService.getSyncHistory(req.params.supplierAccountId, limit);
    res.json(history);
  } catch (error) {
    next(error);
  }
});

// ─── Fulfillment Routes ─────────────────────────────

router.post('/fulfillments', async (req: AuthRequest, res, next) => {
  try {
    const validated = createFulfillmentSchema.parse(req.body);
    const fulfillment = await supplierService.createFulfillment(validated.orderId, validated.supplierId);
    res.status(201).json(fulfillment);
  } catch (error) {
    next(error);
  }
});

router.put('/fulfillments/:id', async (req: AuthRequest, res, next) => {
  try {
    const validated = updateFulfillmentSchema.parse(req.body);
    const fulfillment = await supplierService.updateFulfillmentStatus(
      req.params.id,
      validated.status,
      validated.trackingNumber,
      validated.trackingUrl,
      validated.carrier,
      validated.cost
    );
    res.json(fulfillment);
  } catch (error) {
    next(error);
  }
});

router.get('/fulfillments', async (req: AuthRequest, res, next) => {
  try {
    const { orderId, status, supplierId } = req.query;
    const fulfillments = await supplierService.getFulfillments(req.tenantId, {
      orderId: orderId as string,
      status: status as string,
      supplierId: supplierId as string,
    });
    res.json(fulfillments);
  } catch (error) {
    next(error);
  }
});

router.get('/fulfillments/:id', async (req: AuthRequest, res, next) => {
  try {
    const fulfillment = await supplierService.getFulfillment(req.params.id);
    if (!fulfillment) {
      return res.status(404).json({ error: 'Fulfillment not found' });
    }
    res.json(fulfillment);
  } catch (error) {
    next(error);
  }
});

// ─── Supplier Directory Routes ──────────────────────────

router.get('/directory', async (req: AuthRequest, res, next) => {
  try {
    const { type, search } = req.query;
    const suppliers = await supplierService.getSupplierDirectory({
      type: type as string,
      search: search as string,
    });
    res.json(suppliers);
  } catch (error) {
    next(error);
  }
});

router.get('/directory/:id', async (req: AuthRequest, res, next) => {
  try {
    const supplier = await supplierService.getSupplierDetails(req.params.id);
    if (!supplier) {
      return res.status(404).json({ error: 'Supplier not found' });
    }
    res.json(supplier);
  } catch (error) {
    next(error);
  }
});

export default router;
