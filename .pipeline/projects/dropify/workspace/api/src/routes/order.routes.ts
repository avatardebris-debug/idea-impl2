import { Router } from 'express';
import { z } from 'zod';
import prisma from '../config/db';
import { authMiddleware, AuthRequest } from '../middleware/auth.middleware';

const router = Router();

router.use(authMiddleware);

const updateOrderStatusSchema = z.object({
  status: z.enum(['PENDING', 'PAID', 'FULFILLED', 'SHIPPED', 'DELIVERED', 'CANCELLED']).optional(),
  paymentStatus: z.enum(['PENDING', 'PAID', 'FAILED', 'REFUNDED']).optional(),
});

// Get all orders for the seller's stores
router.get('/', async (req: AuthRequest, res) => {
  const { tenantId } = req;
  const { status, paymentStatus, page = '1', limit = '20' } = req.query;

  if (!tenantId) {
    res.status(400).json({ error: 'Tenant not resolved' });
    return;
  }

  const store = await prisma.store.findFirst({ where: { tenantId } });
  if (!store) {
    res.status(404).json({ error: 'Store not found' });
    return;
  }

  const where: any = { storeId: store.id };
  if (status) where.status = status;
  if (paymentStatus) where.paymentStatus = paymentStatus;

  const skip = (parseInt(page as string) - 1) * parseInt(limit as string);
  const take = parseInt(limit as string);

  const [orders, total] = await Promise.all([
    prisma.order.findMany({
      where,
      skip,
      take,
      orderBy: { createdAt: 'desc' },
      include: {
        items: {
          include: {
            product: { select: { id: true, name: true, images: true } },
            variant: { select: { id: true, name: true, option: true } },
          },
        },
      },
    }),
    prisma.order.count({ where }),
  ]);

  res.json({
    orders,
    pagination: {
      page: parseInt(page as string),
      limit: take,
      total,
      totalPages: Math.ceil(total / take),
    },
  });
});

// Get single order details
router.get('/:orderId', async (req: AuthRequest, res) => {
  const { tenantId } = req;
  const { orderId } = req.params;

  if (!tenantId) {
    res.status(400).json({ error: 'Tenant not resolved' });
    return;
  }

  const store = await prisma.store.findFirst({ where: { tenantId } });
  if (!store) {
    res.status(404).json({ error: 'Store not found' });
    return;
  }

  const order = await prisma.order.findFirst({
    where: { id: orderId, storeId: store.id },
    include: {
      items: {
        include: {
          product: { select: { id: true, name: true, images: true } },
          variant: { select: { id: true, name: true, option: true } },
        },
      },
    },
  });

  if (!order) {
    res.status(404).json({ error: 'Order not found' });
    return;
  }

  res.json({ order });
});

// Update order status (seller only)
router.patch('/:orderId', async (req: AuthRequest, res) => {
  const { tenantId } = req;
  const { orderId } = req.params;

  if (!tenantId) {
    res.status(400).json({ error: 'Tenant not resolved' });
    return;
  }

  const store = await prisma.store.findFirst({ where: { tenantId } });
  if (!store) {
    res.status(404).json({ error: 'Store not found' });
    return;
  }

  const { status, paymentStatus } = updateOrderStatusSchema.parse(req.body);

  const order = await prisma.order.findFirst({
    where: { id: orderId, storeId: store.id },
  });

  if (!order) {
    res.status(404).json({ error: 'Order not found' });
    return;
  }

  const updatedOrder = await prisma.order.update({
    where: { id: orderId },
    data: {
      ...(status && { status }),
      ...(paymentStatus && { paymentStatus }),
    },
  });

  res.json({ order: updatedOrder });
});

export default router;
