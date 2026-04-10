type FormInputProps = React.InputHTMLAttributes<HTMLInputElement>;

export default function FormInput({ className, ...props }: FormInputProps) {
  return (
    <input
      {...props}
      className={`w-full px-3.5 py-2.5 text-sm text-slate-800 placeholder:text-slate-300 bg-white border border-slate-200 rounded-[10px] focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed ${className ?? ''}`}
    />
  );
}