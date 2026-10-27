import type { ReactNode } from "react";
import type { UseQueryResult } from "@tanstack/react-query";

interface Props<T> {
  query: UseQueryResult<T>;
  children: (data: T) => ReactNode;
  isEmpty?: (data: T) => boolean;
  emptyText?: string;
  height?: number;
}

export function QueryState<T>({ query, children, isEmpty, emptyText, height = 260 }: Props<T>) {
  if (query.isPending) {
    return (
      <div className="state skeleton" style={{ height }} role="status" aria-live="polite">
        Loading...
      </div>
    );
  }
  if (query.isError) {
    return (
      <div className="state error" style={{ minHeight: height / 2 }} role="alert">
        <strong>Could not load data.</strong>
        <span>{query.error.message}</span>
        <button onClick={() => query.refetch()}>Retry</button>
      </div>
    );
  }
  if (isEmpty?.(query.data)) {
    return (
      <div className="state" style={{ height: height / 2 }}>
        {emptyText ?? "No data for this selection."}
      </div>
    );
  }
  return <>{children(query.data)}</>;
}