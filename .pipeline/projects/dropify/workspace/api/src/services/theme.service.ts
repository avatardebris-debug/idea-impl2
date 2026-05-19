import prisma from '../config/db';

// ─── Theme Definitions ───────────────────────────────────────────────────────

export interface ThemeDefinition {
  id: string;
  name: string;
  description: string;
  previewUrl: string;
  author: string;
  version: string;
  categories: string[];
  isOfficial: boolean;
  price: number;
  features: string[];
  defaultColors: {
    primary: string;
    secondary: string;
    background: string;
    text: string;
  };
  defaultFonts: {
    heading: string;
    body: string;
  };
  defaultLayout: {
    headerStyle: 'default' | 'minimal' | 'transparent';
    footerStyle: 'default' | 'minimal' | 'hidden';
    productGrid: 'grid' | 'list';
  };
}

export const OFFICIAL_THEMES: ThemeDefinition[] = [
  {
    id: 'minimal-clean',
    name: 'Minimal Clean',
    description: 'A clean, minimalist theme perfect for modern brands. Focuses on product imagery with ample whitespace.',
    previewUrl: '/themes/minimal-clean/preview',
    author: 'Dropify',
    version: '1.0.0',
    categories: ['minimal', 'modern'],
    isOfficial: true,
    price: 0,
    features: ['Responsive', 'Fast Loading', 'SEO Optimized'],
    defaultColors: {
      primary: '#000000',
      secondary: '#666666',
      background: '#FFFFFF',
      text: '#333333',
    },
    defaultFonts: {
      heading: 'Inter',
      body: 'Inter',
    },
    defaultLayout: {
      headerStyle: 'minimal',
      footerStyle: 'minimal',
      productGrid: 'grid',
    },
  },
  {
    id: 'bold-vibrant',
    name: 'Bold Vibrant',
    description: 'Eye-catching theme with bold colors and dynamic layouts. Ideal for fashion and lifestyle brands.',
    previewUrl: '/themes/bold-vibrant/preview',
    author: 'Dropify',
    version: '1.0.0',
    categories: ['bold', 'fashion'],
    isOfficial: true,
    price: 0,
    features: ['Animated', 'Full-width', 'Social Integration'],
    defaultColors: {
      primary: '#FF6B6B',
      secondary: '#4ECDC4',
      background: '#FFFFFF',
      text: '#2D3436',
    },
    defaultFonts: {
      heading: 'Poppins',
      body: 'Open Sans',
    },
    defaultLayout: {
      headerStyle: 'default',
      footerStyle: 'default',
      productGrid: 'grid',
    },
  },
  {
    id: 'elegant-serif',
    name: 'Elegant Serif',
    description: 'Sophisticated theme with serif typography. Perfect for luxury goods and artisanal products.',
    previewUrl: '/themes/elegant-serif/preview',
    author: 'Dropify',
    version: '1.0.0',
    categories: ['elegant', 'luxury'],
    isOfficial: true,
    price: 0,
    features: ['Serif Typography', 'Parallax', 'Gallery'],
    defaultColors: {
      primary: '#8B4513',
      secondary: '#D2691E',
      background: '#FAF9F6',
      text: '#2C1810',
    },
    defaultFonts: {
      heading: 'Playfair Display',
      body: 'Lora',
    },
    defaultLayout: {
      headerStyle: 'default',
      footerStyle: 'default',
      productGrid: 'list',
    },
  },
  {
    id: 'tech-modern',
    name: 'Tech Modern',
    description: 'Futuristic design with dark mode support. Built for tech products and gadgets.',
    previewUrl: '/themes/tech-modern/preview',
    author: 'Dropify',
    version: '1.0.0',
    categories: ['tech', 'modern'],
    isOfficial: true,
    price: 0,
    features: ['Dark Mode', 'Grid Layout', 'Quick View'],
    defaultColors: {
      primary: '#6C5CE7',
      secondary: '#A29BFE',
      background: '#1A1A2E',
      text: '#EAEAEA',
    },
    defaultFonts: {
      heading: 'Roboto',
      body: 'Roboto',
    },
    defaultLayout: {
      headerStyle: 'transparent',
      footerStyle: 'minimal',
      productGrid: 'grid',
    },
  },
  {
    id: 'warm-natural',
    name: 'Warm Natural',
    description: 'Earthy tones and organic feel. Great for home goods, food, and eco-friendly products.',
    previewUrl: '/themes/warm-natural/preview',
    author: 'Dropify',
    version: '1.0.0',
    categories: ['warm', 'natural'],
    isOfficial: true,
    price: 0,
    features: ['Organic Feel', 'Soft Colors', 'Story Sections'],
    defaultColors: {
      primary: '#8D6E63',
      secondary: '#A1887F',
      background: '#FFF8E1',
      text: '#4E342E',
    },
    defaultFonts: {
      heading: 'Merriweather',
      body: 'Nunito',
    },
    defaultLayout: {
      headerStyle: 'default',
      footerStyle: 'default',
      productGrid: 'grid',
    },
  },
];

