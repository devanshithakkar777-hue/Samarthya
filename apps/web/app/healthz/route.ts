// Render health check. Deliberately does not call the API or the database, so checks never wake a sleeping database.
export const dynamic = "force-dynamic";
export function GET() {
  return Response.json({ ok: true });
}
