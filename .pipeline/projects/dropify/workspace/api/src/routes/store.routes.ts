import { v4 as uuidv4 } from 'uuid';
import { Router } from 'express';
import { z } from 'zod';
import prisma from '../config/db';
import { authMiddleware, AuthRequest } from '../middleware/auth.middleware';

const router = Router();

router.use(authMiddleware);

const createStoreSchema = z.object({
  name: z.string().min(1),
  description: z.string().optional(),
  currency: z.string().default('USD'),
  timezone: z.string().default('UTC'),
});

router.post('/', async (req: AuthRequest, res) => {
  try {
    const { name, description, currency, timezone } = createStoreSchema.parse(req.body);

    const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');

    const store = await prisma.store.create({
      data: {
        name,
        slug,
        description,
        currency,
        timezone,
        userId: req.userId!,
        tenantId: uuidv4(),
      },
    });

    res.status(201).json({ store });
  } catch (err) {
    if (err instanceof z.ZodError) {
      res.status(400).json({ error: 'Validation failed', details: err.errors });
      return;
    }
    res.status(500).json({ error: 'Failed to create store' });
  }
});

router.get('/', async (req: AuthRequest, res) => {
  const stores = await prisma.store.findMany({
    where: { userId: req.userId! },
    select: {
      id: true,
      name: true,
      slug: true,
      description: true,
      logoUrl: true,
      currency: true,
      timezone: true,
      status: true,
      createdAt: true,
    },
  });

  res.json({ stores });
});

router.get('/:slug', async (req, res) => {
  const { slug } = req.params;

  const store = await prisma.store.findUnique({
    where: { slug },
    select: {
      id: true,
      name: true,
      slug: true,
      description: true,
      logoUrl: true,
      currency: true,
      timezone: true,
      status: true,
      theme: true,
      createdAt: true,
    },
  });

  if (!store) {
    res.status(404).json({ error: 'Store not found' });
    return;
  }

  res.json({ store });
});

router.put('/:slug', async (req: AuthRequest, res) => {
  try {
    const { slug } = req.params;
    const updateSchema = z.object({
      name: z.string().min(1).optional(),
      description: z.string().optional(),
      currency: z.string().optional(),
      timezone: z.string().optional(),
    });

    const data = updateSchema.parse(req.body);

    const store = await prisma.store.findFirst({
      where: { slug, userId: req.userId! },
    });

    if (!store) {
      res.status(404).json({ error: 'Store not found' });
      return;
    }

    const updated = await prisma.store.update({
      where: { id: store.id },
      data,
    });

    res.json({ store: updated });
  } catch (err) {
    if (err instanceof z.ZodError) {
      res.status(400).json({ error: 'Validation failed', details: err.errors });
      return;
    }
    res.status(500).json({ error: 'Failed to update store' });
  }
});

router.delete('/:slug', async (req: AuthRequest, res) => {
  const { slug } = req.params;

  const store = await prisma.store.findFirst({
    where: { slug, userId: req.userId! },
  });

  if (!store) {
    res.status(404).json({ error: 'Store not found' });
    return;
  }

  await prisma.store.delete({ where: { id: store.id } });

  res.json({ message: 'Store deleted' });
});

export default router;
