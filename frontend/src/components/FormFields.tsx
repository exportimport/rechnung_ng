import type { FieldError, UseFormRegisterReturn } from "react-hook-form";

interface BaseProps {
  label: string;
  registration: UseFormRegisterReturn;
  error?: FieldError;
  required?: boolean;
}

const inputClass =
  "block w-full rounded-md border border-gray-200 px-3 py-2 text-sm shadow-sm focus:border-violet-400 focus:outline-none focus:ring-1 focus:ring-violet-400";
const errorClass = "mt-1 text-xs text-red-600";
const labelClass = "block text-sm font-medium text-gray-700 mb-1";

export function TextField({
  label,
  registration,
  error,
  required,
  type = "text",
}: BaseProps & { type?: string }) {
  return (
    <div>
      <label className={labelClass}>
        {label}
        {required && <span className="text-red-500 ml-0.5">*</span>}
      </label>
      <input type={type} className={inputClass} {...registration} />
      {error && <p className={errorClass}>{error.message}</p>}
    </div>
  );
}

export function TextAreaField({
  label,
  registration,
  error,
  required,
  rows = 3,
}: BaseProps & { rows?: number }) {
  return (
    <div>
      <label className={labelClass}>
        {label}
        {required && <span className="text-red-500 ml-0.5">*</span>}
      </label>
      <textarea rows={rows} className={inputClass} {...registration} />
      {error && <p className={errorClass}>{error.message}</p>}
    </div>
  );
}

export function SelectField({
  label,
  registration,
  error,
  required,
  options,
}: BaseProps & { options: { value: string | number; label: string }[] }) {
  return (
    <div>
      <label className={labelClass}>
        {label}
        {required && <span className="text-red-500 ml-0.5">*</span>}
      </label>
      <select className={inputClass} {...registration}>
        <option value="">— bitte wählen —</option>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
      {error && <p className={errorClass}>{error.message}</p>}
    </div>
  );
}

export function DateField({ label, registration, error, required }: BaseProps) {
  return (
    <div>
      <label className={labelClass}>
        {label}
        {required && <span className="text-red-500 ml-0.5">*</span>}
      </label>
      <input type="date" className={inputClass} {...registration} />
      {error && <p className={errorClass}>{error.message}</p>}
    </div>
  );
}
