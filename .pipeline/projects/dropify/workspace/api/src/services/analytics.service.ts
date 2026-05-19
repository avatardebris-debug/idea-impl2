import prisma from '../config/db';

// ─── Analytics Types ───────────────────────────────────────────────────────────────────

export interface SalesSummary {
  totalRevenue: number;
  totalOrders: number;
  averageOrderValue: number;
  revenueByDay: { date: string; revenue: number }[];
  revenueByProduct: { productName: string; revenue: number; quantity: number }[];
  revenueByCategory: { categoryName: string; revenue: number; quantity: number }[];
  revenueByMonth: { month: string; revenue: number }[];
}

export interface ProductPerformance {
  productId: string;
  productName: string;
  totalSold: number;
  totalRevenue: number;
  views: number;
  conversionRate: number;
  refundRate: number;
  rating: number;
  inventory: number;
}

export interface CustomerAnalytics {
  totalCustomers: number;
  newCustomers: number;
  returningCustomers: number;
  customerLifetimeValue: number;
  topCustomers: {
    customerId: string;
    customerName: string;
    totalSpent: number;
    orderCount: number;
    lastOrderDate: string;
  }[];
  customerGrowth: { month: string; newCustomers: number }[];
}

export interface TrafficAnalytics {
  totalVisits: number;
  uniqueVisitors: number;
  bounceRate: number;
  averageSessionDuration: number;
  topPages: { page: string; views: number }[];
  trafficSources: { source: string; visits: number; percentage: number }[];
  deviceBreakdown: { device: string; visits: number; percentage: number }[];
  geographicData: { country: string; visits: number; percentage: number }[];
}

export interface InventoryAlert {
  productId: string;
  productName: string;
  currentStock: number;
  lowStockThreshold: number;
  status: 'low' | 'out' | 'critical';
}

// ─── Analytics Service ───────────────────────────────────────────────────────────────────

export class AnalyticsService {
  /**
   * Get sales summary for a store within a date range
   */
  static async getSalesSummary(
    storeId: string,
    startDate: Date,
    endDate: Date
  ): Promise<SalesSummary> {
    const orders = await prisma.order.findMany({
      where: {
        storeId,
        createdAt: { gte: startDate, lte: endDate },
        paymentStatus: 'PAID',
      },
      select: {
        id: true,
        total: true,
        createdAt: true,
        items: {
          select: {
            quantity: true,
            price: true,
            product: { select: { name: true, category: { select: { name: true } } } },
          },
        },
      },
    });

    const totalRevenue = orders.reduce((sum, o) => sum + Number(o.total), 0);
    const totalOrders = orders.length;
    const averageOrderValue = totalOrders > 0 ? totalRevenue / totalOrders : 0;

    // Revenue by day
    const revenueByDayMap = new Map<string, number>();
    orders.forEach((order) => {
      const date = order.createdAt.toISOString().split('T')[0];
      revenueByDayMap.set(date, (revenueByDayMap.get(date) || 0) + Number(order.total));
    });
    const revenueByDay = Array.from(revenueByDayMap.entries())
      .map(([date, revenue]) => ({ date, revenue }))
      .sort((a, b) => a.date.localeCompare(b.date));

    // Revenue by product
    const revenueByProductMap = new Map<string, { productName: string; revenue: number; quantity: number }>();
    orders.forEach((order) => {
      order.items.forEach((item) => {
        const key = item.product.name;
        const existing = revenueByProductMap.get(key) || { productName: key, revenue: 0, quantity: 0 };
        revenueByProductMap.set(key, {
          productName: key,
          revenue: existing.revenue + Number(item.price) * item.quantity,
          quantity: existing.quantity + item.quantity,
        });
      });
    });
    const revenueByProduct = Array.from(revenueByProductMap.values())
      .sort((a, b) => b.revenue - a.revenue);

    // Revenue by category
    const revenueByCategoryMap = new Map<string, { categoryName: string; revenue: number; quantity: number }>();
    orders.forEach((order) => {
      order.items.forEach((item) => {
        const catName = item.product.category?.name || 'Uncategorized';
        const existing = revenueByCategoryMap.get(catName) || { categoryName: catName, revenue: 0, quantity: 0 };
        revenueByCategoryMap.set(catName, {
          categoryName: catName,
          revenue: existing.revenue + Number(item.price) * item.quantity,
          quantity: existing.quantity + item.quantity,
        });
      });
    });
    const revenueByCategory = Array.from(revenueByCategoryMap.values())
      .sort((a, b) => b.revenue - a.revenue);

    // Revenue by month
    const revenueByMonthMap = new Map<string, number>();
    orders.forEach((order) => {
      const month = order.createdAt.toISOString().slice(0, 7);
      revenueByMonthMap.set(month, (revenueByMonthMap.get(month) || 0) + Number(order.total));
    });
    const revenueByMonth = Array.from(revenueByMonthMap.entries())
      .map(([month, revenue]) => ({ month, revenue }))
      .sort((a, b) => a.month.localeCompare(b.month));

    return {
      totalRevenue,
      totalOrders,
      averageOrderValue,
      revenueByDay,
      revenueByProduct,
      revenueByCategory,
      revenueByMonth,
    };
  }

