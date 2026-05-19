import { Router } from 'express';
import { z } from 'zod';
import prisma from '../config/db';

const router = Router();

const updateThemeSchema = z.object({
  theme: z.object({
    colors: z.object({
      primary: z.string().optional(),
      secondary: z.string().optional(),
      background: z.string().optional(),
      text: z.string().optional(),
    }).optional(),
    fonts: z.object({
      heading: z.string().optional(),
      body: z.string().optional(),
    }).optional(),
    layout: z.object({
      headerStyle: z.enum(['default', 'minimal', 'transparent']).optional(),
      footerStyle: z.enum(['default', 'minimal', 'hidden']).optional(),
      productGrid: z.enum(['grid', 'list']).optional(),
    }).optional(),
  }).optional(),
});

router.get('/:slug/theme', async (req, res) => {
  const { slug } = req.params;

  const store = await prisma.store.findUnique({
    where: { slug },
    select: { theme: true },
  });

  if (!store) {
    res.status(404).json({ error: 'Store not found' });
    return;
  }

  res.json({ theme: store.theme || {} });
});

router.put('/:slug/theme', async (req, res) => {
  try {
    const { slug } = req.params;
    const { theme } = updateThemeSchema.parse(req.body);

    const store = await prisma.store.findUnique({ where: { slug } });
    if (!store) {
      res.status(404).json({ error: 'Store not found' });
      return;
    }

    const updated = await prisma.store.update({
      where: { id: store.id },
      data: { theme },
    });

    res.json({ theme: updated.theme });
  } catch (err) {
    if (err instanceof z.ZodError) {
      res.status(400).json({ error: 'Validation failed', details: err.errors });
      return;
    }
    res.status(500).json({ error: 'Failed to update theme' });
  }
});

export default router;
