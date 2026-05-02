import type { ReactElement } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";
import { AppRouter } from "./pages/AppRouter";
import { createQueryClient } from "./lib/queryClient";

const queryClient = createQueryClient();

export function App(): ReactElement {
  return (
    <QueryClientProvider client={queryClient}>
      <AppRouter />
      <Toaster position="top-right" />
    </QueryClientProvider>
  );
}