  /**
   * Get product performance metrics
   */
  static async getProductPerformance(
    storeId: string,
    startDate: Date,
    endDate: Date
  ): Promise<ProductPerformance[]> {
    const orders = await prisma.order.findMany({
      where: {
        storeId,
        createdAt: { gte: startDate, lte: endDate },
        paymentStatus: 'PAID',
      },
      select: {
        items: {
          select: {
            productId: true,
            quantity: true,
            price: true,
            variant: { select: { name: true } },
          },
        },
      },
    });

    const productMap = new Map<string, { totalSold: number; totalRevenue: number }>();
    orders.forEach((order) => {
      order.items.forEach((item) => {
        const existing = productMap.get(item.productId) || { totalSold: 0, totalRevenue: 0 };
        productMap.set(item.productId, {
          totalSold: existing.totalSold + item.quantity,
          totalRevenue: existing.totalRevenue + Number(item.price) * item.quantity,
        });
      });
    });

    const products = await prisma.product.findMany({
      where: { storeId },
      select: {
        id: true,
        name: true,
        inventory: true,
        images: true,
      },
    });

    return products
      .map((product) => {
        const metrics = productMap.get(product.id) || { totalSold: 0, totalRevenue: 0 };
        return {
          productId: product.id,
          productName: product.name,
          totalSold: metrics.totalSold,
          totalRevenue: metrics.totalRevenue,
          views: Math.floor(Math.random() * 1000) + 100, // Simulated
          conversionRate: metrics.totalSold > 0 ? (metrics.totalSold / (metrics.totalSold + 50)) * 100 : 0,
          refundRate: 0,
          rating: 4.5,
          inventory: product.inventory,
        };
      })
      .sort((a, b) => b.totalRevenue - a.totalRevenue);
  }

  /**
   * Get customer analytics
   */
  static async getCustomerAnalytics(
    storeId: string,
    startDate: Date,
    endDate: Date
  ): Promise<CustomerAnalytics> {
    const orders = await prisma.order.findMany({
      where: {
        storeId,
        createdAt: { gte: startDate, lte: endDate },
        paymentStatus: 'PAID',
      },
      select: {
        userId: true,
        customerName: true,
        customerEmail: true,
        total: true,
        createdAt: true,
      },
    });

    const customerMap = new Map<string, { totalSpent: number; orderCount: number; lastOrderDate: string; name: string }>();
    orders.forEach((order) => {
      if (order.userId) {
        const existing = customerMap.get(order.userId) || { totalSpent: 0, orderCount: 0, lastOrderDate: '', name: order.customerName || '' };
        customerMap.set(order.userId, {
          totalSpent: existing.totalSpent + Number(order.total),
          orderCount: existing.orderCount + 1,
          lastOrderDate: order.createdAt.toISOString(),
          name: existing.name,
        });
      }
    });

    const totalCustomers = customerMap.size;
    const totalRevenue = orders.reduce((sum, o) => sum + Number(o.total), 0);
    const customerLifetimeValue = totalCustomers > 0 ? totalRevenue / totalCustomers : 0;

    // Top customers
    const topCustomers = Array.from(customerMap.entries())
      .map(([customerId, data]) => ({
        customerId,
        customerName: data.name,
        totalSpent: data.totalSpent,
        orderCount: data.orderCount,
        lastOrderDate: data.lastOrderDate,
      }))
      .sort((a, b) => b.totalSpent - a.totalSpent)
      .slice(0, 10);

    // Customer growth by month
    const growthMap = new Map<string, number>();
    orders.forEach((order) => {
      const month = order.createdAt.toISOString().slice(0, 7);
      growthMap.set(month, (growthMap.get(month) || 0) + 1);
    });
    const customerGrowth = Array.from(growthMap.entries())
      .map(([month, newCustomers]) => ({ month, newCustomers }))
      .sort((a, b) => a.month.localeCompare(b.month));

    return {
      totalCustomers,
      newCustomers: totalCustomers,
      returningCustomers: 0,
      customerLifetimeValue,
      topCustomers,
      customerGrowth,
    };
  }

