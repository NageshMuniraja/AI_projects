import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "success" | "warning" | "destructive" | "info" | "outline";
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium border transition-colors",
        {
          "bg-primary-50 text-primary-700 border-primary-200": variant === "default",
          "bg-emerald-50 text-emerald-700 border-emerald-200": variant === "success",
          "bg-amber-50 text-amber-700 border-amber-200": variant === "warning",
          "bg-red-50 text-red-700 border-red-200": variant === "destructive",
          "bg-blue-50 text-blue-700 border-blue-200": variant === "info",
          "bg-white text-slate-700 border-slate-300": variant === "outline",
        },
        className
      )}
      {...props}
    />
  );
}

export { Badge };
