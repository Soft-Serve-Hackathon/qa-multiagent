interface FormInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export default function FormInput({ label, ...props }: FormInputProps) {
  return (
    <input
      {...props}
      className="input-field"
    />
  );
}
