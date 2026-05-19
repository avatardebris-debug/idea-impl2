import { Router } from 'express';
import { z } from 'zod';
import { slugify } from '../utils/slugify';
import prisma from '../config/db';
import { authMiddleware, AuthRequest } from '../middleware/auth.middleware';

const router = Router();

const createProductSchema = z.object({
  name: z.string().min(1),
  description: z.string().optional(),
  price: z.number().positive(),
  compareAtPrice: z.number().positive().optional(),
  sku: z.string().optional(),
  inventory: z.number().int().nonnegative().default(0),
  images: z.array(z.string()).default([]),
  categoryId: z.string().uuid().optional(),
  variants: z.array(z.object({
    name: z.string(),
    option: z.string(),
    priceDelta: z.number().default(0),
    sku: z.string().optional(),
    inventory: z.number().int().nonnegative().default(0),
  })).default([]),
  tags: z.array(z.string()).default([]),
  status: z.enum(['draft', 'published', 'archived']).default('draft'),
});

router.post('/', async (req: AuthRequest, res) => {
  try {
    const { tenantId } = req;
    if (!tenantId) {
      res.status(400).json({ error: 'Tenant not resolved' });
      return;
    }

    const store = await prisma.store.findUnique({ where: { tenantId } });
    if (!store) {
      res.status(404).json({ error: 'Store not found' });
      return;
    }

    const data = createProductSchema.parse(req.body);

    const product = await prisma.product.create({
      data: {
        ...data,
        slug: slugify(data.name),
        storeId: store.id,
        userId: req.userId!,
        tenantId: store.tenantId,
        variants: data.variants.length > 0
          ? {
              create: data.variants.map((v) => ({
                name: v.name,
                option: v.option,
                priceDelta: v.priceDelta,
                sku: v.sku || null,
                inventory: v.inventory,
                tenantId: store.tenantId,
              })),
            }
          : undefined,
      },
      include: { variants: true },
    });

    res.status(201).json({ product });
  } catch (err) {
    if (err instanceof z.ZodError) {
      res.status(400).json({ error: 'Validation failed', details: err.errors });
      return;
    }
    res.status(500).json({ error: 'Failed to create product' });
  }
});

router.get('/', async (req, res) => {
  const { tenantId } = req;
  const { status, categoryId, search } = req.query;

  const where: any = {};

  if (tenantId) {
    const store = await prisma.store.findUnique({ where: { tenantId } });
    if (store) {
      where.storeId = store.id;
    }
  }

  if (status) where.status = status;
  if (categoryId) where.categoryId = categoryId;
  if (search) where.name = { contains: search as string, mode: 'insensitive' };

  const products = await prisma.product.findMany({
    where,
    orderBy: { createdAt: 'desc' },
    include: {
      category: { select: { name: true } },
      images: true,
    },
  });

  res.json({ products });
});

router.get('/:id', async (req, res) => {
  const { id } = req.params;

  const product = await prisma.product.findUnique({
    where: { id },
    include: {
      category: { select: { name: true } },
      images: true,
      store: { select: { name: true, slug: true } },
    },
  });

  if (!product) {
    res.status(404).json({ error: 'Product not found' });
    return;
  }

  res.json({ product });
});

router.put('/:id', async (req: AuthRequest, res) => {
  try {
    const { id } = req.params;
    const updateSchema = z.object({
      name: z.string().min(1).optional(),
      description: z.string().optional(),
      price: z.number().positive().optional(),
      compareAtPrice: z.number().positive().optional(),
      sku: z.string().optional(),
      inventory: z.number().int().nonnegative().optional(),
      images: z.array(z.string()).optional(),
      categoryId: z.string().uuid().optional(),
      variants: z.array(z.object({
        name: z.string(),
        option: z.string(),
        priceDelta: z.number().default(0),
        sku: z.string().optional(),
        inventory: z.number().int().nonnegative().default(0),
      })).optional(),
      tags: z.array(z.string()).optional(),
      status: z.enum(['draft', 'published', 'archived']).optional(),
    });

    const data = updateSchema.parse(req.body);

    const product = await prisma.product.findUnique({ where: { id } });
    if (!product) {
      res.status(404).json({ error: 'Product not found' });
      return;
    }

    const updated = await prisma.product.update({
      where: { id },
      data,
    });

    res.json({ product: updated });
  } catch (err) {
    if (err instanceof z.ZodError) {
      res.status(400).json({ error: 'Validation failed', details: err.errors });
      return;
    }
    res.status(500).json({ error: 'Failed to update product' });
  }
});

router.delete('/:id', async (req: AuthRequest, res) => {
  const { id } = req.params;

  const product = await prisma.product.findUnique({ where: { id } });
  if (!product) {
    res.status(404).json({ error: 'Product not found' });
    return;
  }

  await prisma.product.delete({ where: { id } });

  res.json({ message: 'Product deleted' });
});

export default router;
