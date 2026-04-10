interface Props {
  isLoading: boolean;
  error?: Error | null;
  children: React.ReactNode;
}

export default function LoadingOrError({ isLoading, error, children }: Props) {
  if (isLoading)
    return (
      <div className="flex items-center gap-2 text-gray-500 py-8">
        <span className="inline-block w-4 h-4 border-2 border-gray-200 border-t-violet-500 rounded-full animate-spin" />
        Wird geladen…
      </div>
    );
  if (error)
    return (
      <div className="rounded-md bg-red-50 border border-red-200 p-4 text-sm text-red-700">
        Fehler: {error.message}
      </div>
    );
  return <>{children}</>;
}
