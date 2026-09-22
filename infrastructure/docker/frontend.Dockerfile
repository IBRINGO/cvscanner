# Development image for the Angular frontend. Runs the Angular dev server
# with live reload against a bind-mounted source tree (see
# docker-compose.dev.yml) — this is not a production build; a real
# deployment would run `ng build` and serve the static output separately.
FROM node:20-alpine

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ .

EXPOSE 4200

CMD ["npm", "start", "--", "--host", "0.0.0.0", "--poll", "2000"]
