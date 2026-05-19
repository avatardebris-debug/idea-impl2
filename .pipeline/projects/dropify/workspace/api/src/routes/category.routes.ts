import { Router } from 'express';
import { z } from 'zod';
import { slugify } from '../utils/slugify';
import prisma from '../config/db';

const router = Router();

const createCategorySchema = z.object({
  name: z.string().min(1),
  description: z.string().optional(),
  parentId: z.string().uuid().optional(),
});

router.post('/', async (req, res) => {
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

    const data = createCategorySchema.parse(req.body);

    const category = await prisma.category.create({
      data: {
        ...data,
        slug: slugify(data.name),
        storeId: store.id,
        tenantId: store.tenantId,
      },
    });

    res.status(201).json({ category });
  } catch (err) {
    if (err instanceof z.ZodError) {
      res.status(400).json({ error: 'Validation failed', details: err.errors });
      return;
    }
    res.status(500).json({ error: 'Failed to create category' });
  }
});

router.get('/', async (req, res) => {
  const { tenantId } = req;

  const where: any = {};
  if (tenantId) {
    const store = await prisma.store.findUnique({ where: { tenantId } });
    if (store) {
      where.storeId = store.id;
    }
  }

  const categories = await prisma.category.findMany({
    where,
    orderBy: { name: 'asc' },
  });

  res.json({ categories });
});

router.get('/:id', async (req, res) => {
  const { id } = req.params;

  const category = await prisma.category.findUnique({
    where: { id },
    include: {
      children: { select: { id: true, name: true, slug: true } },
      products: { select: { id: true, name: true, price: true } },
    },
  });

  if (!category) {
    res.status(404).json({ error: 'Category not found' });
    return;
  }

  res.json({ category });
});

router.put('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const updateSchema = z.object({
      name: z.string().min(1).optional(),
      description: z.string().optional(),
      parentId: z.string().uuid().optional(),
    });

    const data = updateSchema.parse(req.body);

    const category = await prisma.category.findUnique({ where: { id } });
    if (!category) {
      res.status(404).json({ error: 'Category not found' });
      return;
    }

    const updated = await prisma.category.update({
      where: { id },
      data,
    });

    res.json({ category: updated });
  } catch (err) {
    if (err instanceof z.ZodError) {
      res.status(400).json({ error: 'Validation failed', details: err.errors });
      return;
    }
    res.status(500).json({ error: 'Failed to update category' });
  }
});

router.delete('/:id', async (req, res) => {
  const { id } = req.params;

  const category = await prisma.category.findUnique({ where: { id } });
  if (!category) {
    res.status(404).json({ error: 'Category not found' });
    return;
  }

  await prisma.category.delete({ where: { id } });

  res.json({ message: 'Category deleted' });
});

export default router;
