import { Router } from 'express';
import { z } from 'zod';
import prisma from '../config/db';

const router = Router();

const addItemSchema = z.object({
  productId: z.string().uuid(),
  variantId: z.string().uuid().optional(),
  quantity: z.number().int().positive().default(1),
});

router.get('/me', async (req, res) => {
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

  const cart = await prisma.cart.findFirst({
    where: { storeId: store.id },
    include: {
      items: {
        include: {
          product: {
            select: {
              id: true,
              name: true,
              price: true,
              images: true,
              slug: true,
            },
          },
          variant: {
            select: {
              id: true,
              name: true,
              option: true,
              priceDelta: true,
            },
          },
        },
      },
    },
  });

  if (!cart) {
    res.json({ cart: { id: '', items: [], subtotal: 0 } });
    return;
  }

  res.json({ cart });
});

router.post('/items', async (req, res) => {
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

    const { productId, variantId, quantity } = addItemSchema.parse(req.body);

    const product = await prisma.product.findUnique({ where: { id: productId } });
    if (!product) {
      res.status(404).json({ error: 'Product not found' });
      return;
    }

    let cart = await prisma.cart.findFirst({ where: { storeId: store.id } });
    if (!cart) {
      cart = await prisma.cart.create({
        data: { storeId: store.id, tenantId: store.tenantId },
      });
    }

    const existingItem = await prisma.cartItem.findFirst({
      where: {
        cartId: cart.id,
        productId,
        variantId: variantId || null,
      },
    });

    if (existingItem) {
      await prisma.cartItem.update({
        where: { id: existingItem.id },
        data: { quantity: existingItem.quantity + quantity },
      });
    } else {
      await prisma.cartItem.create({
        data: {
          cartId: cart.id,
          productId,
          variantId: variantId || null,
          quantity,
          price: variantId
            ? (product.price as number) + ((await prisma.productVariant.findUnique({ where: { id: variantId } }))?.priceDelta || 0),
          product: { connect: { id: productId } },
          variant: variantId ? { connect: { id: variantId } } : undefined,
        },
      });
    }

    res.json({ message: 'Item added to cart' });
  } catch (err) {
    if (err instanceof z.ZodError) {
      res.status(400).json({ error: 'Validation failed', details: err.errors });
      return;
    }
    res.status(500).json({ error: 'Failed to add item to cart' });
  }
});

router.put('/items/:itemId', async (req, res) => {
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

    const { itemId } = req.params;
    const { quantity } = z.object({ quantity: z.number().int().positive() }).parse(req.body);

    const item = await prisma.cartItem.findFirst({ where: { id: itemId, cart: { storeId: store.id } } });
    if (!item) {
      res.status(404).json({ error: 'Cart item not found' });
      return;
    }

    await prisma.cartItem.update({ where: { id: itemId }, data: { quantity } });
    res.json({ message: 'Cart item updated' });
  } catch (err) {
    if (err instanceof z.ZodError) {
      res.status(400).json({ error: 'Validation failed', details: err.errors });
      return;
    }
    res.status(500).json({ error: 'Failed to update cart item' });
  }
});

router.delete('/items/:itemId', async (req, res) => {
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

    const { itemId } = req.params;
    const item = await prisma.cartItem.findFirst({ where: { id: itemId, cart: { storeId: store.id } } });
    if (!item) {
      res.status(404).json({ error: 'Cart item not found' });
      return;
    }

    await prisma.cartItem.delete({ where: { id: itemId } });
    res.json({ message: 'Cart item removed' });
  } catch (err) {
    res.status(500).json({ error: 'Failed to remove cart item' });
  }
});

router.delete('/clear', async (req, res) => {
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

    const cart = await prisma.cart.findFirst({ where: { storeId: store.id } });
    if (cart) {
      await prisma.cartItem.deleteMany({ where: { cartId: cart.id } });
      await prisma.cart.delete({ where: { id: cart.id } });
    }

    res.json({ message: 'Cart cleared' });
  } catch (err) {
    res.status(500).json({ error: 'Failed to clear cart' });
  }
});

export default router;
