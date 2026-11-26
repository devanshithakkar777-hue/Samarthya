import Link from "next/link";
export default function NotFound() {
  return (
    <div className="mx-auto max-w-2xl px-5 py-20 text-center">
      <h1 className="text-2xl font-semibold">We could not find that page</h1>
      <p className="mt-3 text-slate">It may not be published yet. Every page here is reviewed against a source before it goes live.</p>
      <Link href="/explore" className="mt-6 inline-block rounded-md bg-electric-blue px-5 py-3 text-arctic-white">Explore careers</Link>
    </div>
  );
}
