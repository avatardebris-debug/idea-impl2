# Phase 2: Store Customization & Analytics

## Overview
Phase 2 adds three major capabilities to the Dropify platform:
1. **Store Themes** — Browse, preview, and apply visual themes to stores
2. **Analytics** — Sales, product, customer, and traffic analytics
3. **Discount Codes** — Create, validate, and apply discount codes

## Architecture

### Store Themes
- **Service**: `api/src/services/theme.service.ts`
- **Routes**: `api/src/routes/theme.routes.ts`
- **Features**:
  - Browse themes by category (minimal, bold, colorful, dark, light)
  - Preview themes with mock store data
  - Apply themes to stores (one active theme per store)
  - Customize colors (primary, secondary, accent, background, text)
  - Official vs. third-party themes

### Analytics
- **Service**: `api/src/services/analytics.service.ts`
- **Routes**: `api/src/routes/analytics.routes.ts`
- **Features**:
  - Sales summary (total revenue, orders, average order value, daily trends)
  - Product performance (top selling, revenue by product, inventory alerts)
  - Customer analytics (total customers, lifetime value, top customers, retention)
  - Traffic analytics (simulated visits, unique visitors, top pages, traffic sources)
  - Inventory alerts (low stock, out of stock)
  - Dashboard (comprehensive overview)

### Discount Codes
- **Service**: `api/src/services/discount.service.ts`
- **Routes**: `api/src/routes/discount.routes.ts`
- **Features**:
  - Create discount codes (percentage, fixed, free shipping)
  - Validate discount codes (active, date range, usage limit, minimum order)
  - Apply discount codes to orders
  - Deactivate/delete discount codes

## API Endpoints

### Themes
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/themes` | Browse themes |
| GET | `/api/themes/:id/preview` | Preview a theme |
| POST | `/api/themes/apply` | Apply a theme to store |
| PUT | `/api/themes/customize` | Customize theme colors |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/sales` | Sales summary |
| GET | `/api/analytics/products` | Product performance |
| GET | `/api/analytics/customers` | Customer analytics |
| GET | `/api/analytics/traffic` | Traffic analytics |
| GET | `/api/analytics/inventory/alerts` | Inventory alerts |
| GET | `/api/analytics/dashboard` | Dashboard overview |

### Discount Codes
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/discounts` | Get all discount codes |
| POST | `/api/discounts` | Create a discount code |
| POST | `/api/discounts/validate` | Validate a discount code |
| PUT | `/api/discounts/:code/deactivate` | Deactivate a discount code |
| DELETE | `/api/discounts/:code` | Delete a discount code |
| POST | `/api/discounts/:code/apply` | Apply a discount code to an order |

## Database Schema Additions

### Theme Model
```prisma
model Theme {
  id          String   @id @default(uuid())
  name        String
  description String
  category    String
  price       Float
  isOfficial  Boolean  @default(false)
  previewUrl  String
  colors      String   // JSON string
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
}
```

### DiscountCode Model
```prisma
model DiscountCode {
  id                  String   @id @default(uuid())
  code                String
  storeId             String
  type                String   // percentage, fixed, free_shipping
  value               Float
  usageLimit          Int?
  currentUsage        Int      @default(0)
  startDate           DateTime
  endDate             DateTime?
  isActive            Boolean  @default(true)
  minimumOrderAmount  Float?
  createdAt           DateTime @default(now())
  updatedAt           DateTime @updatedAt
}
```

## Testing
Run tests with:
```bash
cd api && npm test -- phase2.test.ts
```

## Integration Notes
- All routes require authentication via `authenticate` middleware
- Store ownership is verified for admin routes
- Analytics uses simulated data for traffic (no real tracking yet)
- Discount codes are case-insensitive (stored uppercase)
