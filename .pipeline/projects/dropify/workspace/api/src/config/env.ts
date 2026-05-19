import { z } from 'zod';

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  PORT: z.string().default('3001'),
  DATABASE_URL: z.string().url(),
  JWT_SECRET: z.string().min(32),
  JWT_EXPIRES_IN: z.string().default('7d'),
  STRIPE_SECRET_KEY: z.string(),
  STRIPE_WEBHOOK_SECRET: z.string(),
  REDIS_URL: z.string().default('redis://localhost:6379'),
  FRONTEND_URL: z.string().default('http://localhost:3000'),
  ADMIN_URL: z.string().default('http://localhost:3002'),
  STOREFRONT_URL: z.string().default('http://localhost:3003'),
  EMAIL_FROM: z.string().default('noreply@dropify.app'),
  EMAIL_HOST: z.string().default('smtp.sendgrid.net'),
  EMAIL_PORT: z.string().default('587'),
  EMAIL_USER: z.string().default('apikey'),
  EMAIL_PASSWORD: z.string().default(''),
});

export const env = envSchema.parse(process.env);

export type Env = z.infer<typeof envSchema>;
