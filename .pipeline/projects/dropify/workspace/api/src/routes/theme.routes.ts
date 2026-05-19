import { Router } from 'express';
import { z } from 'zod';
import prisma from '../config/db';
import { ThemeService } from '../services/theme.service';
import { authenticate } from '../middleware/auth.middleware';

const router = Router();

// ─── Schemas ───────────────────────────────────────────────────────────────────

const applyThemeSchema = z.object({
  themeId: z.string(),
});

const colorSchema = z.object({
  primary: z.string().regex(/^#([0-9A-F]{6})$/i).optional(),
  secondary: z.string().regex(/^#([0-9A-F]{6})$/i).optional(),
  background: z.string().regex(/^#([0-9A-F]{6})$/i).optional(),
  text: z.string().regex(/^#([0-9A-F]{6})$/i).optional(),
});

const fontSchema = z.object({
  heading: z.string().min(1).optional(),
  body: z.string().min(1).optional(),
});

const layoutSchema = z.object({
  headerStyle: z.enum(['default', 'minimal', 'transparent']).optional(),
  footerStyle: z.enum(['default', 'minimal', 'hidden']).optional(),
  productGrid: z.enum(['grid', 'list']).optional(),
});

// ─── Routes ───────────────────────────────────────────────────────────────────

/**
 * GET /api/themes
 * Get all available themes with optional filters
 */
router.get('/', async (req: any, res) => {
  try {
    const { category, isOfficial, price } = req.query;

    const themes = await ThemeService.getThemes({
      category: category as string,
      isOfficial: isOfficial === 'true' ? true : isOfficial === 'false' ? false : undefined,
      price: price as 'free' | 'paid' | 'all',
    });

    res.json({ themes });
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch themes' });
  }
});

/**
 * GET /api/themes/:themeId
 * Get a specific theme
 */
router.get('/:themeId', async (req: any, res) => {
  try {
    const theme = await ThemeService.getTheme(req.params.themeId);

    if (!theme) {
      res.status(404).json({ error: 'Theme not found' });
      return;
    }

    res.json({ theme });
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch theme' });
  }
});

/**
 * GET /api/stores/:slug/theme
 * Get current store theme
 */
router.get('/stores/:slug/theme', async (req: any, res) => {
  try {
    const store = await prisma.store.findUnique({
      where: { slug: req.params.slug },
      select: { id: true, theme: true },
    });

    if (!store) {
      res.status(404).json({ error: 'Store not found' });
      return;
    }

    const result = await ThemeService.getStoreTheme(store.id);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch store theme' });
  }
});

/**
 * PUT /api/stores/:slug/theme
 * Apply a theme to store (authenticated)
 */
router.put('/stores/:slug/theme', authenticate, async (req: any, res) => {
  try {
    const { slug } = req.params;
    const { themeId } = applyThemeSchema.parse(req.body);

    const store = await prisma.store.findUnique({
      where: { slug },
      select: { id: true },
    });

    if (!store) {
      res.status(404).json({ error: 'Store not found' });
      return;
    }

    const result = await ThemeService.applyTheme(store.id, themeId, req.user.id);

    if (!result.success) {
      res.status(400).json({ error: result.error });
      return;
    }

    res.json({ success: true, theme: result.theme });
  } catch (error) {
    if (error instanceof z.ZodError) {
      res.status(400).json({ error: 'Validation failed', details: error.errors });
      return;
    }
    res.status(500).json({ error: 'Failed to apply theme' });
  }
});

/**
 * PUT /api/stores/:slug/theme/colors
 * Customize theme colors (authenticated)
 */
router.put('/stores/:slug/theme/colors', authenticate, async (req: any, res) => {
  try {
    const { slug } = req.params;
    const colors = colorSchema.parse(req.body);

    const store = await prisma.store.findUnique({
      where: { slug },
      select: { id: true },
    });

    if (!store) {
      res.status(404).json({ error: 'Store not found' });
      return;
    }

    const result = await ThemeService.customizeColors(store.id, colors);

    if (!result.success) {
      res.status(400).json({ error: result.error });
      return;
    }

    res.json({ success: true, theme: result.theme });
  } catch (error) {
    if (error instanceof z.ZodError) {
      res.status(400).json({ error: 'Validation failed', details: error.errors });
      return;
    }
    res.status(500).json({ error: 'Failed to update colors' });
  }
});

/**
 * PUT /api/stores/:slug/theme/fonts
 * Customize theme fonts (authenticated)
 */
router.put('/stores/:slug/theme/fonts', authenticate, async (req: any, res) => {
  try {
    const { slug } = req.params;
    const fonts = fontSchema.parse(req.body);

    const store = await prisma.store.findUnique({
      where: { slug },
      select: { id: true },
    });

    if (!store) {
      res.status(404).json({ error: 'Store not found' });
      return;
    }

    const result = await ThemeService.customizeFonts(store.id, fonts);

    if (!result.success) {
      res.status(400).json({ error: result.error });
      return;
    }

    res.json({ success: true, theme: result.theme });
  } catch (error) {
    if (error instanceof z.ZodError) {
      res.status(400).json({ error: 'Validation failed', details: error.errors });
      return;
    }
    res.status(500).json({ error: 'Failed to update fonts' });
  }
});

/**
 * PUT /api/stores/:slug/theme/layout
 * Customize theme layout (authenticated)
 */
router.put('/stores/:slug/theme/layout', authenticate, async (req: any, res) => {
  try {
    const { slug } = req.params;
    const layout = layoutSchema.parse(req.body);

    const store = await prisma.store.findUnique({
      where: { slug },
      select: { id: true },
    });

    if (!store) {
      res.status(404).json({ error: 'Store not found' });
      return;
    }

    const result = await ThemeService.customizeLayout(store.id, layout);

    if (!result.success) {
      res.status(400).json({ error: result.error });
      return;
    }

    res.json({ success: true, theme: result.theme });
  } catch (error) {
    if (error instanceof z.ZodError) {
      res.status(400).json({ error: 'Validation failed', details: error.errors });
      return;
    }
    res.status(500).json({ error: 'Failed to update layout' });
  }
});

/**
 * PUT /api/stores/:slug/theme/reset
 * Reset theme to defaults (authenticated)
 */
router.put('/stores/:slug/theme/reset', authenticate, async (req: any, res) => {
  try {
    const { slug } = req.params;

    const store = await prisma.store.findUnique({
      where: { slug },
      select: { id: true },
    });

    if (!store) {
      res.status(404).json({ error: 'Store not found' });
      return;
    }

    const result = await ThemeService.resetTheme(store.id);

    if (!result.success) {
      res.status(400).json({ error: result.error });
      return;
    }

    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: 'Failed to reset theme' });
  }
});

export default router;