  /**
   * Get traffic analytics (simulated data)
   */
  static async getTrafficAnalytics(
    storeId: string,
    startDate: Date,
    endDate: Date
  ): Promise<TrafficAnalytics> {
    // Simulated traffic data
    const totalVisits = Math.floor(Math.random() * 5000) + 500;
    const uniqueVisitors = Math.floor(totalVisits * 0.7);
    const bounceRate = Math.floor(Math.random() * 30) + 30;
    const averageSessionDuration = Math.floor(Math.random() * 300) + 60;

    const topPages = [
      { page: '/products', views: Math.floor(totalVisits * 0.35) },
      { page: '/products/:id', views: Math.floor(totalVisits * 0.25) },
      { page: '/cart', views: Math.floor(totalVisits * 0.15) },
      { page: '/checkout', views: Math.floor(totalVisits * 0.10) },
      { page: '/', views: Math.floor(totalVisits * 0.15) },
    ];

    const trafficSources = [
      { source: 'Organic Search', visits: Math.floor(totalVisits * 0.40), percentage: 40 },
      { source: 'Direct', visits: Math.floor(totalVisits * 0.25), percentage: 25 },
      { source: 'Social Media', visits: Math.floor(totalVisits * 0.20), percentage: 20 },
      { source: 'Email', visits: Math.floor(totalVisits * 0.10), percentage: 10 },
      { source: 'Referral', visits: Math.floor(totalVisits * 0.05), percentage: 5 },
    ];

    const deviceBreakdown = [
      { device: 'Mobile', visits: Math.floor(totalVisits * 0.55), percentage: 55 },
      { device: 'Desktop', visits: Math.floor(totalVisits * 0.35), percentage: 35 },
      { device: 'Tablet', visits: Math.floor(totalVisits * 0.10), percentage: 10 },
    ];

    const geographicData = [
      { country: 'United States', visits: Math.floor(totalVisits * 0.40), percentage: 40 },
      { country: 'United Kingdom', visits: Math.floor(totalVisits * 0.15), percentage: 15 },
      { country: 'Germany', visits: Math.floor(totalVisits * 0.10), percentage: 10 },
      { country: 'France', visits: Math.floor(totalVisits * 0.08), percentage: 8 },
      { country: 'Other', visits: Math.floor(totalVisits * 0.27), percentage: 27 },
    ];

    return {
      totalVisits,
      uniqueVisitors,
      bounceRate,
      averageSessionDuration,
      topPages,
      trafficSources,
      deviceBreakdown,
      geographicData,
    };
  }

  /**
   * Get inventory alerts
   */
  static async getInventoryAlerts(storeId: string): Promise<InventoryAlert[]> {
    const products = await prisma.product.findMany({
      where: { storeId },
      select: {
        id: true,
        name: true,
        inventory: true,
        variants: { select: { stock: true } },
      },
    });

    const alerts: InventoryAlert[] = [];
    products.forEach((product) => {
      const totalStock = product.inventory;
      let status: 'low' | 'out' | 'critical' = 'low';
      if (totalStock === 0) status = 'out';
      else if (totalStock <= 10) status = 'critical';

      if (status !== 'low') {
        alerts.push({
          productId: product.id,
          productName: product.name,
          currentStock: totalStock,
          lowStockThreshold: 10,
          status,
        });
      }
    });

    return alerts.sort((a, b) => a.currentStock - b.currentStock);
  }
}
