import * as React from "react"
import { cn } from "@/lib/utils"

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-10 w-full rounded-full border border-gray-300 bg-white text-black px-3 py-2 text-sm " +
          "file:border-0 file:bg-transparent file:text-sm file:font-medium " +
          "placeholder:text-[#757575] disabled:cursor-not-allowed disabled:opacity-50 " +
          "focus:outline-none focus:ring-0 focus:bg-white caret-[#2BA2D4] selection:bg-[#2BA2D4] selection:text-white",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input }