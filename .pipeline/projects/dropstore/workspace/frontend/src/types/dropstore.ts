// Shared TypeScript types for Dropstore

export type NicheCategory =
  | 'home_garden'
  | 'pet_supplies'
  | 'fitness'
  | 'beauty'
  | 'kitchen'
  | 'baby_kids'
  | 'outdoors'
  | 'tech_accessories'
  | 'fashion'
  | 'office';

export interface NicheScore {
  niche_id: string;
  name: string;
  category: NicheCategory;
  demand_score: number;
  supply_score: number;
  competition_level: 'low' | 'medium' | 'high';
  trend_direction: 'rising' | 'stable' | 'falling';
  avg_margin_pct: number;
  combined_score: number;
}

export interface ProductSuggestion {
  product_id: string;
  title: string;
  image_url: string;
  estimated_cost: number;
  suggested_retail: number;
  margin_pct: number;
  category: string;
  supplier: string;
  niche_id: string;
  demand_score: number;
  supply_score: number;
  optimized_title: string;
  variants: Record<string, string>[];
}

export interface CatalogProduct {
  product_id: string;
  title: string;
  image_url: string;
  estimated_cost: number;
  suggested_retail: number;
  margin_pct: number;
  category: string;
  supplier: string;
  niche_id: string;
  optimized_title: string;
  variants: Record<string, string>[];
  in_catalog: boolean;
}

export interface CatalogSummary {
  catalog_id: string;
  niche_id: string;
  niche_name: string;
  product_count: number;
  total_cost: number;
  total_retail: number;
  avg_margin_pct: number;
  products: CatalogProduct[];
}

export interface ShopifyStore {
  store_id: string;
  shop_name: string;
  shop_domain: string;
  access_token: string;
  status: string;
  created_at: string;
}

export interface SyncJob {
  job_id: string;
  store_id: string;
  status: 'pending' | 'success' | 'failed';
  products_pushed: number;
  products_failed: number;
  total_products: number;
  error_messages: string[];
  started_at: string;
  completed_at: string;
}

export interface DashboardOverview {
  store_status: ShopifyStore | null;
  catalog_summary: CatalogSummary | null;
  sync_history: SyncJob[];
  total_products_synced: number;
  total_revenue_potential: number;
  avg_margin_pct: number;
}
