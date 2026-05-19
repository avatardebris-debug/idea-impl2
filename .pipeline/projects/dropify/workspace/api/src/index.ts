import express from 'express';
import cors from 'cors';

import authRoutes from './routes/auth.routes';
import profileRoutes from './routes/profile.routes';
import storeRoutes from './routes/store.routes';
import storeThemeRoutes from './routes/store-theme.routes';
import productRoutes from './routes/product.routes';
import categoryRoutes from './routes/category.routes';
import uploadRoutes from './routes/upload.routes';
import cartRoutes from './routes/cart.routes';
import checkoutRoutes from './routes/checkout.routes';
import orderRoutes from './routes/order.routes';
import supplierRoutes from './routes/supplier.routes';
import { tenantMiddleware } from './middleware/tenant.middleware';
import { env } from './config/env';

const app = express();
const PORT = env.PORT;

// Middleware
app.use(cors({
  origin: [env.FRONTEND_URL, env.ADMIN_URL],
  credentials: true,
}));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Tenant resolution middleware - attach tenantId to all requests
app.use(tenantMiddleware);

// Routes
app.use('/auth', authRoutes);
app.use('/profile', profileRoutes);
app.use('/stores', storeRoutes);
app.use('/stores', storeThemeRoutes);
app.use('/products', productRoutes);
app.use('/categories', categoryRoutes);
app.use('/images', uploadRoutes);
app.use('/cart', cartRoutes);
app.use('/checkout', checkoutRoutes);
app.use('/orders', orderRoutes);
app.use('/suppliers', supplierRoutes);

// Health check
app.get('/health', (_req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Error handler
app.use((err: Error, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
  console.error('Unhandled error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

app.listen(PORT, () => {
  console.log(`Dropify API running on port ${PORT}`);
});

export default app;
