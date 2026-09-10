import * as React from "react";

import { cn } from "@/lib/utils";

function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      className={cn(
        "flex min-h-24 w-full rounded-md border border-[#37393B] bg-[#060608] px-3 py-2 text-sm text-white placeholder:text-[#8F8F8F] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#BB2028] disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
}

export { Textarea };
