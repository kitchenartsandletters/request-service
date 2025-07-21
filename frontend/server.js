import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import { createProxyMiddleware } from 'http-proxy-middleware';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();

if (!process.env.BACKEND_URL) {
  console.warn('⚠️  BACKEND_URL is not set. Proxying /api requests to http://localhost:8000');
}

const PORT = process.env.PORT || 4173;

// Serve static frontend
app.use(express.static(path.join(__dirname, 'dist')));

// Optional: Proxy /api to backend Railway service
app.use('/api', createProxyMiddleware({
  target: process.env.BACKEND_URL || 'http://localhost:8000',
  changeOrigin: true,
  logLevel: 'debug',
}));

// Fallback to index.html for SPA
app.get('*', (req, res) => {
  res.sendFile(path.resolve(__dirname, 'dist', 'index.html'));
});

// Start server
app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT} — serving static files from /dist`);
});