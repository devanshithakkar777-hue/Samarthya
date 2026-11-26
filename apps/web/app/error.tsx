"use client";
export default function Error({ reset }: { error: Error; reset: () => void }) {
  return (
    <div className="mx-auto max-w-2xl px-5 py-20 text-center">
      <h1 className="text-2xl font-semibold">We could not load this page</h1>
      <p className="mt-3 text-slate">The service may be restarting or your connection may have dropped. Nothing you entered has been lost.</p>
      <button onClick={reset} className="mt-6 rounded-md bg-electric-blue px-5 py-3 text-arctic-white">Try again</button>
    </div>
  );
}
