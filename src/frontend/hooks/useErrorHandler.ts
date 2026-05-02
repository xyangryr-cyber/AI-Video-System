import { toast } from "sonner"
import { lookupErrorUx } from "../utils/errorUxMap"
import type { NormalizedError } from "../types/errors"

export function useErrorHandler() {
  return {
    handle(err: NormalizedError) {
      const ux = lookupErrorUx(err.error_code)
      if (ux.component === "toast") {
        toast.error(`[${err.error_code}] ${err.message}`, {
          description: ux.actions.includes("retry_auto") ? "自动重试中..." : undefined,
        })
      }
      return ux
    },
  }
}
