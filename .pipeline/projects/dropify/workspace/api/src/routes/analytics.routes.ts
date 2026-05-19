import { Router } from 'express';
import { z } from 'zod';
import prisma from '../config/db';
import { AnalyticsService } from '../services/analytics.service';
import { authenticate } from '../middleware/auth.middleware';

const router = Router();

// ─── Schemas ───────────────────────────────────────────────────────────────────

const dateRangeSchema = z.object({
  startDate: z.string().transform((val) => new Date(val)),
  endDate: z.string().transform((val) => new Date(val)),
});

// ─── Routes ───────────────────────────────────────────────────────────────────

/**
 * GET /api/analytics/sales
 * Get sales summary
 */
router.get('/sales', authenticate, async (req: any, res) => {
  try {
    const { startDate, endDate } = dateRangeSchema.parse(req.query);

    const store = await prisma.store.findFirst({
      where: { ownerId: req.user.id },
      select: { id: true },
    });

    if (!store) {
      res.status(404).json({ error: 'Store not found' });
      return;
    }

    const salesSummary = await AnalyticsService.getSalesSummary(store.id, startDate, endDate);
    res.json(salesSummary);
  } catch (error) {
    if (error instanceof z.ZodError) {
      res.status(400).json({ error: 'Validation failed', details: error.errors });
      return;
    }
    res.status(500).json({ error: 'Failed to fetch sales analytics' });
  }
});

/**
 * GET /api/analytics/products
 * Get product performance
 */
router.get('/products', authenticate, async (req: any, res) => {
  try {
    const { startDate, endDate } = dateRangeSchema.parse(req.query);

    const store = await prisma.store.findFirst({
      where: { ownerId: req.user.id },
      select: { id: true },
    });

    if (!store) {
      res.status(404).json({ error: 'Store not found' });
      return;
    }

    const productPerformance = await AnalyticsService.getProductPerformance(store.id, startDate, endDate);
    res.json(productPerformance);
  } catch (error) {
    if (error instanceof z.ZodError) {
      res.status(400).json({ error: 'Validation failed', details: error.errors });
      return;
    }
    res.status(500).json({ error: 'Failed to fetch product analytics' });
  }
});

/**
 * GET /api/analytics/customers
 * Get customer analytics
 */
router.get('/customers', authenticate, async (req: any, res) => {
  try {
    const { startDate, endDate } = dateRangeSchema.parse(req.query);

    const store = await prisma.store.findFirst({
      where: { ownerId: req.user.id },
      select: { id: true },
    });

    if (!store) {
      res.status(404).json({ error: 'Store not found' });
      return;
    }

    const customerAnalytics = await AnalyticsService.getCustomerAnalytics(store.id, startDate, endDate);
    res.json(customerAnalytics);
  } catch (error) {
    if (error instanceof z.ZodError) {
      res.status(400).json({ error: 'Validation failed', details: error.errors });
      return;
    }
    res.status(500).json({ error: 'Failed to fetch customer analytics' });
  }
});

/**
 * GET /api/analytics/traffic
 * Get traffic analytics
 */
router.get('/traffic', authenticate, async (req: any, res) => {
  try {
    const { startDate, endDate } = dateRangeSchema.parse(req.query);

    const store = await prisma.store.findFirst({
      where: { ownerId: req.user.id },
      select: { id: true },
    });

    if (!store) {
      res.status(404).json({ error: 'Store not found' });
      return;
    }

    const trafficAnalytics = await AnalyticsService.getTrafficAnalytics(store.id, startDate, endDate);
    res.json(trafficAnalytics);
  } catch (error) {
    if (error instanceof z.ZodError) {
      res.status(400).json({ error: 'Validation failed', details: error.errors });
      return;
    }
    res.status(500).json({ error: 'Failed to fetch traffic analytics' });
  }
});

/**
 * GET /api/analytics/inventory/alerts
 * Get inventory alerts
 */
router.get('/inventory/alerts', authenticate, async (req: any, res) => {
  try {
    const store = await prisma.store.findFirst({
      where: { ownerId: req.user.id },
      select: { id: true },
    });

    if (!store) {
      res.status(404).json({ error: 'Store not found' });
      return;
    }

    const alerts = await AnalyticsService.getInventoryAlerts(store.id);
    res.json(alerts);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch inventory alerts' });
  }
});

/**
 * GET /api/analytics/dashboard
 * Get comprehensive dashboard data
 */
router.get('/dashboard', authenticate, async (req: any, res) => {
  try {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30); // Last 30 days

    const store = await prisma.store.findFirst({
      where: { ownerId: req.user.id },
      select: { id: true },
    });

    if (!store) {
      res.status(404).json({ error: 'Store not found' });
      return;
    }

    const [sales, products, customers, traffic, alerts] = await Promise.all([
      AnalyticsService.getSalesSummary(store.id, startDate, endDate),
      AnalyticsService.getProductPerformance(store.id, startDate, endDate),
      AnalyticsService.getCustomerAnalytics(store.id, startDate, endDate),
      AnalyticsService.getTrafficAnalytics(store.id, startDate, endDate),
      AnalyticsService.getInventoryAlerts(store.id),
    ]);

    res.json({
      sales,
      products: products.slice(0, 10), // Top 10
      customers,
      traffic,
      inventoryAlerts: alerts,
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch dashboard data' });
  }
});

export default router;
