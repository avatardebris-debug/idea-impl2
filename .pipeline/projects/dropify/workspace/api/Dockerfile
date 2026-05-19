FROM node:20-alpine

WORKDIR /app

COPY package.json api/package.json ./api/

RUN cd api && npm install

COPY api/ ./api/

RUN cd api && npx prisma generate

EXPOSE 3001

CMD ["node", "api/dist/index.js"]
