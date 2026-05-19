import { Router } from 'express';
import { z } from 'zod';
import Stripe from 'stripe';
import prisma from '../config/db';
import { env } from '../config/env';

const router = Router();

const stripe = new Stripe(env.STRIPE_SECRET_KEY, { apiVersion: '2023-10-16' as any });

const checkoutSchema = z.object({
  shippingAddress: z.object({
    line1: z.string(),
    line2: z.string().optional(),
    city: z.string(),
    state: z.string(),
    postalCode: z.string(),
    country: z.string(),
  }),
  customerEmail: z.string().email(),
  customerName: z.string(),
});

router.post('/create-checkout-session', async (req, res) => {
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

    const { shippingAddress, customerEmail, customerName } = checkoutSchema.parse(req.body);

    const cart = await prisma.cart.findFirst({
      where: { storeId: store.id },
      include: { items: { include: { product: true, variant: true } } },
    });

    if (!cart || cart.items.length === 0) {
      res.status(400).json({ error: 'Cart is empty' });
      return;
    }

    const lineItems = cart.items.map((item) => {
      const price = item.variant
        ? (item.product.price as number) + (item.variant.priceDelta || 0)
        : (item.product.price as number);

      return {
        price_data: {
          currency: (store.currency || 'usd').toLowerCase(),
          product_data: {
            name: item.product.name,
            images: item.product.images || [],
          },
          unit_amount: Math.round(price * 100),
        },
        quantity: item.quantity,
      };
    });

    const order = await prisma.order.create({
      data: {
        orderNumber: `ORD-${Date.now()}`,
        status: 'PENDING',
        paymentStatus: 'PENDING',
        subtotal: cart.items.reduce((sum, item) => {
          const price = item.variant
            ? (item.product.price as number) + (item.variant.priceDelta || 0)
            : (item.product.price as number);
          return sum + price * item.quantity;
        }, 0),
        tax: 0,
        shipping: 0,
        total: cart.items.reduce((sum, item) => {
          const price = item.variant
            ? (item.product.price as number) + (item.variant.priceDelta || 0)
            : (item.product.price as number);
          return sum + price * item.quantity;
        }, 0),
        customerEmail,
        customerName,
        shippingAddress,
        tenantId: store.tenantId,
        storeId: store.id,
        items: {
          create: cart.items.map((item) => ({
            productId: item.productId,
            variantId: item.variantId || null,
            quantity: item.quantity,
            price: item.variant
              ? (item.product.price as number) + (item.variant.priceDelta || 0)
              : (item.product.price as number),
            tenantId: store.tenantId,
          })),
        },
      },
    });

    const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      line_items: lineItems,
      mode: 'payment',
      customer_email: customerEmail,
      metadata: {
        orderId: order.id,
        storeId: store.id,
      },
      success_url: `${env.FRONTEND_URL}/tenant/${store.slug}/order-confirmation/${order.id}?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${env.FRONTEND_URL}/tenant/${store.slug}/cart`,
    });

    await prisma.order.update({
      where: { id: order.id },
      data: { stripeSessionId: session.id },
    });

    res.json({ sessionId: session.id, url: session.url });
  } catch (err) {
    if (err instanceof z.ZodError) {
      res.status(400).json({ error: 'Validation failed', details: err.errors });
      return;
    }
    res.status(500).json({ error: 'Failed to create checkout session' });
  }
});

router.post('/webhook', async (req, res) => {
  const sig = req.headers['stripe-signature'] as string;
  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(req.body, sig, env.STRIPE_WEBHOOK_SECRET);
  } catch {
    res.status(400).json({ error: 'Webhook signature verification failed' });
    return;
  }

  if (event.type === 'checkout.session.completed') {
    const session = event.data.object as Stripe.Checkout.Session;
    const orderId = session.metadata?.orderId;

    if (orderId) {
      await prisma.order.update({
        where: { id: orderId },
        data: {
          status: 'PAID',
          paymentStatus: 'PAID',
        },
      });
    }
  }

  res.json({ received: true });
});

export default router;
