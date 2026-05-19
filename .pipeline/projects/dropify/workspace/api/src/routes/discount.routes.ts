import { Router } from 'express';
import { z } from 'zod';
import prisma from '../config/db';
import { DiscountCodeService } from '../services/discount.service';
import { authenticate } from '../middleware/auth.middleware';

const router = Router();

// ─── Schemas ───────────────────────────────────────────────────────────────────

const createDiscountSchema = z.object({
  code: z.string().min(1).max(50),
  type: z.enum(['percentage', 'fixed', 'free_shipping']),
  value: z.number().min(0),
  usageLimit: z.number().int().positive().optional(),
  startDate: z.string().optional(),
  endDate: z.string().optional(),
  minimumOrderAmount: z.number().min(0).optional(),
});

const validateDiscountSchema = z.object({
  code: z.string().min(1),
});

// ─── Routes ───────────────────────────────────────────────────────────────────

/**
 * GET /api/discounts
 * Get all discount codes for the store
 */
router.get('/', authenticate, async (req: any, res) => {
  try {
    const store = await prisma.store.findFirst({
      where: { ownerId: req.user.id },
      select: { id: true },
    });

    if (!store) {
      res.status(404).json({ error: 'Store not found' });
      return;
    }

    const discountCodes = await DiscountCodeService.getDiscountCodes(store.id);
    res.json(discountCodes);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch discount codes' });
  }
});

/**
 * POST /api/discounts
 * Create a new discount code
 */
router.post('/', authenticate, async (req: any, res) => {
  try {
    const store = await prisma.store.findFirst({
      where: { ownerId: req.user.id },
      select: { id: true },
    });

    if (!store) {
      res.status(404).json({ error: 'Store not found' });
      return;
    }

    const data = createDiscountSchema.parse(req.body);
    const result = await DiscountCodeService.createDiscountCode(store.id, req.user.id, data);

    if (!result.success) {
      res.status(400).json({ error: result.error });
      return;
    }

    res.status(201).json(result.discountCode);
  } catch (error) {
    if (error instanceof z.ZodError) {
      res.status(400).json({ error: 'Validation failed', details: error.errors });
      return;
    }
    res.status(500).json({ error: 'Failed to create discount code' });
  }
});

/**
 * POST /api/discounts/validate
 * Validate a discount code (public endpoint for storefront)
 */
router.post('/validate', async (req: any, res) => {
  try {
    const { code, storeId, orderAmount } = validateDiscountSchema.extend({
      storeId: z.string(),
      orderAmount: z.number().min(0),
    }).parse(req.body);

    const validation = await DiscountCodeService.validateDiscountCode(code, storeId, orderAmount);
    res.json(validation);
  } catch (error) {
    if (error instanceof z.ZodError) {
      res.status(400).json({ error: 'Validation failed', details: error.errors });
      return;
    }
    res.status(500).json({ error: 'Failed to validate discount code' });
  }
});

/**
 * PUT /api/discounts/:code/deactivate
 * Deactivate a discount code
 */
router.put('/:code/deactivate', authenticate, async (req: any, res) => {
  try {
    const store = await prisma.store.findFirst({
      where: { ownerId: req.user.id },
      select: { id: true },
    });

    if (!store) {
      res.status(404).json({ error: 'Store not found' });
      return;
    }

    const result = await DiscountCodeService.deactivateDiscountCode(req.params.code, store.id);

    if (!result.success) {
      res.status(400).json({ error: result.error });
      return;
    }

    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: 'Failed to deactivate discount code' });
  }
});

/**
 * DELETE /api/discounts/:code
 * Delete a discount code
 */
router.delete('/:code', authenticate, async (req: any, res) => {
  try {
    const store = await prisma.store.findFirst({
      where: { ownerId: req.user.id },
      select: { id: true },
    });

    if (!store) {
      res.status(404).json({ error: 'Store not found' });
      return;
    }

    const result = await DiscountCodeService.deleteDiscountCode(req.params.code, store.id);

    if (!result.success) {
      res.status(400).json({ error: result.error });
      return;
    }

    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: 'Failed to delete discount code' });
  }
});

/**
 * POST /api/discounts/:code/apply
 * Apply a discount code to an order
 */
router.post('/:code/apply', authenticate, async (req: any, res) => {
  try {
    const store = await prisma.store.findFirst({
      where: { ownerId: req.user.id },
      select: { id: true },
    });

    if (!store) {
      res.status(404).json({ error: 'Store not found' });
      return;
    }

    const { orderId } = z.object({ orderId: z.string() }).parse(req.body);

    const result = await DiscountCodeService.applyDiscountCode(orderId, req.params.code, store.id);

    if (!result.success) {
      res.status(400).json({ error: result.error });
      return;
    }

    res.json({ success: true, discountAmount: result.discountAmount });
  } catch (error) {
    if (error instanceof z.ZodError) {
      res.status(400).json({ error: 'Validation failed', details: error.errors });
      return;
    }
    res.status(500).json({ error: 'Failed to apply discount code' });
  }
});

export default router;
