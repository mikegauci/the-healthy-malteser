import type { APIRoute } from 'astro';
import routes from '../content/routes.json';
export const GET: APIRoute = () => {
  const escape = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
  const urls = routes.filter(route => !route.noindex && route.kind !== 'print').map(route => `<url><loc>${escape(new URL(route.path, 'https://thehealthymalteser.com').href)}</loc>${route.modified ? `<lastmod>${route.modified}Z</lastmod>` : ''}</url>`).join('');
  return new Response(`<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls}</urlset>`, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
};
