import { cn, getInitials } from "@/lib/utils";

interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  src?: string | null;
  name: string;
  size?: "sm" | "md" | "lg";
}

function Avatar({ src, name, size = "md", className, ...props }: AvatarProps) {
  const sizeClasses = {
    sm: "h-8 w-8 text-xs",
    md: "h-10 w-10 text-sm",
    lg: "h-12 w-12 text-base",
  };

  if (src) {
    return (
      <div
        className={cn(
          "relative rounded-full overflow-hidden flex-shrink-0",
          sizeClasses[size],
          className
        )}
        {...props}
      >
        <img
          src={src}
          alt={name}
          className="h-full w-full object-cover"
        />
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex items-center justify-center rounded-full bg-primary-100 text-primary-700 font-medium flex-shrink-0",
        sizeClasses[size],
        className
      )}
      {...props}
    >
      {getInitials(name)}
    </div>
  );
}

export { Avatar };