export const MARKETPLACE_THEMES: ThemeDefinition[] = [
  {
    id: 'marketplace-1',
    name: 'ShopFlow Pro',
    description: 'Professional theme with advanced filtering and comparison features.',
    previewUrl: '/themes/shopflow-pro/preview',
    author: 'ThemeCraft',
    version: '2.1.0',
    categories: ['professional', 'advanced'],
    isOfficial: false,
    price: 49,
    features: ['Advanced Filtering', 'Product Comparison', 'Wishlist'],
    defaultColors: {
      primary: '#2196F3',
      secondary: '#03A9F4',
      background: '#FFFFFF',
      text: '#212121',
    },
    defaultFonts: {
      heading: 'Montserrat',
      body: 'Roboto',
    },
    defaultLayout: {
      headerStyle: 'default',
      footerStyle: 'default',
      productGrid: 'grid',
    },
  },
  {
    id: 'marketplace-2',
    name: 'Luxe Boutique',
    description: 'High-end boutique theme with elegant animations and transitions.',
    previewUrl: '/themes/luxe-boutique/preview',
    author: 'DesignLab',
    version: '1.5.0',
    categories: ['luxury', 'boutique'],
    isOfficial: false,
    price: 79,
    features: ['Animations', 'Lookbook', 'Instagram Feed'],
    defaultColors: {
      primary: '#000000',
      secondary: '#C0C0C0',
      background: '#FFFFFF',
      text: '#000000',
    },
    defaultFonts: {
      heading: 'Cormorant Garamond',
      body: 'Raleway',
    },
    defaultLayout: {
      headerStyle: 'transparent',
      footerStyle: 'minimal',
      productGrid: 'list',
    },
  },
];

export const ALL_THEMES = [...OFFICIAL_THEMES, ...MARKETPLACE_THEMES];

// ─── Theme Service ───────────────────────────────────────────────────────────

export class ThemeService {
  /**
   * Get all available themes (marketplace)
   */
  static async getThemes(filters?: {
    category?: string;
    isOfficial?: boolean;
    price?: 'free' | 'paid' | 'all';
  }): Promise<ThemeDefinition[]> {
    let themes = [...ALL_THEMES];

    if (filters?.category) {
      themes = themes.filter((t) => t.categories.includes(filters.category!));
    }

    if (filters?.isOfficial !== undefined) {
      themes = themes.filter((t) => t.isOfficial === filters.isOfficial);
    }

    if (filters?.price) {
      if (filters.price === 'free') {
        themes = themes.filter((t) => t.price === 0);
      } else if (filters.price === 'paid') {
        themes = themes.filter((t) => t.price > 0);
      }
    }

    return themes;
  }

  /**
   * Get a specific theme by ID
   */
  static async getTheme(themeId: string): Promise<ThemeDefinition | null> {
    return ALL_THEMES.find((t) => t.id === themeId) || null;
  }

