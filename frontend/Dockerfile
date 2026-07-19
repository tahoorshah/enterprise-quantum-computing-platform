# Multi-stage build for the frontend.
#
# Stage 1 ("build"): use Node to install deps and produce the optimized
# production React build (static HTML/CSS/JS).
#
# Stage 2 ("serve"): copy ONLY the built static files into a tiny nginx
# image. The final image doesn't contain Node or node_modules - just nginx
# and the compiled site, so it's small and production-appropriate.

# ---- Stage 1: build ----
FROM node:22-alpine AS build

WORKDIR /app

# Install dependencies first (better layer caching - only re-runs if
# package.json changes, not on every source edit)
COPY package.json package-lock.json ./
RUN npm ci

# Copy the rest of the source and build.
COPY . .

# VITE_API_BASE="" makes the app use relative /api paths (proxied by nginx)
# instead of http://localhost:8000. Set at build time since Vite bakes env
# vars into the static build.
ENV VITE_API_BASE=""
RUN npm run build

# ---- Stage 2: serve ----
FROM nginx:1.27-alpine AS serve

# Replace the default nginx site config with ours (which proxies /api).
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the built static files from the build stage.
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
