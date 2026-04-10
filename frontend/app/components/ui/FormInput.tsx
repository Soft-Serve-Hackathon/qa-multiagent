type FormInputProps = React.InputHTMLAttributes<HTMLInputElement>;

export default function FormInput(props: FormInputProps) {
  return <input {...props} className="input-field" />;
}