  /**
   * Apply a theme to a store
   */
  static async applyTheme(storeId: string, themeId: string, userId: string): Promise<{
    success: boolean;
    theme?: any;
    error?: string;
  }> {
    const theme = await this.getTheme(themeId);
    if (!theme) {
      return { success: false, error: 'Theme not found' };
    }

    try {
      const updatedStore = await prisma.store.update({
        where: { id: storeId },
        data: {
          theme: {
            colors: theme.defaultColors,
            fonts: theme.defaultFonts,
            layout: theme.defaultLayout,
            appliedThemeId: themeId,
          },
        },
        select: { theme: true },
      });

      return { success: true, theme: updatedStore.theme };
    } catch (error) {
      return { success: false, error: 'Failed to apply theme' };
    }
  }

  /**
   * Get current store theme with customization options
   */
  static async getStoreTheme(storeId: string): Promise<{
    theme: any;
    availableThemes: ThemeDefinition[];
    isCustomized: boolean;
  }> {
    const store = await prisma.store.findUnique({
      where: { id: storeId },
      select: { theme: true },
    });

    const currentTheme = store?.theme || {};
    const isCustomized = !!(
      currentTheme.colors?.primary ||
      currentTheme.fonts?.heading ||
      currentTheme.layout?.headerStyle
    );

    return {
      theme: currentTheme,
      availableThemes: ALL_THEMES,
      isCustomized,
    };
  }

  /**
   * Customize theme colors
   */
  static async customizeColors(
    storeId: string,
    colors: {
      primary?: string;
      secondary?: string;
      background?: string;
      text?: string;
    }
  ): Promise<{ success: boolean; theme?: any; error?: string }> {
    try {
      const store = await prisma.store.findUnique({
        where: { id: storeId },
        select: { theme: true },
      });

      const currentTheme = store?.theme || {};
      const updatedTheme = {
        ...currentTheme,
        colors: {
          ...(currentTheme.colors || {}),
          ...colors,
        },
      };

      const updatedStore = await prisma.store.update({
        where: { id: storeId },
        data: { theme: updatedTheme },
        select: { theme: true },
      });

      return { success: true, theme: updatedStore.theme };
    } catch (error) {
      return { success: false, error: 'Failed to update colors' };
    }
  }

  /**
   * Customize theme fonts
   */
  static async customizeFonts(
    storeId: string,
    fonts: {
      heading?: string;
      body?: string;
    }
  ): Promise<{ success: boolean; theme?: any; error?: string }> {
    try {
      const store = await prisma.store.findUnique({
        where: { id: storeId },
        select: { theme: true },
      });

      const currentTheme = store?.theme || {};
      const updatedTheme = {
        ...currentTheme,
        fonts: {
          ...(currentTheme.fonts || {}),
          ...fonts,
        },
      };

      const updatedStore = await prisma.store.update({
        where: { id: storeId },
        data: { theme: updatedTheme },
        select: { theme: true },
      });

      return { success: true, theme: updatedStore.theme };
    } catch (error) {
      return { success: false, error: 'Failed to update fonts' };
    }
  }

  /**
   * Customize theme layout
   */
  static async customizeLayout(
    storeId: string,
    layout: {
      headerStyle?: 'default' | 'minimal' | 'transparent';
      footerStyle?: 'default' | 'minimal' | 'hidden';
      productGrid?: 'grid' | 'list';
    }
  ): Promise<{ success: boolean; theme?: any; error?: string }> {
    try {
      const store = await prisma.store.findUnique({
        where: { id: storeId },
        select: { theme: true },
      });

      const currentTheme = store?.theme || {};
      const updatedTheme = {
        ...currentTheme,
        layout: {
          ...(currentTheme.layout || {}),
          ...layout,
        },
      };

      const updatedStore = await prisma.store.update({
        where: { id: storeId },
        data: { theme: updatedTheme },
        select: { theme: true },
      });

      return { success: true, theme: updatedStore.theme };
    } catch (error) {
      return { success: false, error: 'Failed to update layout' };
    }
  }

  /**
   * Reset theme to defaults
   */
  static async resetTheme(storeId: string): Promise<{ success: boolean; error?: string }> {
    try {
      await prisma.store.update({
        where: { id: storeId },
        data: { theme: null },
      });

      return { success: true };
    } catch (error) {
      return { success: false, error: 'Failed to reset theme' };
    }
  }
}
