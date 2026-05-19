import { Request, Response, NextFunction } from 'express';

export interface TenantRequest extends Request {
  tenantId?: string;
}

export const tenantMiddleware = (req: TenantRequest, res: Response, next: NextFunction): void => {
  // Try to resolve tenant from subdomain (e.g., mystore.dropify.app)
  const host = req.headers.host || '';
  const subdomain = host.split('.')[0];

  // Try to resolve tenant from URL path (/s/{slug})
  const pathMatch = req.path.match(/^\/s\/([^/]+)/);

  if (subdomain && subdomain !== 'www' && subdomain !== 'api' && subdomain !== 'admin') {
    req.tenantId = subdomain;
  } else if (pathMatch) {
    req.tenantId = pathMatch[1];
  }

  next();
};
